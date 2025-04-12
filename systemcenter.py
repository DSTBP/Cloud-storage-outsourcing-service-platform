# # -*- coding: utf-8 -*-
# # @Time    : 2024/11/19 21:47
# # @Author  : DSTBP
# # @File    : SystemCenter/core/systemcenter.py
# # @Description : 系统中心核心类
# import math
# import traceback
# import time
# import secrets
# import threading
# import uuid
# from flask import Flask, request
# from loguru import logger
# from typing import Tuple, Optional, Dict
# from SystemCenter.model.config import SystemCenterConfig
# from SystemCenter.model.schema import (
#     ServerStatus, ServerInfo, UserInfo, SystemParameters,
#     FileInfo, UserRegisterRequest, UserLoginRequest, UserPublicKeyRequest, FileUploadRequest, ServerRegisterRequest
# )
# from builtin_tools.ellipticCurve import Util
# from builtin_tools.polynomial import Polynomial
# from services.crypto import CryptoService
# from services.database import DatabaseService
# from services.storage import StorageService
# from utils.converter import TypeConverter as tc
# from utils.network import NetworkAPI
# from utils.validator import validate_system_parameters
#
#
# class SystemCenter:
#     def __init__(self, config: Optional[SystemCenterConfig] = None):
#         """
#         初始化系统中心
#         :param config: 系统中心配置
#         """
#         self.__config = config or SystemCenterConfig()
#         self.__private_key: Optional[int] = None  # SM2 私钥
#         self.__public_key: Optional[Tuple[int, int]] = None  # SM2 公钥
#         self.__system_params: Optional[SystemParameters] = None  # 缓存系统参数
#
#         # 初始化服务实例
#         self.cryptoservice = None
#         self.databaseservice = None
#         self.storageservice = None
#         self.net = NetworkAPI()
#
#         # 创建 Flask 应用
#         self.__app = self.__create_app()
#
#     def __create_app(self) -> Flask:
#         """创建并配置 Flask 应用"""
#         app = Flask(__name__)
#         return app
#
#     def run_server(self):
#         """系统中心实例"""
#         logger.info(
#             f"[SystemCenter (id: {self.__config.id})] 系统中心已启动 (ip: {self.__config.host}, 端口:{self.__config.port})")
#         # 使用线程启动系统中心
#         threading.Thread(
#             target=self.__app.run,
#             kwargs={
#                 'host': '0.0.0.0',
#                 'port': self.__config.port,
#                 'threaded': True
#             },
#             daemon=True
#         ).start()
#
#     def initialize(self, params: dict) -> bool:
#         """初始化系统中心服务"""
#         try:
#             # 初始化服务器服务
#             self.databaseservice = DatabaseService(uri=self.__config.mongo_uri, db_name=self.__config.db_name)
#
#             # 初始化系统参数以及初始化加密服务
#             self._init_system_params(params)
#
#             # 初始化存储服务
#             self.storageservice = StorageService(base_path=f'{self.__config.storage_path}/{self.__config.id}')
#
#             # 从本地提取密钥文件或保存密钥文件
#             if self.__private_key and self.__public_key:
#                 self.__save_keypair()
#             else:
#                 self.__extract_keypair()
#
#             # 注册路由
#             self.__register_routes(self.__app)
#
#             logger.success("[SC] 系统中心初始化完成")
#             return True
#
#         except Exception as e:
#             logger.exception("[SC] 系统中心初始化失败")
#             return False
#
#     def __save_keypair(self):
#         """保存密钥对到本地"""
#         pem_keypair = self.cryptoservice.generate_keypair_file(
#             data={'private_key': self.__private_key, 'public_key': self.__public_key})
#         self.storageservice.save_keypair(pem_keypair)
#
#     def __extract_keypair(self):
#         """从本地加载密钥对"""
#         pem_keypair = self.storageservice.load_keypair()
#         keypair = self.cryptoservice.extract_keypair_data(pem_keypair)
#         self.__private_key, self.__public_key = keypair['private_key'], keypair['public_key']
#
#     def __setup_new_system_params(self, params: dict):
#         self.__config.id = uuid.uuid4().hex
#         validate_system_parameters(params)
#         return {
#             "_id": self.__config.id,
#             'n': params['n'],
#             't': params['t'],
#             'p': params['p'],
#             'a': params['a'] % params['p'],
#             'b': params['b'],
#             'Gx': params['Gx'],
#             'Gy': params['Gy'],
#             'N': params['N'],
#             'H': 'sha256'
#         }
#
#     def __load_existing_system_params(self, params: dict):
#         self.__config.id = params.get('_id')
#         return params
#
#     def _init_system_params(self, params: dict) -> None:
#         """初始化系统参数"""
#         try:
#             # 查找已有初始化参数
#             existing = self.databaseservice.find_document(self.__config.sys_params_collection, {})
#             if existing:
#                 params = self.__load_existing_system_params(existing)
#             else:
#                 params = self.__setup_new_system_params(params)
#
#             # 初始化加密服务
#             self.cryptoservice = CryptoService(
#                 curve_params=params,
#                 sign_algorithms={'SM2': {'user_id': self.__config.id}},
#                 crypto_algorithms={'ECC': {}},
#                 digest_algorithms=[params['H'], 'md5']
#             )
#
#             # 生成 SM2 密钥对、存储系统参数
#             if not params.get('SM2_PublicKey'):
#                 params.update(self.generate_SM2_keypair())
#                 self.databaseservice.bulk_insert(self.__config.sys_params_collection, params)
#
#             self.__system_params = SystemParameters(**params)
#             logger.success("[SC] 系统参数初始化完成")
#
#         except Exception as e:
#             logger.exception("[SC] 系统参数初始化失败")
#             raise
#
#     def __register_routes(self, app: Flask):
#         """注册所有路由处理器"""
#         # 系统参数相关路由
#         app.route('/system/parameters', methods=['GET'])(
#             self.get_system_params)  # 云服务器获取系统参数接口
#
#         # 服务器信息相关路由
#         app.route('/server/register', methods=['POST'])(
#             self.server_register)  # 云服务器上传公钥接口
#
#         # 用户信息相关路由
#         app.route('/user/register', methods=['POST'])(
#             self.user_register)  # 用户注册接口
#
#         app.route('/user/login', methods=['POST'])(
#             self.user_login)  # 用户登录接口
#
#         app.route('/user/public_key', methods=['POST'])(
#             self.user_public_key)  # 用户上传公钥接口
#
#         # 文件信息相关路由
#         app.route('/file/upload', methods=['POST'])(
#             self.handle_file_upload)  # 用户上传文件信息接口
#
#         app.route('/file/download', methods=['POST'])(
#             self.handle_file_download)  # 用户下载文件信息接口
#
#         app.route('/file/list', methods=['GET'])(
#             self.list_file_info)  # 用户获取所有文件信息接口
#
#         app.route('/files/detail', methods=['GET'])(
#             self.get_file_info)  # 用户获取指定文件信息接口
#
#     def __broadcast_to_server(self, endpoint: str, address: list, data: dict) -> dict:
#         """向云服务器群发密钥请求"""
#         return self.net.extract_response_data(
#             self.net.broadcast_request(method='POST', endpoint=endpoint, data=data, address_list=address))
#
#     def __batch_to_server(self, endpoint: str, address_data: dict) -> list:
#         return self.net.extract_response_data(
#             self.net.system_center_batch_request(method='POST', endpoint=endpoint, address_data_map=address_data))
#
#     # ------------------------- 注册方法 -------------------------
#     def server_register(self) -> dict:
#         """注册新服务器"""
#         data = self.net.extract_response_data(request.get_json())
#         register_data = ServerRegisterRequest(**data)
#         server_id = self._generate_unique_id("server")
#         server_info = ServerInfo(
#             **register_data.__dict__,
#             _id=server_id,
#             status=ServerStatus.ACTIVE,
#             last_heartbeat=str(int(time.time() * 1000))
#         )
#
#         self.databaseservice.bulk_insert(
#             self.__config.servers_collection,
#             server_info.__dict__
#         )
#
#         logger.success(f"[SC] 已注册服务器: {server_id}")
#         return {'error_code': 200, 'data': {'server_id': server_id}}
#
#     def _generate_unique_id(self, kind: str, username: str = '') -> Optional[str]:
#         """
#         生成唯一用户/服务器 ID
#         :param username: 用户名
#         :param kind: "server" 或 "user"
#         :return: 生成的唯一 ID，失败返回 None
#         """
#         if kind not in {"server", "user"}:
#             return None
#
#         prefix = "sid" if kind == "server" else "uid"
#         rand_num = secrets.randbelow(self.__system_params.n - 2) + 1
#         return self.cryptoservice.digest_message(
#             f"{prefix}_{time.time_ns()}&{username if kind == 'user' else ''}&{rand_num}",
#             algorithm='md5' if kind == 'server' else self.__system_params.H
#         )
#
#     def cleanup(self) -> None:
#         """清理资源"""
#         try:
#             # TODO
#             pass
#
#         except Exception as e:
#             logger.exception("[SC] 资源清理失败")
#             raise
#
#     def get_system_params(self):
#         """获取系统参数副本"""
#         return {'error_code': 200, 'data': self.__system_params.__dict__}
#
#     def generate_SM2_keypair(self):
#         """生成并发布 SM2 密钥对"""
#         self.__private_key, self.__public_key = self.cryptoservice.generate_keypair()
#         logger.success("[SC] SM2 密钥对已生成")
#         return {'SM2_PublicKey': self.__public_key}
#
#     def user_register(self) -> Dict:
#         """
#         处理用户注册请求
#         :return: 处理结果
#         """
#         try:
#             data = self.net.extract_response_data(request.get_json())
#             register_data = UserRegisterRequest(**data)
#
#             # 检查用户名是否已存在
#             if self.databaseservice.find_document(self.__config.users_collection, {'username': register_data.username}):
#                 return {'error_code': 101, 'message': '用户名已存在'}
#
#             # 创建新用户
#             user_id = self._generate_unique_id("user", register_data.username)
#             user_info = UserInfo(
#                 _id=user_id,
#                 username=register_data.username,
#                 password=data.get("password"),
#                 public_key=None,
#                 created_at=str(int(time.time() * 1000))
#             )
#
#             self.databaseservice.bulk_insert(
#                 self.__config.users_collection,
#                 user_info.__dict__
#             )
#
#             logger.success(f"用户 {register_data.username} 注册成功")
#             return {
#                 'error_code': 200,
#                 'data': {
#                     'user_id': user_id,
#                     'message': '注册成功'
#                 }
#             }
#
#         except Exception as e:
#             logger.exception("处理用户注册请求时发生异常")
#             return {'error_code': 500, 'message': '服务器内部错误'}
#
#     def user_login(self) -> Dict:
#         """
#         处理用户登录请求
#         :return: 处理结果
#         """
#         try:
#             data = self.net.extract_response_data(request.get_json())
#             login_data = UserLoginRequest(**data)
#
#             # 验证用户登录
#             exists = self.databaseservice.find_document(
#                 self.__config.users_collection,
#                 login_data.__dict__,
#                 ['username', 'password', '_id', 'public_key'],
#             )
#
#             if not exists:
#                 return {'error_code': 102, 'message': '用户名或密码错误'}
#
#             # TODO生成登录令牌
#
#             logger.success(f"用户 {login_data.username} 登录成功")
#             return {
#                 'error_code': 200,
#                 'data': {
#                     # 'token': token,
#                     'message': '登录成功'
#                 }
#             }
#
#         except Exception as e:
#             logger.exception("处理用户登录请求时发生异常")
#             return {'error_code': 500, 'message': '服务器内部错误'}
#
#     def user_public_key(self) -> Dict:
#         """
#         上传用户公钥
#         :return: 用户公钥信息
#         """
#         try:
#             data = self.net.extract_response_data(request.get_json())
#             public_key_data = UserPublicKeyRequest(**data)
#             self.databaseservice.update_document(self.__config.users_collection, public_key_data.__dict__)
#             logger.success(f'[SC] {data.get("username")} 用户公钥上传成功')
#         except Exception as e:
#             logger.exception(f"上传用户公钥时发生异常： {e}")
#             return {'error_code': 500, 'message': '服务器内部错误'}
#
#     # ------------------------- 上传方法 -------------------------
#     def handle_file_upload(self):
#         """处理文件上传请求"""
#         try:
#             data = self.net.extract_response_data(request.get_json())
#             upload_data = FileUploadRequest(**data)
#             public_keys = self.databaseservice.find_document(self.__config.servers_collection, {},
#                                                              ['_id', 'public_key'])
#
#             # 生成签密和承诺
#             signcryptions, commits = self.__generate_shares(self.__system_params.__dict__, public_keys,
#                                                             upload_data.file_key)
#
#             # 发布文件信息
#             file_uuid = self.__upload_file_info(data, commits)
#             if not file_uuid:
#                 return {'error_code': 200, 'data': '文件已存在, 请勿重复上传'}
#
#             # 分发签密数据
#             self.__distribute_shares(file_uuid, signcryptions)
#
#             return {'error_code': 200}
#
#         except Exception as e:
#             logger.exception("处理文件上传请求时发生异常")
#             return {'error_code': 500, 'message': '服务器内部错误'}
#
#     def __upload_file_info(self, data: dict, commits: dict) -> str:
#         """上传文件信息"""
#         user_info = self.databaseservice.find_document(self.__config.users_collection, projection=['_id'],
#                                                        filter_query={'username': data['username']})
#         file_uuid = self.cryptoservice.digest_message(f"{data['file_path']}||{data['file_hash']}".encode())
#         file_info = FileInfo(
#             _id=file_uuid,
#             file_ciphertext=data['file_ciphertext'],
#             file_path=data['file_path'],
#             file_hash=data['file_hash'],
#             upload_user=data['username'],
#             upload_time=str(int(time.time() * 1000)),
#             commits=commits
#         )
#
#         self.databaseservice.bulk_insert(
#             self.__config.files_collection,
#             file_info.__dict__
#         )
#         return file_uuid
#
#     def __distribute_shares(self, file_uuid: str, signcryptions: list) -> None:
#         """分发签密数据到各服务器"""
#         server_addresses = self.databaseservice.find_document(self.__config.servers_collection, {},
#                                                               projection=['_id', 'address'])
#         server_data_by_id = {item['server_id']: item for item in signcryptions}
#
#         # 构建 payload_map
#         payload_map = {
#             server['address']: {
#                 **server_data_by_id[server['_id']],
#                 'file_uuid': file_uuid
#             }
#             for server in server_addresses
#             if server['_id'] in server_data_by_id
#         }
#         logger.debug(payload_map)
#
#         self.__batch_to_server(
#             endpoint="sign_cryption",
#             address_data=payload_map
#         )
#
#     def __generate_shares(self, params: dict, public_keys: list, secret: str) -> Tuple[list, dict]:
#         try:
#             # 生成多项式
#             poly = self.__generate_polynomial(params['t'], params['N'], secret)
#
#             # 生成份额和承诺
#             shares = {info['_id']: tc.int_to_hex(poly(tc.hex_to_int(info['_id']))) for info in public_keys}
#
#             curve, base_point = self.cryptoservice.export_curve_params()
#             commits = {i: Util.point_to_tuple(coeff * base_point) for i, coeff in poly.coef.items()}
#
#             # 对份额进行 ECC 加密
#             logger.debug(public_keys)
#             enc_shares = {
#                 info['_id']: self.cryptoservice.encrypt_data(shares[info['_id']], tuple(info['public_key']))
#                 for info in public_keys
#             }
#
#             # 生成签密数据
#             signcryptions = []
#             for sid, enc_share in enc_shares.items():
#                 signcryptions.append({
#                     "server_id": sid,
#                     "ciphertext": enc_share,
#                     "signature": self.cryptoservice.signature(self.__public_key, self.__private_key, enc_share)
#                 })
#             return signcryptions, commits
#         except Exception as e:
#             logger.error(e)
#             logger.error(traceback.format_exc())
#
#     def __generate_polynomial(self, degree: int, modulus: int, secret: str) -> Polynomial:
#         """
#         生成秘密共享多项式
#         :param degree: 最高次 + 1
#         :param modulus: 模数
#         :param secret: 主密钥
#         :return: 多项式实例
#         """
#         secret_int = tc.hex_to_int(secret)
#
#         # 计算分块数
#         blocks_min = math.ceil(secret_int.bit_length() / modulus.bit_length())
#         if blocks_min > degree - 1:
#             raise ValueError("秘密超出范围，可通过增大阈值实现秘密共享")
#
#         blocks_num = secrets.SystemRandom().randint(blocks_min, degree - 1)
#         secret_blocks = self.__split_secret_block(str(secret_int), blocks_num, modulus)
#         if not secret_blocks:
#             raise ValueError("无法找到有效分割方案")
#
#         # 获取随机掩码
#         mask = [1] * blocks_num + [0] * (degree - 1 - blocks_num)
#         secrets.SystemRandom().shuffle(mask)
#
#         # 设置多项式系数
#         coefficients = {0: int(''.join(map(str, mask)), 2)}
#         coefficients.update({
#             i + 1: int(secret_blocks.pop(0)) if m else secrets.randbelow(modulus - 2) + 1
#             for i, m in enumerate(mask)
#         })
#
#         return Polynomial(
#             coef=coefficients,
#             modulo=modulus
#         )
#
#     def __split_secret_block(self, secret: str, blocks_num: int, modulus: int):
#         """
#         将密钥分割成指定数量的块
#         :param secret: 密钥字符串
#         :param blocks_num: 分块数量
#         :param modulus: 模数
#         :return: 分块列表
#         """
#         length = len(secret)
#         avg_size = length // blocks_num  # 每块的平均长度
#         remainder = length % blocks_num  # 余数用于均匀分布
#
#         blocks = []
#         start = 0
#
#         for i in range(blocks_num):
#             extra = 1 if i < remainder else 0  # 让前 remainder 块多分配 1 位
#             end = start + avg_size + extra
#             block = secret[start:end]
#
#             # 确保块不以 0 开头
#             if block.startswith("0") and len(block) > 1:
#                 block = block.lstrip("0") or "0"
#
#             # 确保整数值不超过 modulus
#             if int(block) > modulus:
#                 block = str(modulus)  # 直接截断为最大值
#
#             blocks.append(block)
#             start = end
#
#         return blocks
#
#     # ------------------------- 下载方法 -------------------------
#     def handle_file_download(self) -> dict:
#         """
#         发起文件下载流程
#         :return: 服务器响应字典
#         :raises ValueError: 用户未注册
#         """
#         try:
#             data = self.net.extract_response_data(request.get_json())
#             exists = self.databaseservice.find_document(self.__config.users_collection, projection=['username'],
#                                                         filter_query={'username': data['username']})
#
#             if not exists:
#                 return {'error_code': 404, 'data': '用户未注册'}
#
#             responses = self.__collect_shares(
#                 data['file_uuid'],
#                 data['username'],
#                 self.__select_random_servers()  # t-nums chosen_servers
#             )
#             return {'error_code': 200, 'data': responses}
#         except Exception as e:
#             logger.error(e)
#             logger.error(traceback.format_exc())
#
#     def __select_random_servers(self):
#         """随机选择指定数量的活跃服务器"""
#         active_servers = self.databaseservice.find_document(self.__config.servers_collection,
#                                                             projection=['_id', 'address', 'public_key'],
#                                                             filter_query={'status': "active"})
#
#         if len(active_servers) < self.__system_params.t:
#             raise ValueError(f"[SC] 活跃服务器数量不足 ({len(active_servers)} < {self.__system_params.t})")
#
#         selected = secrets.SystemRandom().sample(active_servers, self.__system_params.t)
#         return selected
#
#     def __collect_shares(self, file_uuid: str, download_username: str, servers: list) -> list:
#         """从选中的服务器收集份额"""
#         user_info = self.databaseservice.find_document(self.__config.users_collection, projection=['_id', 'public_key'],
#                                                        filter_query={'username': download_username})
#         if not user_info:
#             raise ValueError("下载者未注册或未生成公钥")
#
#         broadcast_results = self.__broadcast_to_server(
#             endpoint="download_request",
#             address=[item["address"] for item in servers],
#             data={"file_uuid": file_uuid, "download_user": user_info}
#         )
#         return list(broadcast_results.values())
#
#     # ------------------------- 文件查询方法 -------------------------
#     def get_file_info(self) -> dict:
#         file_uuid = request.args.get('file_uuid')
#         if not file_uuid:
#             return {'error_code': 123}
#
#         file_info = self.databaseservice.find_document(self.__config.files_collection, {'_id': file_uuid},
#                                                        ['file_path', 'file_hash', 'commits', 'file_ciphertext'])
#         if file_info:
#             return {'error_code': 200, 'data': file_info}
#         return {'error_code': 119}  # 文件不存在
#
#     def list_file_info(self) -> dict:
#         res = self.databaseservice.find_document(self.__config.files_collection, {}, ['file_path', '_id'])
#         return {'error_code': 200, 'data': res}



# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : User/core/user.py
# @Description : 用户类
import secrets
from builtin_tools.polynomial import Polynomial
from loguru import logger
from typing import Dict, Tuple, Optional
from User.model.config import UserConfig
from User.model.schema import FileInfo
from builtin_tools.ellipticCurve import Util, INFINITY
from services.crypto import CryptoService
from services.storage import StorageService
from utils.network import NetworkAPI
from utils.converter import TypeConverter as tc


class User:
    """用户基类，实现文件上传者(FU)和下载者(FD)的通用功能"""
    def __init__(self, config: Optional[UserConfig] = None):
        """
        初始化用户实例
        :param config: 用户配置
        """
        self.__config = config or UserConfig()
        self.__private_key: Optional[int] = None            # 用户私钥
        self.__public_key: Optional[Tuple[int, int]] = None # 用户公钥
        self.__system_params: Optional[Dict] = None         # 缓存系统参数
        self.cryptoservice = None
        self.storageservice = None
        self.net = NetworkAPI(base_url=self.__config.system_center_url)

    # ------------------------- 通信方法 -------------------------
    def __post_to_SC(self, endpoint: str, data: dict):
        """
        发送数据到系统中心
        :param endpoint: API端点路径
        :param data: 请求数据
        :return: 响应 JSON
        """
        return self.net.extract_response_data(self.net.post(endpoint, data))

    def __get_from_SC(self, endpoint: str, params: Optional[Dict]=None):
        """ 从系统中心获取数据 """
        return self.net.extract_response_data(self.net.get(endpoint, params=params))


    # ------------------------- 通用方法 -------------------------
    def __generate_keypair(self) -> None:
        """生成用户密钥对"""
        pem_keypair = self.storageservice.load_keypair()
        if pem_keypair:
            keypair = self.cryptoservice.extract_keypair_data(pem_keypair)
            if self.__public_key == keypair.get('public_key'):              # 本地文件未遭到篡改
                self.__private_key = keypair.get('private_key')
        else:
            self.__private_key, self.__public_key = self.cryptoservice.generate_keypair()
            # 保存密钥对到本地
            pem_keypair = self.cryptoservice.generate_keypair_file(
                data={'private_key': self.__private_key, 'public_key': self.__public_key})
            self.storageservice.save_keypair(pem_keypair)
            self.__post_to_SC('user/public_key', {
                "username": self.__config.username,
                "user_id": self.__config.id,
                'public_key': self.__public_key,
            })

    def __register(self, username: str, password: str):
        """
        用户注册
        :param username: 用户名
        """
        if not username or not password:
            raise ValueError("用户名或密码不能为空")

        # 向系统中心注册
        self.__config.username = username
        response = self.__post_to_SC('user/register', {
            "username": username,
            "password": self.cryptoservice.digest_message(password)
        })
        logger.debug(response)
        if not response:
            raise ValueError('用户名已存在，请重新输入')

        self.__config.id = response.get('user_id')
        if self.__config.id:
            self.storageservice = StorageService(base_path=f'{self.__config.storage_path}/{self.__config.id}')
            logger.success(f"[用户 {self.__config.username}] 注册成功，ID: {self.__config.id}")
        return True


    def __login(self, username: str, password: str):
        if not username or not password:
            raise ValueError("用户名或密码不能为空")

        # 向系统中心注册
        self.__config.username = username
        user_info = self.__post_to_SC('user/login', {
            "username": username,
            "password": self.cryptoservice.digest_message(password)
        })

        if not user_info:
            raise ValueError("用户名或密码錯誤")

        if user_info.get('user_id'):
            self.__config.id = user_info['user_id']
            if user_info.get('public_key'):
                self.__public_key = user_info['public_key']
        else:
            raise ValueError("未找到信息")
        self.storageservice = StorageService(base_path=f'{self.__config.storage_path}/{self.__config.id}')
        logger.success(f"[用户 {self.__config.username}] 登录成功，ID: {self.__config.id}")
        return True


    def initialize(self, username: str, password: str, status: str) -> None:
        self.__system_params = self.__get_from_SC("system/parameters")
        self.cryptoservice = CryptoService(
            curve_params=self.__system_params,
            digest_algorithms=['SHA256'],
            crypto_algorithms={'AES': {'mode': 'CBC', 'iv': '12121212121212121212121212121212', 'padding_type': "PKCS7Padding"}, 'ECC': {}}
        )
        if status == 'register':
            self.__register(username, password)
        elif status == 'login':
            self.__login(username, password)

        # 生成公私钥文件
        self.__generate_keypair()


    def get_files_info(self) -> dict:
        """
        获取可下载文件列表
        :return: 文件路径列表
        """
        return self.__get_from_SC("file/list")

    # ------------------------- 文件上传者（FU）专属方法 -------------------------
    def upload_file(self, file_name: str, file_path: str, file_data: bytes):
        """
        文件上传并触发密钥共享流程
        :param file_name: 文件名
        :param file_path: 文件存储路径标识
        :param file_data: 原始文件数据
        :raises ValueError: 参数无效或上传失败
        """
        # 加密文件
        key = secrets.token_hex(16)  # 生成32字节的随机密钥
        ciphertext, file_hash = self.__encrypt_data(key, file_data)

        # 提交可信中心
        response = self.__post_to_SC("file/upload", {
            "file_name": file_name,
            "file_path": file_path,
            "file_ciphertext": ciphertext,
            "file_hash": file_hash,
            "file_key": key,
            "upload_user": self.__config.username
        })

        if not response:
            logger.error(response)
        else:
            logger.success(f"[FU {self.__config.username}] 文件 {file_name} 上传成功")

    def __encrypt_data(self, key: str, data: bytes) -> tuple:
        """
        AES加密数据
        :param key: 加密密钥（32字节）
        :param data: 原始数据
        :return: (密文bytes, 文件哈希)
        """
        return (
            self.cryptoservice.encrypt_data(data, key, algorithm="AES"),
            self.cryptoservice.digest_message(data)
        )


    # ------------------------- 文件下载者（FD）专属方法 -------------------------
    def download_file(self, file_uuid: str) -> str:
        """
        文件下载并解密文件
        :param file_uuid: 文件唯一标识
        :return: 解密后的文件数据
        """

        # 获取文件信息和分片数据
        file_info = FileInfo(**self.__get_from_SC(f"file/detail", params={'file_uuid': file_uuid}))
        shares_data = self.__post_to_SC("file/download", {
            "file_uuid": file_uuid,
            "download_user": self.__config.username
        }).get('enc_shares_list')
        curve, base_point = self.cryptoservice.export_curve_params()

        # 验证服务器响应并解密
        recovery_points = self.__process_shares(curve, base_point, file_info.commits, shares_data)

        # 恢复密钥
        recovered_key = self.__recover_key(recovery_points)

        # 解密文件
        return self.__decrypt_data(file_info.file_ciphertext, recovered_key)

    def __process_shares(self, curve, base_point, commits: dict, shares_data: list):
        """
        验证并解密密钥分片
        :param commits: 承诺值
        :param shares_data: 加密的分片数据
        :return: 验证通过的恢复点列表
        """
        # 预计算承诺值
        commit_points = {
            i: Util.tuple_to_point(curve, (c[0], c[1]))
            for i, c in commits.items()
        }

        recovery_points = []
        for info in shares_data:
            decrypted_share = tc.hex_to_int(self.cryptoservice.decrypt_data(info['enc_share'], self.__private_key, algorithm="ecc"))     # ECC 解密加密份额
            if self.__verify_share(base_point, tc.hex_to_int(info['server_id']), commit_points, decrypted_share):     #TODO int(info['server_id'], 16)
                logger.success(f"分片 {info['server_id']} 验证成功")
                recovery_points.append((int(info['server_id'], 16), decrypted_share))
            else:
                logger.error(f"分片 {info['server_id']} 验证失败")
        return recovery_points

    def __verify_share(self, base_point, sid: int, commits: dict, share: int):
        """
        验证单个分片的承诺
        :param sid: 分片ID
        :param commits: 承诺点字典
        :param share: 分片值
        :return: 验证是否通过
        """
        N = self.__system_params['N']
        logger.debug(commits)
        powers = {idx: pow(sid, int(idx), N) for idx in commits.keys()}

        left = share * base_point
        right = sum((powers[idx] * commit for idx, commit in commits.items()), INFINITY)

        return Util.point_to_tuple(left) == Util.point_to_tuple(right)

    def __recover_key(self, points: list):
        """
        恢复加密密钥
        :param points: 恢复点列表
        :return: 十六进制格式的密钥
        """
        coeffs = Polynomial.lagrange_poly_coeffs(points, self.__system_params['N'])

        mask = [int(x) for x in bin(coeffs[0])[2:].zfill(self.__system_params['t'] - 1)]
        key = ''.join(str(coeffs[i + 1]) for i, v in enumerate(mask) if v)
        return hex(int(key))

    def __decrypt_data(self, ciphertext: bytes, key: str) -> str:
        """
        解密文件数据
        :param ciphertext: 密文
        :param key: 解密密钥
        :return: 解密后的文件内容
        """
        return self.cryptoservice.decrypt_data(ciphertext, key, algorithm="Aes").decode("utf8")
