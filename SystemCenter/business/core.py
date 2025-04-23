# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : SystemCenter/business/core.py
# @Description : 系统中心核心类
import math
import traceback
import time
import secrets
import threading
import uuid
import os
from flask import Flask, request
from loguru import logger
from flask_cors import CORS
from typing import Tuple, Optional, Dict
from business.config import SystemCenterConfig
from builtin_tools.ellipticCurve import Util
from builtin_tools.polynomial import Polynomial
from services.crypto import CryptoService
from services.database import DatabaseService
from services.storage import StorageService
from utils.converter import TypeConverter as tc
from utils.network import NetworkAPI
from utils.validator import validate_system_parameters
from business.routes import SystemCenterRoutes
from business.schema import (SystemParameters, FileInfo, FileUploadRequest, CenterContext, ServerDownloadRequest)


class SystemCenter:
    def __init__(self, config: Optional[SystemCenterConfig] = None):
        """
        初始化系统中心
        :param config: 系统中心配置
        """
        self.__config = config or SystemCenterConfig()
        self.__private_key: Optional[int] = None  # SM2 私钥
        self.__public_key: Optional[Tuple[int, int]] = None  # SM2 公钥
        self.__system_params: Optional[SystemParameters] = None  # 缓存系统参数
        self.__shutdown_event = threading.Event()  # 添加关闭事件
        self.server_thread = None  # 服务器线程

        # 初始化服务实例
        self.cryptoservice = None
        self.databaseservice = None
        self.storageservice = None
        self.net = NetworkAPI()

        # 创建 Flask 应用
        self.__app = self.__create_app()

    def __create_app(self) -> Flask:
        """创建并配置 Flask 应用"""
        app = Flask(__name__)
        
        # 添加CORS配置
        CORS(app, resources={
            r"/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
        })
        
        return app

    def run_server(self):
        """系统中心实例"""
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("服务器已经在运行中")
            return

        # 如果端口为0或未指定，自动查找可用端口
        if self.__config.port == 0:
            self.__config.port = self.net.find_available_port()
            logger.info(f"自动选择端口: {self.__config.port}")

        def run_flask():
            try:
                with self.__app.app_context():
                    self.__app.run(
                        host='0.0.0.0',      # 监听地址
                        port=self.__config.port,
                        threaded=True,
                        use_reloader=False    # 禁用重载器
                    )
            except Exception as e:
                logger.error(f"服务器运行错误: {str(e)}")
                self.__shutdown_event.set()

        # 重置关闭事件
        self.__shutdown_event.clear()
        
        # 使用线程启动系统中心
        self.server_thread = threading.Thread(target=run_flask, daemon=True)
        self.server_thread.start()
        
        host_ip = self.net.get_local_ip()
        logger.info(f"[SystemCenter (id: {self.__config.id})] 系统中心已启动 (地址:{host_ip}:{self.__config.port})")

    def stop_server(self):
        """停止系统中心服务"""
        try:
            with self.__app.app_context():
                # 设置关闭事件
                self.__shutdown_event.set()
                
                # 关闭 Flask 服务器
                if hasattr(self.__app, 'server'):
                    func = request.environ.get('werkzeug.server.shutdown')
                    if func is None:
                        raise RuntimeError('未找到 werkzeug 服务器')
                    func()
                
                # 等待线程结束
                if self.server_thread and self.server_thread.is_alive():
                    self.server_thread.join(timeout=5.0)
                    
                logger.info("[SystemCenter] 系统中心服务已停止")
        except Exception as e:
            logger.error(f"停止服务失败: {str(e)}")
            raise

    def initialize(self, params: dict) -> bool:
        """初始化系统中心服务"""
        # 初始化服务器服务
        self.databaseservice = DatabaseService(uri=self.__config.mongo_uri, db_name=self.__config.db_name)

        # 初始化系统参数以及初始化加密服务
        self._init_system_params(params)

        # 初始化存储服务
        self.storageservice = StorageService(base_path=f'{self.__config.storage_path}/{self.__config.id}')

        # 从本地提取密钥文件或保存密钥文件
        if self.__private_key and self.__public_key:
            self.__save_keypair()
        else:
            self.__extract_keypair()

        # 生成SSL证书
        self.__config.ssl_key_path = f'{self.__config.storage_path}/{self.__config.id}/ssl.key'
        self.__config.ssl_cert_path = f'{self.__config.storage_path}/{self.__config.id}/ssl.crt'
        if not os.path.exists(self.__config.ssl_key_path) or not os.path.exists(self.__config.ssl_cert_path):
            NetworkAPI.generate_key_and_cert(f'{self.__config.storage_path}/{self.__config.id}')

        # 初始化路由
        self.init_routes()

        logger.success("[SC] 系统中心初始化完成")
        return True

    def __save_keypair(self):
        """保存密钥对到本地"""
        pem_keypair = self.cryptoservice.generate_keypair_file(
            data={'private_key': self.__private_key, 'public_key': self.__public_key})
        self.storageservice.save_keypair(pem_keypair)

    def __extract_keypair(self):
        """从本地加载密钥对"""
        pem_keypair = self.storageservice.load_keypair()
        keypair = self.cryptoservice.extract_keypair_data(pem_keypair)
        self.__private_key, self.__public_key = keypair['private_key'], keypair['public_key']

    def __setup_new_system_params(self, params: dict):
        self.__config.id = uuid.uuid4().hex.upper()
        validate_system_parameters(params)
        return {
            "_id": self.__config.id,
            'n': params['n'],
            't': params['t'],
            'p': params['p'],
            'a': params['a'] % params['p'],
            'b': params['b'],
            'Gx': params['Gx'],
            'Gy': params['Gy'],
            'N': params['N'],
            'H': 'sha256'
        }

    def __load_existing_system_params(self, params: dict):
        self.__config.id = params.get('_id')
        return params

    def _init_system_params(self, params: dict) -> None:
        """初始化系统参数"""
        # 查找已有初始化参数
        existing = self.databaseservice.find_document(self.__config.sys_params_collection, {})
        if existing:
            params = self.__load_existing_system_params(existing)
        else:
            params = self.__setup_new_system_params(params)

        # 初始化加密服务
        self.cryptoservice = CryptoService(
            curve_params=params,
            sign_algorithms={'SM2': {'user_id': self.__config.id}},
            crypto_algorithms={'ECC': {}},
            digest_algorithms=[params['H'], 'md5']
        )

        # 生成 SM2 密钥对、存储系统参数
        if not params.get('SM2_PublicKey'):
            params.update(self.generate_SM2_keypair())
            self.databaseservice.bulk_insert(self.__config.sys_params_collection, params)

        self.__system_params = SystemParameters(**params)
        logger.success("[SC] 系统参数初始化完成")

    def __broadcast_to_server(self, endpoint: str, address: list, data: dict) -> dict:
        """向云服务器群发密钥请求"""
        return self.net.extract_response_data(
            self.net.broadcast_request(method='POST', endpoint=endpoint, data=data, address_list=address))

    def __batch_to_server(self, endpoint: str, address_data: dict) -> list:
        """向云服务器批量发送对应签密数据"""
        return self.net.extract_response_data(
            self.net.system_center_batch_request(method='POST', endpoint=endpoint, address_data_map=address_data))

    def generate_unique_id(self, kind: str, data: Optional[Dict] = None) -> Optional[str]:
        """
        生成唯一用户/服务器 ID
        :param data: 生成唯一ID的辅助数据
        :param kind: "server" 或 "user"
        :return: 生成的唯一 ID，失败返回 None
        """
        if kind not in {"server", "user", 'file'}:
            raise ValueError('错误的 kind')

        if kind == 'file':
            return self.cryptoservice.digest_message(f"{data['file_path']}||{data['file_hash']}||{data['upload_user']}".encode())

        prefix = "sid" if kind == "server" else "uid"
        rand_num = secrets.randbelow(self.__system_params.n - 2) + 1
        return self.cryptoservice.digest_message(
            f"{prefix}_{time.time_ns()}&{data['username'] if kind == 'user' else ''}&{rand_num}",
            algorithm='md5', length = 16 if kind == 'user' else 32
        )

    def generate_SM2_keypair(self):
        """生成 SM2 密钥对"""
        self.__private_key, self.__public_key = self.cryptoservice.generate_keypair()
        return {'SM2_PublicKey': self.__public_key}

    def __upload_file_info(self, file_uuid: str, data: FileUploadRequest, commits: dict) -> None:
        """上传文件信息"""
        file_info = FileInfo(
            _id=file_uuid,
            file_name=data.file_name,
            file_path=data.file_path,
            file_hash=data.file_hash,
            file_ciphertext=data.file_ciphertext,
            file_size=data.file_size,
            upload_time=str(int(time.time() * 1000)),
            upload_user=data.upload_user,
            commits=commits
        )
        self.databaseservice.bulk_insert(self.__config.files_collection, file_info.__dict__)

    def __distribute_shares(self, file_uuid: str, signcryptions: list) -> None:
        """分发份额"""
        server_addresses = self.databaseservice.find_document(self.__config.servers_collection, {},
                                                              projection=['_id', 'address'])
        server_data_by_id = {item['server_id']: item for item in signcryptions}

        # 构建 payload_map
        payload_map = {
            server['address']: {
                **server_data_by_id[server['_id']],
                'file_uuid': file_uuid
            }
            for server in server_addresses
            if server['_id'] in server_data_by_id
        }

        self.__batch_to_server(
            endpoint="sign_cryption",
            address_data=payload_map
        )

    def __generate_signcryptions_commits(self, secret: str) -> Tuple[list, dict]:
        """生成份额"""
        try:
            # 生成多项式
            poly = self.__generate_polynomial(self.__system_params.t, self.__system_params.N, secret)

            # 获取云服务器公钥
            public_keys = self.databaseservice.find_document(self.__config.servers_collection, {},
                                                             ['_id', 'public_key'])
            # 生成份额和承诺
            shares = {info['_id']: tc.int_to_hex(poly(tc.hex_to_int(info['_id']))) for info in public_keys}

            logger.debug(f'shares: {shares}')

            curve, base_point = self.cryptoservice.export_curve_params()
            commits = {i: Util.point_to_tuple(coeff * base_point) for i, coeff in poly.coef.items()}

            # 对份额进行 ECC 加密
            logger.debug(public_keys)
            enc_shares = {
                info['_id']: self.cryptoservice.encrypt_data(shares[info['_id']], tuple(info['public_key']))
                for info in public_keys
            }

            # 生成签密数据
            signcryptions = []
            for sid, enc_share in enc_shares.items():
                signcryptions.append({
                    "server_id": sid,
                    "ciphertext": enc_share,
                    "signature": self.cryptoservice.signature(self.__public_key, self.__private_key, enc_share)
                })
            return signcryptions, commits

        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())

    def __generate_polynomial(self, degree: int, modulus: int, secret: str) -> Polynomial:
        """
        生成秘密共享多项式
        :param degree: 最高次 + 1
        :param modulus: 模数
        :param secret: 主密钥
        :return: 多项式实例
        """
        secret_int = tc.hex_to_int(secret)

        # 计算分块数
        blocks_min = math.ceil(secret_int.bit_length() / modulus.bit_length())
        if blocks_min > degree - 1:
            raise ValueError("秘密超出范围，可通过增大阈值实现秘密共享")

        blocks_num = secrets.SystemRandom().randint(blocks_min, degree - 1)
        secret_blocks = self.__split_secret_block(str(secret_int), blocks_num, modulus)
        if not secret_blocks:
            raise ValueError("无法找到有效分割方案")

        # 获取随机掩码
        mask = [1] * blocks_num + [0] * (degree - 1 - blocks_num)
        secrets.SystemRandom().shuffle(mask)

        # 设置多项式系数
        coefficients = {0: int(''.join(map(str, mask)), 2)}
        coefficients.update({
            i + 1: int(secret_blocks.pop(0)) if m else secrets.randbelow(modulus - 2) + 1
            for i, m in enumerate(mask)
        })

        return Polynomial(
            coef=coefficients,
            modulo=modulus
        )

    def __split_secret_block(self, secret: str, blocks_num: int, modulus: int):
        """
        将密钥分割成指定数量的块
        :param secret: 密钥字符串
        :param blocks_num: 分块数量
        :param modulus: 模数
        :return: 分块列表
        """
        length = len(secret)
        avg_size = length // blocks_num  # 每块的平均长度
        remainder = length % blocks_num  # 余数用于均匀分布

        blocks = []
        start = 0

        for i in range(blocks_num):
            extra = 1 if i < remainder else 0  # 让前 remainder 块多分配 1 位
            end = start + avg_size + extra
            block = secret[start:end]

            # 确保块不以 0 开头
            if block.startswith("0") and len(block) > 1:
                block = block.lstrip("0") or "0"

            # 确保整数值不超过 modulus
            if int(block) > modulus:
                block = str(modulus)  # 直接截断为最大值

            blocks.append(block)
            start = end

        return blocks

    def __select_random_servers(self):
        """随机选择指定数量的活跃服务器"""
        active_servers = self.databaseservice.find_document(self.__config.servers_collection,
                                                            projection=['_id', 'address', 'public_key'],
                                                            filter_query={'status': "active"})

        if len(active_servers) < self.__system_params.t:
            raise ValueError(f"[SC] 活跃服务器数量不足 ({len(active_servers)} < {self.__system_params.t})")

        selected = secrets.SystemRandom().sample(active_servers, self.__system_params.t)
        return selected

    def __collect_shares(self, file_uuid: str, download_username: str) -> list[Dict]:
        """收集份额"""
        # 选择随机服务器
        servers = self.__select_random_servers()
        user_info = self.databaseservice.find_document(self.__config.users_collection, {'username': download_username}, ['_id', 'public_key'])

        if not user_info:
            raise ValueError("下载者未注册或未生成公钥")

        request = ServerDownloadRequest(file_uuid=file_uuid, download_user=user_info)
        # 向服务器请求份额
        broadcast_results = self.__broadcast_to_server(
            endpoint="download_request",
            address=[item["address"] for item in servers],
            data=request.__dict__
        )
        return list(broadcast_results.values())

    def notify_servers_delete_shares(self, file_uuid: str) -> bool:
        """通知服务器删除文件份额"""
        # 获取所有活跃服务器
        servers = self.databaseservice.find_document(
            self.__config.servers_collection,
            {"status": "active"},
            ["address"]
        )
        
        # 广播通知到所有服务器
        broadcast_results = self.__broadcast_to_server(
            endpoint="delete_request",
            address=[item["address"] for item in servers],
            data={"file_uuid": file_uuid}
        )
        
        logger.debug(broadcast_results)

        # 检查广播结果
        success_count = sum(1 for value in broadcast_results.values() if value is None)
        if success_count == len(servers):
            return True
        else:
            return False


    def init_routes(self):
        """注册路由处理器"""
        # 构建中心上下文
        center_context = CenterContext(
            center_id=self.__config.id,
            cryptoservice=self.cryptoservice,
            databaseservice=self.databaseservice,
            net=self.net,
            app=self.__app,
            files_collection=f'{self.__config.files_collection}',
            servers_collection=f'{self.__config.servers_collection}',
            users_collection=f'{self.__config.users_collection}',
            system_params=self.__system_params,
            generate_unique_id=self.generate_unique_id,
            upload_file_info=self.__upload_file_info,
            distribute_shares=self.__distribute_shares,
            collect_shares=self.__collect_shares,
            generate_signcryptions_commits=self.__generate_signcryptions_commits,
            delete_shares=self.notify_servers_delete_shares,
        )
        # 注册路由
        routes = SystemCenterRoutes(center_context)
        routes.register_routes(self.__app)