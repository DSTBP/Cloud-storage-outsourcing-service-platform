# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : User/model/config.py
# @Description : 用户配置类
from dataclasses import dataclass


@dataclass
class UserConfig:
    """用户配置"""
    system_center_url: str = "http://localhost:6666"    # 系统中心地址
    username: str = "Guest"                             # 用户名
    permissions: str = "User"                           # 用户权限
    storage_path: str = "User/keys"                     # 公私钥文件存储目录
    id: str = ""                                        # 用户ID
    AES_mode: str = 'CBC'                               # AES 分组模式
    AES_padding: str = 'PKCS7Padding'                   # AES 填充模式
    AES_iv: str = '12121212121212121212121212121212'    # AES 初始化向量