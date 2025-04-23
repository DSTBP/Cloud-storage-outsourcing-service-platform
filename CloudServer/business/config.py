# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : business/config.py
# @Description : 云服务器配置类
from dataclasses import dataclass


@dataclass
class CloudServerConfig:
    """云服务器配置"""
    host: str = '127.0.0.1'                             # 服务器地址
    port: int = 7777                                    # 服务端口号
    system_center_url: str = ""                         # 系统中心地址
    mongo_uri: str = "mongodb://localhost:27017/"       # MongoDB 连接 URI
    db_name: str = "Server"                             # 服务器数据库名称
    enc_shares_collection: str = 'enc_shares'           # 加密份额表名称
    status: str = 'active'                              # 服务器状态
    storage_path: str = "business/keys"                 # 公私钥文件存储目录
    id: str = ""                                        # TODO 模拟
    ssl_key_path: str = ""                              # SSL私钥文件路径
    ssl_cert_path: str = ""                             # SSL证书文件路径