# -*- coding: utf-8 -*-
# @Time    : 2025/4/7 11:47
# @Author  : DSTBP
# @File    : business/schema.py
# @Description : 云服务器数据模式类 (用于 API 请求/响应格式验证)
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Tuple, Dict, Optional
from services.crypto import CryptoService
from services.database import DatabaseService
from utils.network import NetworkAPI


# 请求模型
class ServerRegisterRequest(BaseModel):
    address: str                        # 服务器地址
    public_key: Tuple[int, int]         # 服务器公钥

class ServerUpdateRequest(BaseModel):
    address: str                        # 服务器地址
    sid: str                            # 服务器 ID

class SigncryptoShareRequest(BaseModel):
    """签密份额模式"""
    server_id: str               # 目标服务器 ID
    file_uuid: str               # 文件 ID
    ciphertext: str              # 加密分片数据
    signature: Tuple[int, int]   # 数据签名

class SharesDeleteRequest(BaseModel):
    """文件删除请求模式"""
    file_uuid: str  # 文件元数据

class ServerDownloadRequest(BaseModel):
    """文件下载请求模式"""
    file_uuid: str                   # 文件元数据
    download_user: Dict              # 文件下载用户信息

# 响应模型
class ServerRegisterResponse(BaseModel):
    server_id: str                      # 服务器 ID

class ServerDownloadResponse(BaseModel):
    server_id: str                      # 服务器 ID
    enc_share: str                      # 加密份额


@dataclass
class EncShareInfo:
    """加密份额信息"""
    _id: str                            # 文件UUID
    enc_share: str                      # 份额
    server_id: str                      # 服务器ID
    created_at: str                     # 创建时间
    expires_at: Optional[str] = None    # 过期时间

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
class ServerContext:
    """服务器上下文"""
    server_id: str
    cryptoservice: Optional[CryptoService]
    databaseservice: Optional[DatabaseService]
    net: NetworkAPI
    encshares_collection: str
    system_params: Optional[SystemParameters]
    private_key: Optional[int]

