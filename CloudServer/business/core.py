
# -*- coding: utf-8 -*-
# @Time    : 2025/04/20 21:47
# @Author  : DSTBP
# @File    : business/core.py
# @Description : 云服务器核心类
import os
import threading
from flask import Flask
from flask import request
from loguru import logger
from business.schema import ServerContext, ServerRegisterRequest, ServerRegisterResponse, SystemParameters
from utils.network import NetworkAPI
from typing import Tuple, Optional
from services.crypto import CryptoService
from services.storage import StorageService
from services.database import DatabaseService
from business.config import CloudServerConfig
from business.routes import CloudServerRoutes


class CloudServer:
    def __init__(self, config: Optional[CloudServerConfig] = None):
        """
        云服务器节点
        :param config: 服务器配置
        """
        self.__config = config or CloudServerConfig()
        self.__private_key: Optional[int] = None                # ECC 私钥
        self.__public_key: Optional[Tuple[int, int]] = None     # ECC 公钥

        # 初始化服务实例
        self.cryptoservice = None
        self.storageservice = None
        self.databaseservice = None

        # 初始化网络服务
        if not self.__config.system_center_url.startswith(("http://", "https://")):
            self.__config.system_center_url = "http://" + self.__config.system_center_url
        self.net = NetworkAPI(base_url=self.__config.system_center_url)
        self.__config.host = self.net.get_local_ip()

        # 缓存系统参数
        self.__system_params: Optional[SystemParameters] = None

        # 创建 Flask 应用
        self.__app = self.__create_app()

    def __create_app(self) -> Flask:
        """创建并配置 Flask 应用"""
        app = Flask(__name__)
        return app

    def run_server(self):
        """启动云服务器实例"""
        logger.info(f"[Server (id: {self.__config.id})] 云服务器已启动 (ip: {self.__config.host}, 端口:{self.__config.port})")
        # 使用线程启动服务器
        threading.Thread(
            target=self.__app.run,
            kwargs={
                'host': '0.0.0.0',
                'port': self.__config.port,
                'threaded': True,
                # 'ssl_context': (self.__config.ssl_cert_path, self.__config.ssl_key_path) if self.__config.ssl_cert_path and self.__config.ssl_key_path else None
            },
            daemon=True
        ).start()

    def stop_server(self):
        """停止云服务器"""
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            logger.warning("无法关闭服务器（非Werkzeug环境）")
            return
        func()
        logger.info(f"[Server (id: {self.__config.id})] 云服务器已停止")

    def __get_from_SC(self, endpoint: str) -> dict:
        """从系统中心获取数据"""
        return self.net.extract_response_data(self.net.get(endpoint))

    def __post_to_SC(self, endpoint: str, data: dict) -> dict:
        """发送数据到系统中心"""
        return self.net.extract_response_data(self.net.post(endpoint, data=data))

    def initialize(self):
        """
        初始化服务器节点
        1. 获取系统参数
        2. 初始化加密服务
        3. 加载或生成密钥对
        4. 初始化存储和数据库服务
        5. 注册路由
        """
        # 获取系统参数
        self.__system_params = SystemParameters(**self.__get_from_SC("system/parameters"))
        logger.success("获取系统参数成功")

        # 初始化加密服务
        self.cryptoservice = CryptoService(
            curve_params=self.__system_params.__dict__,
            sign_algorithms={'SM2': {'user_id': self.__system_params._id}},
            crypto_algorithms={'ECC': {}}
        )

        # 处理服务器ID和密钥对
        if self.__config.id:
            self.__load_existing_server()
        else:
            self.__setup_new_server()

        # 初始化数据库服务
        self.databaseservice = DatabaseService(
            uri=self.__config.mongo_uri,
            db_name=self.__config.db_name
        )

        # 初始化路由
        self.__config.ssl_key_path = f'{self.__config.storage_path}/{self.__config.id}/ssl.key'
        self.__config.ssl_cert_path = f'{self.__config.storage_path}/{self.__config.id}/ssl.crt'
        if not os.path.exists(self.__config.ssl_key_path) or not os.path.exists(self.__config.ssl_cert_path):
            NetworkAPI.generate_key_and_cert(f'{self.__config.storage_path}/{self.__config.id}')
        self.init_routes()
        logger.success(f"[Server (id: {self.__config.id})] 初始化完成")

    def __load_existing_server(self):
        """加载已存在的服务器配置"""
        self.storageservice = StorageService(
            base_path=f'{self.__config.storage_path}/{self.__config.id}'
        )

        # 加载服务器信息
        server_info = self.storageservice.load_info_json()
        self.__config = CloudServerConfig(**server_info)

        # 加载密钥对
        pem_keypair = self.storageservice.load_keypair()
        keypair = self.cryptoservice.extract_keypair_data(pem_keypair)
        self.__private_key, self.__public_key = keypair['private_key'], keypair['public_key']

    def __setup_new_server(self):
        """设置新服务器"""
        # 生成密钥对
        self.__private_key, self.__public_key = self.cryptoservice.generate_keypair()

        # 注册服务器
        self.__register_server()

        # 初始化存储服务
        self.storageservice = StorageService(f'{self.__config.storage_path}/{self.__config.id}')

        # 保存配置和密钥
        self.storageservice.save_info_json(data=self.__config.__dict__)
        pem_keypair = self.cryptoservice.generate_keypair_file(
            data={'private_key': self.__private_key, 'public_key': self.__public_key}
        )
        self.storageservice.save_keypair(pem_keypair)

    def __register_server(self):
        """注册服务器到系统中心"""
        request = ServerRegisterRequest(
            public_key=self.__public_key,
            address=f"http://{self.__config.host}:{self.__config.port}"
        )
        resp = ServerRegisterResponse(**self.__post_to_SC("server/register", request.__dict__))
        self.__config.id = resp.server_id

    def init_routes(self):
        """注册路由处理器"""
        # 构建服务器上下文
        server_context = ServerContext(
            server_id=self.__config.id,
            cryptoservice=self.cryptoservice,
            databaseservice=self.databaseservice,
            net=self.net,
            encshares_collection=f'{self.__config.enc_shares_collection}_{self.__config.id}',
            system_params=self.__system_params,
            private_key=self.__private_key
        )
        # 注册路由
        routes = CloudServerRoutes(server_context)
        routes.register_routes(self.__app)