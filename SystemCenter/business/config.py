# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : SystemCenter/business/config.py
# @Description : 系统中心配置类
from dataclasses import dataclass


@dataclass
class SystemCenterConfig:
    """系统中心配置"""
    host: str = '127.0.0.1'                             # 系统中心地址
    port: int = 8085                                    # 服务端口号
    mongo_uri: str = "mongodb://localhost:27017/"       # MongoDB 连接 URI
    db_name: str = "SystemBoard"                        # 数据库名称
    files_collection: str = 'files'                     # 文件信息表名称
    servers_collection: str = 'servers'                 # 服务器信息表名称
    users_collection: str = 'users'                     # 用户信息表名称
    sys_params_collection: str = 'system_params'        # 系统参数表名称
    storage_path: str = ""                              # 公私钥文件存储目录
    id: str = ""                                        # 系统中心ID
    ssl_key_path: str = ""                              # SSL私钥文件路径
    ssl_cert_path: str = ""                             # SSL证书文件路径
    AES_mode: str  = 'CBC'                              # ASE 分组模式
    AES_padding: str  = 'PKCS7Padding'                  # AES 填充模式
    AES_iv: str = '12121212121212121212121212121212'    # TODO随机生成