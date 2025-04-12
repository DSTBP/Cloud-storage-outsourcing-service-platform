# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : SystemCenter/routes/routes.py
# @Description : 系统中心路由处理

from flask import Flask, request
from loguru import logger
from typing import Dict
from pymongo.errors import BulkWriteError
from SystemCenter.model.schema import (
    ServerRegisterRequest, ServerInfo, ServerStatus,
    UserRegisterRequest, UserLoginRequest, UserPublicKeyRequest,
    FileUploadRequest, CenterContext, FileDownloadRequest, UserInfo, FileInfoListResponse, UserRegisterResponse,
    UserLoginResponse, FileUploadResponse, FileDownloadResponse, ServerRegisterResponse, FileDetailResponse
)
import time
from SystemCenter.model.schema import UserStatus, UserPermissions


class SystemCenterRoutes:
    def __init__(self, system_center: CenterContext):
        self.context = system_center

    def register_routes(self, app: Flask):
        """注册所有路由处理器"""
        # 系统参数相关路由
        app.route('/system/parameters', methods=['GET'])(self.get_system_params)

        # 服务器信息相关路由
        app.route('/server/register', methods=['POST'])(self.server_register)

        # 用户信息相关路由
        app.route('/user/register', methods=['POST'])(self.user_register)
        app.route('/user/login', methods=['POST'])(self.user_login)
        app.route('/user/public_key', methods=['POST'])(self.user_public_key)

        # 文件信息相关路由
        app.route('/file/upload', methods=['POST'])(self.handle_file_upload)
        app.route('/file/download', methods=['POST'])(self.handle_file_download)
        app.route('/file/list', methods=['GET'])(self.list_file_info)
        app.route('/file/detail', methods=['GET'])(self.get_file_info)

    def get_system_params(self):
        """获取系统参数"""
        return {'error_code': 200, 'data': self.context.system_params.__dict__}

    def server_register(self) -> dict:
        """注册新服务器"""
        data = request.get_json()
        register_data = ServerRegisterRequest(**data)
        server_id = self.context.generate_unique_id("server", None)
        server_info = ServerInfo(
            **register_data.__dict__,
            _id=server_id,
            status=ServerStatus.ACTIVE,
            last_heartbeat=str(int(time.time() * 1000))
        )

        self.context.databaseservice.bulk_insert(
            self.context.servers_collection,
            server_info.__dict__
        )

        logger.success(f"[SC] 已注册服务器: {server_id}")
        resp = ServerRegisterResponse(server_id=server_id)
        return {'error_code': 200, 'data': resp.__dict__}

    def user_register(self) -> Dict:
        """用户注册"""
        data = request.get_json()
        register_data = UserRegisterRequest(**data)

        # 检查用户名是否已存在
        if self.context.databaseservice.find_document(self.context.users_collection, {'username': register_data.username}):
            return {'error_code': 101}  # 'message': '用户名已存在'

        user_id = self.context.generate_unique_id("user", {'username': register_data.username})
        user_info = UserInfo(
            _id=user_id,
            username=register_data.username,
            password=register_data.password,
            public_key=None,
            status=UserStatus.ACTIVE,
            permissions=UserPermissions.USER,
            created_at=str(int(time.time() * 1000)),
            last_login=str(int(time.time() * 1000)),
        )
        
        self.context.databaseservice.bulk_insert(
            self.context.users_collection,
            user_info.__dict__
        )

        resp = UserRegisterResponse(user_id=user_id)
        logger.success(f"[SC] 已注册用户: {user_id}")
        return {'error_code': 200, 'data': resp.__dict__}

    def user_login(self) -> Dict:
        """用户登录"""
        data = request.get_json()
        login_data = UserLoginRequest(**data)
        
        user = self.context.databaseservice.find_document(
            self.context.users_collection,
            {"username": login_data.username}
        )
        if not user:
            return {'error_code': 401, 'msg': '用户名不存在'}

        user_data = UserInfo(**user)

        if user_data.password != login_data.password:
            return {'error_code': 401, 'msg': '密码错误'}

        resp = UserLoginResponse(user_id=user_data._id, public_key=user_data.public_key)
        return {'error_code': 200, 'data': resp.__dict__}

    def user_public_key(self) -> Dict:
        """用户上传公钥"""
        data = request.get_json()
        key_data = UserPublicKeyRequest(**data)
        logger.debug(f'id: {key_data.user_id}')
        self.context.databaseservice.update_document(
            self.context.users_collection,
            {"_id": key_data.user_id},
            {"public_key": key_data.public_key}
        )
        return {'error_code': 200, 'data': None}

    def handle_file_upload(self):
        """处理文件上传"""
        try:
            data = request.get_json()
            upload_data = FileUploadRequest(**data)

            # 生成文件UUID
            file_uuid = self.context.generate_unique_id("file", {'file_hash': upload_data.file_hash, 'file_path': upload_data.file_path})

            # 生成签密和承诺
            signcryptions, commits = self.context.generate_signcryptions_commits(upload_data.file_key)

            # 上传文件信息
            self.context.upload_file_info(file_uuid, upload_data, commits)

            # 分发份额
            self.context.distribute_shares(file_uuid, signcryptions)

            resp = FileUploadResponse(file_uuid=file_uuid)
            return {'error_code': 200, 'data': resp.__dict__}
        except BulkWriteError:
            return {'error_code': 114, 'message': "文件已存在"}

    def handle_file_download(self) -> dict:
        """处理文件下载"""
        data = request.get_json()
        download_data = FileDownloadRequest(**data)
        
        # 收集份额
        shares = self.context.collect_shares(download_data.file_uuid, download_data.download_user)
        resp = FileDownloadResponse(enc_shares_list=shares)
        return {'error_code': 200, 'data': resp.__dict__}

    def get_file_info(self) -> dict:
        """获取指定文件信息"""
        file_uuid = request.args.get('file_uuid')
        file_info = self.context.databaseservice.find_document(
            self.context.files_collection,
            {"_id": file_uuid},
            ['_id', 'file_hash', 'file_size', 'file_name', 'commits', 'file_ciphertext']
        )
        
        if not file_info:
            return {'error_code': 404, 'message': '文件不存在'}

        resp = FileDetailResponse(**file_info)
        return {'error_code': 200, 'data': resp.__dict__}

    def list_file_info(self) -> dict:
        """获取所有文件信息"""
        files = self.context.databaseservice.find_document(
            self.context.files_collection,
            {},
            ['_id', 'file_name', 'file_size', 'file_hash', 'upload_user', 'upload_time', 'status', 'download_count']
        )
        resp = FileInfoListResponse(files_info=[files])
        return {'error_code': 200, 'data': resp.__dict__}