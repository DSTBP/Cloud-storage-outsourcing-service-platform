# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : business/routes/routes.py
# @Description : 云服务器路由处理
import time
from flask import request
from loguru import logger
from typing import Dict
from business.schema import SigncryptoShareRequest, EncShareInfo, ServerContext, \
    ServerDownloadRequest, ServerDownloadResponse, SharesDeleteRequest


class CloudServerRoutes:
    def __init__(self, cloud_server: ServerContext):
        """
        初始化路由处理器
        :param cloud_server: 服务器上下文
        """
        self.context = cloud_server
        

    def register_routes(self, app):
        """
        注册所有路由
        :param app: Flask应用实例
        """
        # 签密验证路由
        app.route('/sign_cryption', methods=['POST'])(
                self.handle_sign_cryption)

        # 下载请求路由
        app.route('/download_request', methods=['POST'])(
                self.handle_download_request)

        # 删除份额路由
        app.route('/delete_request', methods=['POST'])(
                self.handle_delete_request)

    def handle_sign_cryption(self) -> Dict:
        """
        处理签密数据验证请求
        :return: 处理结果
        """
        try:
            # 获取并验证请求数据
            data = request.get_json()
            sign_data = SigncryptoShareRequest(**data)
            
            # 验证签名
            if not self.context.cryptoservice.verify_signature(
                signature=sign_data.signature,
                message=sign_data.ciphertext,
                public_key=self.context.system_params.SM2_PublicKey,
                algorithm="SM2"
            ):
                logger.warning(f"[Server {self.context.server_id}] 签名验证失败")
                return self.context.net.create_standard_response(error_code=112)

            enc_share_info = EncShareInfo(
                _id=sign_data.file_uuid,
                enc_share=sign_data.ciphertext,
                server_id=sign_data.server_id,
                created_at=str(int(time.time() * 1000)),                        # 当前时间戳（秒）
                expires_at=str(int(time.time() * 1000 + 30 * 24 * 60 * 60))     # 30天后时间戳
            )

            # 保存加密份额
            self.context.databaseservice.bulk_insert(
                self.context.encshares_collection,
                enc_share_info.__dict__
            )
            
            logger.success(f"[Server {self.context.server_id}] 签密数据保存成功")
            return self.context.net.create_standard_response(data=None)

        except Exception as e:
            return self.context.net.create_standard_response(error_code=126)

    def handle_download_request(self) -> Dict:
        """
        处理下载请求
        :return: 处理结果
        """
        try:
            # 获取请求数据
            data = request.get_json()
            resp = ServerDownloadRequest(**data)
            
            # 查询加密份额
            ciphertext = self.context.databaseservice.find_document(
                self.context.encshares_collection,
                {"_id": resp.file_uuid},
                ['enc_share']
            )['enc_share']

            # 嵌套加密份额
            ct = self.context.cryptoservice.encrypt_data(
                message=ciphertext,
                key=resp.download_user["public_key"],
                algorithm='ECC',
                additional={'multi': True}
            )

            # 解密嵌套份额
            enc_share = self.context.cryptoservice.decrypt_data(
                message=ct,
                key=self.context.private_key,
                additional={'multi': True, 'blinding': 'c1'}
            )

            resp = ServerDownloadResponse(server_id=self.context.server_id, enc_share=enc_share)
            return self.context.net.create_standard_response(data=resp.__dict__)

        except Exception as e:
            return self.context.net.create_standard_response(error_code=127)

    def handle_delete_request(self):
        request_data = request.get_json()
        if not request_data:
            return self.context.net.create_standard_response(error_code=101)

        # 验证请求数据
        delete_request = SharesDeleteRequest(**request_data)

        # 查找份额信息
        file_info = self.context.databaseservice.find_document(
            self.context.encshares_collection,
            {'_id': delete_request.file_uuid}
        )

        # 检查权限
        if not file_info:
            return self.context.net.create_standard_response(error_code=110)

        # 删除文件
        result = self.context.databaseservice.delete_documents(
            self.context.encshares_collection,
            {'_id': delete_request.file_uuid},
            single=True
        )

        if result > 0:
            return self.context.net.create_standard_response(data=None)
        else:
            return self.context.net.create_standard_response(error_code=118)