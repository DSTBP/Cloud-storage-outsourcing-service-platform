# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : SystemCenter/business/routes.py
# @Description : 系统中心路由处理类
import traceback

from flask import Flask, request
from loguru import logger
from typing import Dict
from pymongo.errors import BulkWriteError
from business.schema import (
    ServerRegisterRequest, ServerInfo, ServerStatus,
    UserRegisterRequest, UserLoginRequest, UserPublicKeyRequest,
    FileUploadRequest, CenterContext, FileDownloadRequest, UserInfo, FileInfoListResponse, UserRegisterResponse,
    UserLoginResponse, FileUploadResponse, FileDownloadResponse, ServerRegisterResponse, FileDetailResponse,
    FileDetailRequest, AvatarUploadRequest, FileDeleteRequest, FileListRequest, ServerUpdateRequest
)
import time
from business.schema import UserStatus, UserPermissions
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


class SystemCenterRoutes:
    def __init__(self, system_center: CenterContext):
        self.context = system_center
        
        # 初始化Limiter
        self.limiter = Limiter(
            app=system_center.app,
            key_func=get_remote_address,
            default_limits=["400 per day", "100 per hour"]
        )

    def register_routes(self, app: Flask):
        """注册所有路由处理器"""
        # 系统参数相关路由
        app.route('/system/parameters', methods=['GET'])(self.get_system_params)

        # 服务器信息相关路由
        app.route('/server/register', methods=['POST'])(self.server_register)
        app.route('/server/update_info', methods=['POST'])(self.server_update_info)

        # 用户信息相关路由
        app.route('/user/register', methods=['POST'])(self.limiter.limit("3 per minute")(self.user_register))
        app.route('/user/login', methods=['POST'])(self.limiter.limit("5 per minute")(self.user_login))
        app.route('/user/public_key', methods=['POST'])(self.user_public_key)
        app.route('/user/avatar', methods=['POST'])(self.upload_avatar)

        # 文件信息相关路由
        app.route('/file/upload', methods=['POST'])(self.handle_file_upload)
        app.route('/file/download', methods=['POST'])(self.handle_file_download)
        app.route('/file/list', methods=['GET'])(self.list_file_info)
        app.route('/file/detail', methods=['GET'])(self.get_file_info)
        app.route('/file/delete', methods=['POST'])(self.handle_file_delete)
        
    def get_system_params(self):
        """获取系统参数"""
        try:
            return self.context.net.create_standard_response(data=self.context.system_params.__dict__)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def server_register(self, max_try_times: int = 5) -> dict:
        """注册新服务器"""
        try:
            data = request.get_json()
            register_data = ServerRegisterRequest(**data)

            for attempt in range(max_try_times):
                try:
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
                    return self.context.net.create_standard_response(data=resp.__dict__)
                except BulkWriteError:
                    logger.warning(f"[SC] 第 {attempt + 1} 次尝试注册服务器失败，尝试使用新 ID 重试...")
                    if attempt == max_try_times - 1:
                        return self.context.net.create_standard_response(error_code=103)
        except TypeError:
            return self.context.net.create_standard_response(error_code=102)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def server_update_info(self):
        try:
            data = request.get_json()
            logger.info(data)
            update_data = ServerUpdateRequest(**data)
            req = self.context.databaseservice.update_document(
                self.context.servers_collection,
                {"_id": update_data.sid},
                {"address": update_data.address}
            )
            logger.info(req)
            return self.context.net.create_standard_response(data=None)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)


    def user_register(self, max_try_times: int = 5) -> Dict:
        """用户注册"""
        try:
            data = request.get_json()
            logger.debug(data)
            register_data = UserRegisterRequest(**data)

            # 检查用户名是否已存在
            if self.context.databaseservice.find_document(self.context.users_collection, {'username': register_data.username}):
                return self.context.net.create_standard_response(error_code=115)

            for attempt in range(max_try_times):
                try:
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
                    return self.context.net.create_standard_response(data=resp.__dict__)
                except BulkWriteError:
                    logger.warning(f"[SC] 第 {attempt + 1} 次尝试注册用户失败，尝试使用新 ID 重试...")
                    if attempt == max_try_times - 1:
                        return self.context.net.create_standard_response(error_code=104)

        except TypeError:
            return self.context.net.create_standard_response(error_code=102)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def user_login(self) -> Dict:
        """用户登录"""
        try:
            data = request.get_json()
            login_data = UserLoginRequest(**data)
            
            user = self.context.databaseservice.find_document(
                self.context.users_collection,
                {"username": login_data.username}
            )
            if not user:
                return self.context.net.create_standard_response(error_code=116)

            user_data = UserInfo(**user)

            if user_data.password != login_data.password:
                return self.context.net.create_standard_response(error_code=128)

            # 更新用户的最后登录时间
            current_time = str(int(time.time() * 1000))
            self.context.databaseservice.update_document(
                self.context.users_collection,
                {"_id": user_data._id},
                {"last_login": current_time}
            )

            resp = UserLoginResponse(user_id=user_data._id, public_key=user_data.public_key, avatar=user_data.avatar)
            return self.context.net.create_standard_response(data=resp.__dict__)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def user_public_key(self) -> Dict:
        try:
            """用户上传公钥"""
            data = request.get_json()
            key_data = UserPublicKeyRequest(**data)
            public_key = self.context.cryptoservice.ecc_public_key_pem_to_point(key_data.public_key)
            self.context.databaseservice.update_document(
                self.context.users_collection,
                {"_id": key_data.user_id},
                {"public_key": public_key}
            )
            return self.context.net.create_standard_response()
        except TypeError:
            return self.context.net.create_standard_response(error_code=102)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def handle_file_upload(self):
        """处理文件上传"""
        try:
            data = request.get_json()
            upload_data = FileUploadRequest(**data)

            # 生成文件UUID
            file_uuid = self.context.generate_unique_id("file", {'file_hash': upload_data.file_hash, 'file_path': upload_data.file_path, 'upload_user': upload_data.upload_user})

            # 生成签密和承诺
            signcryptions, commits = self.context.generate_signcryptions_commits(upload_data.file_key)
            logger.debug(f'commits: {commits}')

            # 上传文件信息
            self.context.upload_file_info(file_uuid, upload_data, commits)

            # 分发份额
            self.context.distribute_shares(file_uuid, signcryptions)

            resp = FileUploadResponse(file_uuid=file_uuid)
            return self.context.net.create_standard_response(data=resp.__dict__)
        except BulkWriteError:
            return self.context.net.create_standard_response(error_code=114)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def handle_file_download(self) -> dict:
        """处理文件下载"""
        try:
            data = request.get_json()
            download_data = FileDownloadRequest(**data)

            # 收集份额
            shares = self.context.collect_shares(download_data.file_uuid, download_data.download_user)
            resp = FileDownloadResponse(enc_shares_list=shares)
            return self.context.net.create_standard_response(data=resp.__dict__)
        except TypeError:
            return self.context.net.create_standard_response(error_code=102)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def get_file_info(self) -> dict:
        """获取指定文件信息"""
        try:
            req = FileDetailRequest(**request.args)
            file_info = self.context.databaseservice.find_document(
                self.context.files_collection,
                {"_id": req.file_uuid},
                ['_id', 'file_hash', 'file_size', 'file_name', 'commits', 'file_ciphertext', 'grid_ref', 'download_count']
            )
            if not file_info:
                return self.context.net.create_standard_response(error_code=119)
            resp = FileDetailResponse(**file_info)

            # 更新文件下载次数
            self.context.databaseservice.update_document(
                self.context.files_collection,
                {"_id": req.file_uuid},
                {"download_count": resp.download_count + 1}
            )

            return self.context.net.create_standard_response(data=resp.__dict__)
        except TypeError:
            return self.context.net.create_standard_response(error_code=120)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def list_file_info(self) -> dict:
        """获取所有文件信息"""
        try:
            req = FileListRequest(**request.args) if request.args else {}
            logger.debug(f'req: {req}')
            files = self.context.databaseservice.find_document(
                self.context.files_collection,
                {"upload_user": req.username} if req else {},
                ['_id', 'file_name', 'file_size', 'file_hash', 'upload_user', 'upload_time', 'status', 'download_count']
            )
            if not files:
                resp = FileInfoListResponse(files_info=[])
            else:
                resp = FileInfoListResponse(files_info=[files] if isinstance(files, Dict) else files)
            return self.context.net.create_standard_response(data=resp.__dict__)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def upload_avatar(self) -> dict:
        """处理用户头像上传"""
        try:
            data = request.get_json()
            upload_data = AvatarUploadRequest(**data)

            # 检查用户是否存在
            user = self.context.databaseservice.find_document(
                self.context.users_collection,
                {"_id": upload_data.user_id}
            )
            if not user:
                return self.context.net.create_standard_response(error_code=116)

            # 更新用户头像
            self.context.databaseservice.update_document(
                self.context.users_collection,
                {"_id": upload_data.user_id},
                {"avatar": upload_data.avatar}
            )

            return self.context.net.create_standard_response(data=None)
        except TypeError:
            return self.context.net.create_standard_response(error_code=102)
        except Exception:
            return self.context.net.create_standard_response(error_code=118)

    def handle_file_delete(self) -> Dict:
        """处理文件删除请求"""
        try:
            # 解析请求数据
            request_data = request.get_json()
            if not request_data:
                return self.context.net.create_standard_response(error_code=101)

            # 验证请求数据
            delete_request = FileDeleteRequest(**request_data)
            
            # 查找文件信息
            file_info = self.context.databaseservice.find_document(
                self.context.files_collection,
                {'_id': delete_request.file_uuid},
                ['upload_user']
            )
            
            if not file_info:
                return self.context.net.create_standard_response(error_code=119)
            
            # 检查权限
            if file_info['upload_user'] != delete_request.username:
                return self.context.net.create_standard_response(error_code=108)
            
            # 删除文件
            result = self.context.databaseservice.delete_documents(
                self.context.files_collection,
                {'_id': delete_request.file_uuid},
                single=True
            )
            
            # 通知服务器删除相关份额
            res = self.context.delete_shares(delete_request.file_uuid)
            if not res:
                return self.context.net.create_standard_response(error_code=109)

            if result > 0:
                return self.context.net.create_standard_response(data=None)
            else:
                return self.context.net.create_standard_response(error_code=118)
                
        except Exception as e:
            logger.error(f"删除文件时发生错误: {str(e)}")
            return self.context.net.create_standard_response(error_code=118)
