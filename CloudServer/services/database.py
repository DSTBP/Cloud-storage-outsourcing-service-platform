# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : services/database.py
# @Description : MongoDB 数据库服务（集成GridFS）
import base64
from io import BytesIO
from bson import ObjectId
from pymongo import MongoClient, errors
from gridfs import GridFSBucket
from loguru import logger
from typing import Optional, Dict, List, Union
from utils.converter import TypeConverter


class DatabaseService:
    def __init__(self, uri: str, db_name: str, max_retries=3):
        self.uri = uri
        self.db_name = db_name
        self.max_retries = max_retries
        self._client = None
        self._db = None
        self._fs_bucket = None  # GridFS存储桶
        self._connect()

    def _connect(self):
        """建立数据库连接并初始化GridFS"""
        for attempt in range(self.max_retries):
            try:
                self._client = MongoClient(self.uri)
                self._db = self._client[self.db_name]
                self._fs_bucket = GridFSBucket(self._db)  # 默认使用fs存储桶
                logger.success(f"成功连接数据库及GridFS: {self.db_name}")
                return
            except errors.ConnectionFailure as e:
                logger.error(f"连接失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise RuntimeError("无法建立数据库连接") from e

    def _handle_large_file(self, document: Dict) -> Dict:
        """处理大文件存储逻辑"""
        if 'file_ciphertext' in document and len(document['file_ciphertext']) > 10 * 1024 * 1024:  # 10MB阈值
            try:
                # Base64解码为二进制数据
                file_data = base64.b64decode(document['file_ciphertext'])

                # 创建GridFS文件
                file_id = self._fs_bucket.upload_from_stream(
                    document['file_name'],
                    BytesIO(file_data),
                    metadata={
                        'upload_user': document.get('upload_user'),
                        'file_size': document['file_size'],
                        'file_hash': document['file_hash']
                    }
                )

                # 替换原始字段
                document['grid_ref'] = str(file_id)
                del document['file_ciphertext']

                logger.info(f"大文件已存储到GridFS，ID: {file_id}")
            except Exception as e:
                logger.error(f"GridFS上传失败: {str(e)}")
                raise
        return document

    def bulk_insert(self, collection: str, documents: Union[Dict, List[Dict]], ordered: bool = False) -> int:
        """批量插入"""
        processed_docs = []
        try:
            # 统一格式转换
            if isinstance(documents, dict):
                documents = [documents]

            # 大文件处理
            for doc in documents:
                if collection == 'files':
                    processed = self._handle_large_file(doc.copy())
                else:
                    processed = doc.copy()
                processed_docs.append(processed)

            # 执行数据库操作
            processed_docs = TypeConverter.unified_format(processed_docs, "i2h")
            result = self._db[collection].insert_many(processed_docs, ordered=ordered)
            return len(result.inserted_ids)
        except errors.PyMongoError as e:
            logger.error(f"文档插入失败: {str(e)}")
            # 回滚已上传的GridFS文件
            for doc in processed_docs:
                if 'grid_ref' in doc:
                    self._fs_bucket.delete(ObjectId(doc['grid_ref']))
            raise

    def update_document(self, collection: str, filter_query: Dict, update_data: Dict, upsert: bool = False) -> bool:
        """文档更新"""
        try:
            # 格式转换
            filter_query = TypeConverter.unified_format(filter_query, "i2h")
            update_data = TypeConverter.unified_format(update_data, "i2h")

            # 处理大文件更新
            if 'file_ciphertext' in update_data:
                # 查询现有文档
                original = self.find_document(collection, filter_query)
                if original and 'grid_ref' in original:
                    # 删除旧文件
                    self._fs_bucket.delete(ObjectId(original['grid_ref']))

                # 处理新文件
                update_data = self._handle_large_file(update_data.copy())

            # 更新数据库
            result = self._db[collection].update_one(
                filter_query,
                {'$set': update_data},
                upsert=upsert
            )
            return result.modified_count > 0
        except errors.PyMongoError as e:
            logger.error(f"文档更新失败: {str(e)}")
            raise

    def find_document(self, collection: str, filter_query: Dict, projection: Optional[List] = None) -> Union[Optional[List], Optional[Dict]]:
        """文档查询"""
        try:
            # 格式处理
            projection = {field: 1 for field in projection} if projection else None
            filter_query = TypeConverter.unified_format(filter_query, "i2h")

            # 执行查询
            cursor = self._db[collection].find(filter_query, projection)
            results = [doc for doc in cursor]
            if not results:
                return None

            # 处理文件内容
            results = TypeConverter.unified_format(results, "h2i")
            if collection == 'files':
                for doc in results:
                    if 'grid_ref' in doc:
                        # 从GridFS获取文件
                        grid_out = self._fs_bucket.open_download_stream(ObjectId(doc['grid_ref']))
                        doc['file_ciphertext'] = base64.b64encode(grid_out.read()).decode('utf-8')

            if len(results) == 1:
                return results[0]
            return results
        except errors.PyMongoError as e:
            logger.error(f"文档查询失败: {str(e)}")
            raise

    def delete_documents(self, collection: str, filter_query: Dict, single: bool = False) -> int:
        """文档删除（自动清理GridFS文件）"""
        try:
            # 先查询相关文档
            docs = self.find_document(collection, filter_query)
            if not docs:
                return 0

            # 收集文件引用
            grid_refs = []
            if isinstance(docs, list):
                grid_refs = [doc['grid_ref'] for doc in docs if 'grid_ref' in doc]
            elif isinstance(docs, dict) and 'grid_ref' in docs:
                grid_refs = [docs['grid_ref']]

            # 删除数据库文档
            filter_query = TypeConverter.unified_format(filter_query, "i2h")
            if single:
                result = self._db[collection].delete_one(filter_query)
            else:
                result = self._db[collection].delete_many(filter_query)

            # 清理GridFS文件
            for ref in grid_refs:
                self._fs_bucket.delete(ObjectId(ref))

            logger.info(f"删除文档{result.deleted_count}个，清理GridFS文件{len(grid_refs)}个")
            return result.deleted_count
        except errors.PyMongoError as e:
            logger.error(f"删除失败: {str(e)}")
            raise