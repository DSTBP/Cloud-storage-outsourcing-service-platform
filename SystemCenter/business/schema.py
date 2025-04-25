# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : SystemCenter/business/schema.py
# @Description : 系统中心数据模型
from enum import Enum
from flask import Flask
from pydantic import BaseModel
from dataclasses import dataclass
from utils.network import NetworkAPI
from services.crypto import CryptoService
from services.database import DatabaseService
from typing import List, Optional, Tuple, Dict, Callable


class ServerStatus(str, Enum):
    """服务器状态枚举"""
    ACTIVE = "active"        # 活跃状态
    OFFLINE = "offline"      # 离线状态
    MAINTENANCE = "maintenance"  # 维护状态

class UserStatus(str, Enum):
    """服务器状态枚举"""
    ACTIVE = "active"        # 活跃状态
    FAULT = "fault"        # 故障状态
    CANCELLATION = "cancellation"  # 注销状态

class UserPermissions(str, Enum):
    """服务器状态枚举"""
    ADMIN = "admin"               # 管理员权限
    USER = "user"                 # 用户权限

class FileStatus(str, Enum):
    """文件状态枚举"""
    ACTIVE = "active"            # 活跃状态
    DELETED = "deleted"          # 已删除状态
    EXPIRED = "expired"          # 已过期状态
    MAINTENANCE = "maintenance"  # 维护状态


# 请求模型
class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str                   # 用户名
    password: str                   # 密码

class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str                   # 用户名
    password: str                   # 密码

class UserPublicKeyRequest(BaseModel):
    """用户上传公钥请求"""
    username: str                   # 用户名
    user_id: str                    # 用户 iD
    public_key: str                 # 用户公钥（pem 格式）

class AvatarUploadRequest(BaseModel):
    """用户上传头像请求"""
    user_id: str                    # 用户ID
    avatar: str                     # 头像base64编码

class FileUploadRequest(BaseModel):
    """文件上传请求"""
    file_name: str                      # 文件名
    file_path: str                      # 文件路径
    file_size: int                      # 文件大小
    file_ciphertext: str                # 文件密文
    file_hash: str                      # 文件哈希
    file_key: str                       # 文件密钥
    upload_user: str                    # 上传用户信息

class FileDownloadRequest(BaseModel):
    """文件下载请求"""
    file_uuid: str                      # 文件UUID
    download_user: str                  # 下载用户信息

class ServerRegisterRequest(BaseModel):
    address: str                        # 服务器地址
    public_key: Tuple[int, int]         # 服务器公钥

class ServerUpdateRequest(BaseModel):
    address: str                        # 服务器地址
    sid: str                            # 服务器 ID

class FileDetailRequest(BaseModel):
    file_uuid: str                      # 获取文件详情信息请求

class FileListRequest(BaseModel):
    username: Optional[str] = None      # 获取指定用户文件列表信息请求

class FileDeleteRequest(BaseModel):
    """文件删除请求"""
    file_uuid: str                      # 文件UUID
    username: str                       # 用户名

class ServerDownloadRequest(BaseModel):
    file_uuid: str                      # 文件UUID
    download_user: Dict                 # 文件下载者信息

# 响应模型
class UserLoginResponse(BaseModel):
    user_id: str                                    # 用户 ID
    public_key: Optional[Tuple[int, int]] = None    # 用户公钥
    avatar: Optional[str] = None                    # 用户头像base64编码

class FileInfoListResponse(BaseModel):
    files_info: List[Dict]              # 文件信息列表

class UserRegisterResponse(BaseModel):
    user_id: str                        # 用户 ID

class FileUploadResponse(BaseModel):
    file_uuid: str                      # 文件UUID

class FileDownloadResponse(BaseModel):
    enc_shares_list: list[Dict]         # 加密份额列表

class ServerRegisterResponse(BaseModel):
    server_id: str                      # 服务器 ID

class FileDetailResponse(BaseModel):
    """文件详细信息"""
    _id: str                            # 文件UUID
    file_ciphertext: str                # 文件密文
    file_name: str                      # 文件名
    file_size: int                      # 文件大小
    file_hash: str                      # 文件哈希
    download_count: int                 # 下载次数
    commits: Optional[Dict] = None      # 承诺值


@dataclass
class ServerInfo:
    """服务器信息"""
    _id: str                                    # 服务器ID
    public_key: Tuple[int, int]                 # 服务器公钥
    address: str                                # 服务器地址
    status: ServerStatus = ServerStatus.ACTIVE  # 服务器状态
    last_heartbeat: Optional[str] = None        # 最后心跳时间
    load_factor: float = 0.0                    # 负载因子


@dataclass
class UserInfo:
    """用户信息"""
    _id: str                                        # 用户ID
    username: str                                   # 用户名
    password: str                                   # 密码
    public_key: Optional[Tuple[int, int]] = None    # 用户公钥
    status: str = UserStatus.ACTIVE                 # 用户状态
    permissions: str = UserPermissions.USER         # 用户权限
    created_at: str = None                          # 创建时间
    last_login: str = None                          # 最后登录时间
    avatar: Optional[str] = None                    # 用户头像base64编码


@dataclass
class FileInfo:
    """文件信息"""
    _id: str                            # 文件UUID
    file_ciphertext: str                # 文件密文
    file_path: str                      # 文件路径
    file_name: str                      # 文件名
    file_size: int                      # 文件大小
    file_hash: str                      # 文件哈希
    upload_user: str                    # 上传用户
    upload_time: str                    # 上传时间
    status: str = FileStatus.ACTIVE     # 文件状态
    commits: Dict[str, str] = None      # 承诺值
    download_count: int = 0             # 下载次数


@dataclass
class SystemParameters:
    """系统参数"""
    _id: str                            # 参数ID
    n: int                              # 总服务器数
    t: int                              # 阈值
    p: int                              # 椭圆曲线参数p
    a: int                              # 椭圆曲线参数a
    b: int                              # 椭圆曲线参数b
    Gx: int                             # 基点x坐标
    Gy: int                             # 基点y坐标
    N: int                              # 椭圆曲线阶
    H: str                              # 哈希算法
    SM2_PublicKey: Optional[Tuple[int, int]] = None  # SM2公钥

@dataclass
class CenterContext:
    system_params: SystemParameters
    files_collection: str
    servers_collection: str
    users_collection: str
    center_id: str
    cryptoservice: Optional[CryptoService]
    databaseservice: Optional[DatabaseService]
    net: NetworkAPI
    app: Flask

    # 方法字段
    generate_unique_id: Callable[[str, Optional[Dict]], Optional[str]]
    upload_file_info: Callable[[str, FileUploadRequest, dict], None]
    distribute_shares: Callable[[str, list], None]
    collect_shares: Callable[[str, str], List]
    generate_signcryptions_commits: Callable[[str], Tuple[list, dict]]
    delete_shares: Callable[[str], bool]
