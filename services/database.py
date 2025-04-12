# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : services/database.py
# @Description : MongoDB 数据库服务
from pymongo import MongoClient, errors
from loguru import logger
from typing import Optional, Dict, List, Union
from utils.converter import TypeConverter


class DatabaseService:
    def __init__(self, uri: str, db_name: str, max_retries=3):
        """
        初始化数据库连接
        :param uri: MongoDB 连接字符串
        :param db_name: 数据库名称
        :param max_retries: 最大重试次数
        """
        self.uri = uri
        self.db_name = db_name
        self.max_retries = max_retries
        self._client = None
        self._db = None
        self._connect()

    def _connect(self):
        """建立数据库连接"""
        for attempt in range(self.max_retries):
            try:
                self._client = MongoClient(self.uri)
                self._db = self._client[self.db_name]
                logger.success(f"成功连接数据库: {self.db_name}")
                return
            except errors.ConnectionFailure as e:
                logger.error(f"数据库连接失败 (尝试 {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise RuntimeError("无法建立数据库连接") from e

    def get_collection(self, collection_name: str):
        """
        获取集合对象
        :param collection_name: MongoDB 集合名
        """
        return self._db[collection_name]

    def find_document(self, collection: str, filter_query: Dict, projection: Optional[List] = None) -> Union[Optional[List], Optional[Dict]]:
        """
        查询单个或多个文档
        :param collection: 集合名称
        :param filter_query: 查询条件
        :param projection: 返回字段过滤
        :return: 如果找到一条数据，返回该数据；如果多条，返回数据列表
        """
        try:
            projection = {field: 1 for field in projection} if projection else None
            cursor = self.get_collection(collection).find(filter_query, projection)
            results = [doc for doc in cursor]
            results = TypeConverter.unified_format(results, "h2i")
            if not results:
                return None
            elif len(results) == 1:
                return results[0]
            else:
                return results
        except errors.PyMongoError as e:
            logger.error(f"文档查询失败: {str(e)}")
            raise

    def update_document(self, collection: str, filter_query: Dict, update_data: Dict, upsert: bool = False) -> bool:
        """
        更新文档
        :param collection: 集合名称
        :param filter_query: 查询条件
        :param update_data: 更新数据
        :param upsert: 不存在时是否插入
        """
        try:
            filter_query = TypeConverter.unified_format(filter_query, "i2h")
            update_data = TypeConverter.unified_format(update_data, "i2h")
            result = self.get_collection(collection).update_one(
                filter_query, {'$set': update_data}, upsert=upsert
            )
            return result.modified_count > 0
        except errors.PyMongoError as e:
            logger.error(f"文档更新失败: {str(e)}")
            raise

    def bulk_insert(self, collection: str, documents: Union[Dict, List[Dict]], ordered: bool = False) -> int:
        """
        批量插入文档（支持单个文档）
        :param collection: 集合名称
        :param documents: 文档列表
        :param ordered: 是否顺序插入
        """
        if isinstance(documents, dict):
            documents = [documents]  # 转为列表以支持 insert_many

        try:
            documents = TypeConverter.unified_format(documents, "i2h")
            result = self.get_collection(collection).insert_many(documents, ordered=ordered)
            return len(result.inserted_ids)
        except errors.BulkWriteError as e:
            logger.error(f"批量插入失败: {str(e.details)}")
            raise

    def delete_documents(self, collection: str, filter_query: Dict, single: bool = False) -> int:
        """
        删除文档
        :param collection: 集合名称
        :param filter_query: 查询条件
        :param single: 是否只删除第一个匹配的文档，默认为 False（删除所有匹配的文档）
        :return: 删除的文档数量
        """
        try:
            filter_query = TypeConverter.unified_format(filter_query, "i2h")
            if single:
                result = self.get_collection(collection).delete_one(filter_query)
            else:
                result = self.get_collection(collection).delete_many(filter_query)

            deleted_count = result.deleted_count
            logger.info(f"成功删除 {deleted_count} 个文档")
            return deleted_count
        except errors.PyMongoError as e:
            logger.error(f"删除失败: {str(e)}")
            raise

    def delete_collection(self, collection: str) -> bool:
        """
        删除整个集合
        :param collection: 集合名称
        :return: 是否删除成功
        """
        try:
            self._db.drop_collection(collection)
            logger.info(f"成功删除集合: {collection}")
            return True
        except errors.PyMongoError as e:
            logger.error(f"集合删除失败: {str(e)}")
            raise