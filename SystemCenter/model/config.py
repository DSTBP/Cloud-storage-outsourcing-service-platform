# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : SystemCenter/model/config.py
# @Description : 系统中心配置类
from dataclasses import dataclass


@dataclass
class SystemCenterConfig:
    """系统中心配置"""
    host: str = '127.0.0.1'                             # 服务地址
    port: int = 6666                                    # 服务端口号
    mongo_uri: str = "mongodb://localhost:27017/"       # MongoDB 连接 URI
    db_name: str = "SystemBoard"                        # 系统中心数据库名称
    sys_params_collection: str = 'system_params'        # 系统参数表名称
    servers_collection: str = 'servers'                 # 云服务器表名称
    users_collection: str = 'users'                     # 用户表名称
    files_collection: str = 'files'                     # 文件表名称
    AES_mode: str  = 'CBC'                              # ASE 分组模式
    AES_padding: str  = 'PKCS7Padding'                  # AES 填充模式
    AES_iv: str = '12121212121212121212121212121212'    # TODO随机生成
    storage_path: str = 'SystemCenter/keys'             # 存储公私钥文件根目录
    id: str = ""