# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : User/core/user.py
# @Description : 用户类
import os
import secrets
from builtin_tools.polynomial import Polynomial
from loguru import logger
from typing import Dict, Tuple, Optional, List
from User.model.config import UserConfig
from User.model.schema import (
    FileBaseInfo,
    UserRegisterRequest, UserLoginRequest, UserPublicKeyRequest, FileDetailRequest,
    FileUploadRequest, FileDownloadRequest, UserRegisterResponse, UserLoginResponse, FileInfoListResponse,
    FileUploadResponse, FileDownloadResponse, SystemParameters, FileDetailResponse
)
from builtin_tools.ellipticCurve import Util, INFINITY
from services.crypto import CryptoService
from services.storage import StorageService
from services.database import DatabaseService
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
        self.__private_key: Optional[int] = None                            # 用户私钥
        self.__public_key: Optional[Tuple[int, int]] = None                             # 用户公钥
        self.__system_params: Optional[SystemParameters] = None   # 缓存系统参数

        # 初始化服务实例
        self.cryptoservice = None
        self.storageservice = None
        self.databaseservice = None
        self.net = NetworkAPI(base_url=self.__config.system_center_url)

    def initialize(self, username: str, password: str, status: str) -> bool:
        """
        初始化用户服务
        1. 获取系统参数
        2. 初始化加密服务
        3. 用户注册/登录
        4. 生成或加载密钥对
        5. 初始化存储和数据库服务
        """
        try:
            # 获取系统参数
            self.__system_params = SystemParameters(**self.__get_from_SC("system/parameters"))

            # 初始化加密服务
            self.cryptoservice = CryptoService(
                curve_params=self.__system_params.__dict__,
                digest_algorithms=['SHA256'],
                crypto_algorithms={
                    'AES': {
                        'mode': self.__config.AES_mode,
                        'iv': self.__config.AES_iv,
                        'padding_type': self.__config.AES_padding
                    },
                    'ECC': {}
                }
            )

            # 用户注册/登录
            if status == 'register':
                self.__register(username, password)
            elif status == 'login':
                self.__login(username, password)

            # 初始化存储服务
            self.storageservice = StorageService(
                base_path=f'{self.__config.storage_path}/{self.__config.id}'
            )

            # 初始化数据库服务
            self.databaseservice = DatabaseService(
                uri=self.__config.mongo_uri,
                db_name=self.__config.db_name
            )

            # 生成或加载密钥对
            self.__generate_keypair()
            logger.success(f"[User (id: {self.__config.id})] 初始化完成")
            return True

        except Exception as e:
            logger.exception("[User] 用户初始化失败")
            raise

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
        """从系统中心获取数据"""
        return self.net.extract_response_data(self.net.get(endpoint, params=params))

    # ------------------------- 通用方法 -------------------------
    def __generate_keypair(self) -> None:
        """生成用户密钥对"""
        pem_keypair = self.storageservice.load_keypair()
        if pem_keypair:
            keypair = self.cryptoservice.extract_keypair_data(pem_keypair)
            logger.debug(self.__public_key)
            logger.debug(keypair.get('public_key'))
            if self.__public_key == keypair.get('public_key'):              # 本地文件未遭到篡改
                self.__private_key = keypair.get('private_key')
        else:
            self.__private_key, self.__public_key = self.cryptoservice.generate_keypair()
            # 保存密钥对到本地
            pem_keypair = self.cryptoservice.generate_keypair_file(
                data={'private_key': self.__private_key, 'public_key': self.__public_key})
            self.storageservice.save_keypair(pem_keypair)
            # 上传公钥到系统中心
            request = UserPublicKeyRequest(
                username=self.__config.username,
                user_id=self.__config.id,
                public_key=self.__public_key
            )
            self.__post_to_SC('user/public_key', request.dict())

    def __register(self, username: str, password: str):
        """
        用户注册
        :param username: 用户名
        :param password: 密码
        """
        if not username or not password:
            raise ValueError("用户名或密码不能为空")

        # 向系统中心注册
        self.__config.username = username
        request = UserRegisterRequest(
            username=username,
            password=self.cryptoservice.digest_message(password)
        )
        response = UserRegisterResponse(**self.__post_to_SC('user/register', request.dict()))
        if not response:
            raise ValueError('用户名已存在，请重新输入')

        self.__config.id = response.user_id
        if self.__config.id:
            logger.success(f"[用户 {self.__config.username}] 注册成功，ID: {self.__config.id}")
        return True

    def __login(self, username: str, password: str):
        """
        用户登录
        :param username: 用户名
        :param password: 密码
        """
        if not username or not password:
            raise ValueError("用户名或密码不能为空")

        # 向系统中心登录
        self.__config.username = username
        request = UserLoginRequest(
            username=username,
            password=self.cryptoservice.digest_message(password)
        )

        res = self.__post_to_SC('user/login', request.dict())

        user_info = UserLoginResponse(**res)

        if user_info.user_id:
            self.__config.id = user_info.user_id
            if user_info.public_key:
                self.__public_key = user_info.public_key
        else:
            raise ValueError("未找到用户信息")
        logger.success(f"[用户 {self.__config.username}] 登录成功，ID: {self.__config.id}")
        return True

    def get_files_info(self) -> List[FileBaseInfo]:
        """获取可下载文件列表"""
        resp = FileInfoListResponse(**self.__get_from_SC("file/list"))
        return [FileBaseInfo(**info) for info in resp.files_info]

    # ------------------------- 文件上传者（FU）专属方法 -------------------------
    def upload_file(self, file_path: str):
        """
        文件上传并触发密钥共享流程
        :param file_path: 文件存储路径标识
        :raises ValueError: 参数无效或上传失败
        """
        # 读取文件为字节形式
        file_bytes = self.storageservice.get_file(file_path)

        # 获取文件信息
        file_size = len(file_bytes)
        file_path, file_name = os.path.split(file_path)

        # 加密文件
        key = secrets.token_hex(16)  # 生成32字节的随机密钥
        ciphertext, file_hash = self.__encrypt_data(key, file_bytes)

        # 提交可信中心
        request = FileUploadRequest(
            file_name=file_name,
            file_path=file_path,
            file_ciphertext=ciphertext,
            file_hash=file_hash,
            file_size=file_size,
            file_key=key,
            upload_user=self.__config.username
        )
        resp = FileUploadResponse(**self.__post_to_SC("file/upload", request.dict()))

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
    def download_file(self, file_uuid: str, file_dir: str) -> None:
        """
        文件下载并解密文件
        :param file_uuid: 文件唯一标识
        :param file_dir: 文件保存路径
        :return: 解密后的文件数据
        """
        # 获取文件信息和分片数据
        request = FileDetailRequest(file_uuid=file_uuid)

        file_info = FileDetailResponse(**self.__get_from_SC(f"file/detail", params=request.dict()))

        request = FileDownloadRequest(
            file_uuid=file_uuid,
            download_user=self.__config.username
        )
        resp = FileDownloadResponse(**self.__post_to_SC("file/download", request.dict()))
        curve, base_point = self.cryptoservice.export_curve_params()

        # 验证服务器响应并解密
        recovery_points = self.__process_shares(curve, base_point, file_info.commits, resp.enc_shares_list)

        # 恢复密钥
        recovered_key = self.__recover_key(recovery_points)

        # 解密文件
        file_bytes = self.__decrypt_data(file_info.file_ciphertext, recovered_key)

        if self.cryptoservice.digest_message(file_bytes) == file_info.file_hash:
            # 保存文件
            logger.success("Hash 验证成功!")
            self.storageservice.save_file(file_bytes, file_dir, file_info.file_name)


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
        N = self.__system_params.N
        powers = {idx: pow(sid, int(idx), N) for idx in commits.keys()}

        left = share * base_point
        right = sum((powers[idx] * commit for idx, commit in commits.items()), INFINITY)

        return Util.point_to_tuple(left) == Util.point_to_tuple(right)

    def __recover_key(self, points: list):
        """
        恢复加密密钥
        :param points: 恢复点列表
        :return: 恢复的密钥
        """
        coeffs = Polynomial.lagrange_poly_coeffs(points, self.__system_params.N)

        mask = [int(x) for x in bin(coeffs[0])[2:].zfill(self.__system_params.t - 1)]
        key = ''.join(str(coeffs[i + 1]) for i, v in enumerate(mask) if v)
        return hex(int(key))

    def __decrypt_data(self, ciphertext: str, key: str) -> str:
        """
        解密数据
        :param ciphertext: Base64编码密文
        :param key: 解密密钥
        :return: 解密后的数据
        """
        return self.cryptoservice.decrypt_data(ciphertext, key, algorithm="Aes")
