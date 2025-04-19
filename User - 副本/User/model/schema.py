# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : User/model/schema.py
# @Description : 用户数据模型
from dataclasses import dataclass
from pydantic import BaseModel
from typing import Tuple, Dict, List, Optional


class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str                       # 用户名
    password: str                       # 密码

class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str                       # 用户名
    password: str                       # 密码

class UserPublicKeyRequest(BaseModel):
    """用户上传公钥请求"""
    username: str                       # 用户名
    user_id: str                        # 用户ID
    public_key: Tuple[int, int]         # 用户公钥

class FileUploadRequest(BaseModel):
    """文件上传请求"""
    file_name: str                      # 文件名
    file_path: str                      # 文件路径
    file_size: int                      # 文件大小
    file_ciphertext: str                # 文件密文
    file_hash: str                      # 文件哈希
    file_key: str                       # 文件密钥
    upload_user: str                    # 上传用户名

class FileDetailRequest(BaseModel):
    file_uuid: str                      # 获取文件详情信息请求

class FileDownloadRequest(BaseModel):
    """文件下载请求"""
    file_uuid: str                      # 文件UUID
    download_user: str                  # 下载用户信息


# 响应模型
class UserRegisterResponse(BaseModel):
    user_id: str                        # 用户 ID

class UserLoginResponse(BaseModel):
    user_id: str                        # 用户 ID
    public_key: Tuple[int, int]         # 用户公钥

class FileInfoListResponse(BaseModel):
    files_info: List[Dict]              # 文件信息列表

class FileUploadResponse(BaseModel):
    file_uuid: str                      # 文件UUID

class FileDownloadResponse(BaseModel):
    enc_shares_list: list[Dict]         # 加密份额列表

class FileDetailResponse(BaseModel):
    """文件详细信息"""
    _id: str                            # 文件UUID
    file_ciphertext: str                # 文件密文
    file_name: str                      # 文件名
    file_size: int                      # 文件大小
    file_hash: str                      # 文件哈希
    commits: Optional[Dict] = None      # 承诺值



@dataclass
class FileBaseInfo:
    """文件基础信息"""
    _id: str                            # 文件UUID
    file_name: str                      # 文件名
    file_size: int                      # 文件大小
    file_hash: str                      # 文件哈希
    upload_user: str                    # 上传用户
    upload_time: str                    # 上传时间
    status: str                         # 文件状态
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