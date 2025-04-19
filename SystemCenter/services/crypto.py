# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : services/crypto.py
# @Description : 加解密、签名、验签服务 (支持向后兼容) (ECIES  Elliptic Curve Integrated Encryption Scheme 椭圆曲线集成加密方案)
import time
import secrets
from loguru import logger
from typing import Tuple, Optional, Dict, List, Union
from builtin_tools.ellipticCurve import Curve, Point, Util
from builtin_tools.encryption import Hash, AES, ECC, SM2, Base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateNumbers, EllipticCurvePublicNumbers, \
    EllipticCurvePrivateKey


class CryptoService:
    # 默认曲线参数 (SECP256k1)
    DEFAULT_CURVE_PARAMS = {
        'p': 115792089237316195423570985008687907853269984665640564039457584007908834671663,
        'a': 0,
        'b': 7,
        'Gx': 55066263022277343669578718895168534326250603453777594175500187360389116729240,
        'Gy': 32670510020758816978083085130507043184471273380659243275938904335757337482424,
        'N': 115792089237316195423570985008687907852837564279074904382605163141518161494337,
    }

    # 默认算法参数
    DEFAULT_ALGO_PARAMS = {
        'AES': {
            'mode': 'CBC',
            'iv': '12121212121212121212121212121212',
            'padding_type': 'PKCS7Padding'
        },
        'ECC': {
            'curve': None,  # 使用默认曲线
            'base_point': None  # 使用默认基点
        },
        'SM2': {
            'curve': None,  # 使用默认曲线
            'base_point': None,  # 使用默认基点
            'user_id': None
        }
    }

    def __init__(self,
                curve_params: Optional[Dict] = None,
                crypto_algorithms: Optional[Dict[str, Dict]] = None,
                sign_algorithms: Optional[Dict[str, Dict]] = None,
                digest_algorithms: Optional[List[str]] = None,
                ) -> None:
        """
        初始化密码学服务
        :param curve_params: 椭圆曲线参数
        :param crypto_algorithms: 支持的加密算法及其参数，如 {"AES": {"mode": "ECB", "iv": "...", "padding_type": "..."}, "ECC": {...}}
        :param sign_algorithms: 支持的签名算法及其参数，如 {"SM2": {"user_id": "..."}, "DSA": {...}}
        :param digest_algorithms: 支持的消息摘要算法列表，如 ["SHA256", "SM3"]
        """
        # 初始化曲线
        self.curve = self._init_curve(curve_params or self.DEFAULT_CURVE_PARAMS)
        self.base_point = self._init_base_point(curve_params or self.DEFAULT_CURVE_PARAMS)

        # 初始化算法实例
        self.crypto_ciphers = self._init_crypto_ciphers(crypto_algorithms or {"AES": {}})
        self.sign_ciphers = self._init_sign_ciphers(sign_algorithms or {"SM2": {}})
        self.digest_algorithms = [item.upper() for item in digest_algorithms] if digest_algorithms else ["SHA256"]

    def _init_curve(self, params: Dict) -> Curve:
        """初始化椭圆曲线参数"""

        def restore_signed(val: int) -> int:  # 获取负数形式的椭圆曲线参数
            return val if val <= params['p'] // 2 else val - params['p']

        a = restore_signed(params['a'])
        b = restore_signed(params['b'])
        return Curve(params['p'], a, b)

    def _init_base_point(self, params: Dict) -> Point:
        """初始化基点"""
        return Point(self.curve, params['Gx'], params['Gy'], params['N'])

    def _init_crypto_ciphers(self, algorithms: Dict[str, Dict]) -> Dict[str, Union[AES, ECC]]:
        """初始化加密算法实例"""
        ciphers = {}
        for algo, params in algorithms.items():
            algo = algo.upper()
            # 合并默认参数和用户参数
            algo_params = {**self.DEFAULT_ALGO_PARAMS.get(algo, {}), **params}

            match algo:
                case "AES":
                    ciphers[algo] = AES(
                        mode=algo_params['mode'],
                        iv=algo_params['iv'],
                        padding_type=algo_params['padding_type']
                    )
                case "ECC":
                    curve = algo_params['curve'] or self.curve
                    base_point = algo_params['base_point'] or self.base_point
                    ciphers[algo] = ECC(curve, base_point)
                case _:
                    logger.warning(f"不支持的加密算法: {algo}")
        return ciphers

    def _init_sign_ciphers(self, algorithms: Dict[str, Dict]) -> Dict[str, SM2]:
        """初始化签名算法实例"""
        ciphers = {}
        for algo, params in algorithms.items():
            algo = algo.upper()
            # 合并默认参数和用户参数
            algo_params = {**self.DEFAULT_ALGO_PARAMS.get(algo, {}), **params}

            match algo:
                case "SM2":
                    curve = algo_params['curve'] or self.curve
                    base_point = algo_params['base_point'] or self.base_point
                    ciphers[algo] = SM2(curve, base_point, algo_params['user_id'])
                case _:
                    logger.warning(f"不支持的签名算法: {algo}")
        return ciphers

    def generate_keypair(self) -> Tuple[str, Tuple]:
        """生成密钥对"""
        private_key = Hash.digest(
            f"uuid_{time.time_ns()}&{secrets.randbelow(self.curve.p() - 1) + 1}".encode(),
            "md5",
            output_format="int"
        )
        public_key = Util.point_to_tuple(private_key * self.base_point)
        return private_key, public_key

    def encrypt_data(self, message: Union[str, bytes], key: Union[str, tuple],
                    algorithm: Optional[str] = None, additional: Optional[Dict] = None) -> str:
        """
        加密数据
        :param message: 明文数据
        :param key: 加密密钥
        :param algorithm: 指定加密算法，不指定则使用第一个可用的算法
        :param additional: 额外参数
        """
        try:
            algo = (algorithm or list(self.crypto_ciphers.keys())[0]).upper()
            if algo not in self.crypto_ciphers:
                raise ValueError(f"不支持的加密算法: {algo}")

            cipher = self.crypto_ciphers[algo]
            match algo:
                case 'AES':
                    return cipher.aes_encrypt(message, key)
                case 'ECC':
                    if additional and additional.get('multi'):
                        return cipher.ecc_multi_encrypt(message, key)
                    return cipher.ecc_encrypt(message, key)
                case _:
                    raise ValueError(f"不支持的加密算法: {algo}")
        except Exception as e:
            logger.error(f"加密失败: {str(e)}")
            raise

    def decrypt_data(self, message: str, key: Union[str, int],
                    algorithm: Optional[str] = None, additional: Optional[Dict] = None) -> Union[str, bytes]:
        """
        解密数据
        :param message: 密文数据
        :param key: 解密密钥
        :param algorithm: 指定解密算法，不指定则使用第一个可用的算法
        :param additional: 额外参数
        """
        try:
            algo = (algorithm or list(self.crypto_ciphers.keys())[0]).upper()
            if algo not in self.crypto_ciphers:
                raise ValueError(f"不支持的解密算法: {algo}")

            cipher = self.crypto_ciphers[algo]
            match algo:
                case 'AES':
                    return cipher.aes_decrypt(message, key)
                case 'ECC':
                    if additional and additional.get('multi'):
                        return cipher.ecc_multi_decrypt(message, key, additional['blinding'])
                    return cipher.ecc_decrypt(message, key)
                case _:
                    raise ValueError(f"不支持的解密算法: {algo}")
        except Exception as e:
            logger.error(f"解密失败: {str(e)}")
            raise

    def signature(self, public_key: tuple[int, int], private_key: int, message: Union[str, bytes],
                algorithm: Optional[str] = None, additional: Optional[Dict] = None) -> tuple:
        """
        数字签名
        :param public_key: 公钥
        :param private_key: 私钥
        :param message: 原始消息
        :param algorithm: 指定签名算法，不指定则使用第一个可用的算法
        :param additional: 额外参数
        """
        try:
            algo = (algorithm or list(self.sign_ciphers.keys())[0]).upper()
            if algo not in self.sign_ciphers:
                raise ValueError(f"不支持的签名算法: {algo}")

            match algo:
                case 'SM2':
                    za = additional['za'] if additional and 'za' in additional else self.sign_ciphers[
                        algo].compute_sm2_za(public_key)

                    if isinstance(message, str):
                        try:
                            message = Base64.b64decode(message)
                        except:
                            message = message.encode('utf-8')

                    return self.sign_ciphers[algo].signature(message, bytes.fromhex(za), private_key)
                case _:
                    raise ValueError(f"不支持的签名算法: {algo}")
        except Exception as e:
            logger.error(f"签名失败: {str(e)}")
            raise

    def verify_signature(self, public_key: tuple[int, int], signature: Union[tuple[int, int], list[int]],
                        message: Union[str, bytes],
                        algorithm: Optional[str] = None, additional: Optional[Dict] = None) -> bool:
        """
        验证数字签名
        :param public_key: 公钥
        :param signature: 签名数据
        :param message: 原始消息
        :param algorithm: 指定验证算法，不指定则使用第一个可用的算法
        :param additional: 额外参数
        """
        try:
            algo = (algorithm or list(self.sign_ciphers.keys())[0]).upper()
            if algo not in self.sign_ciphers:
                raise ValueError(f"不支持的验证算法: {algo}")

            match algo:
                case 'SM2':
                    za = additional['za'] if additional and 'za' in additional else self.sign_ciphers[
                        algo].compute_sm2_za(public_key)

                    if isinstance(message, str):
                        try:
                            message = Base64.b64decode(message)
                        except:
                            message = message.encode('utf-8')

                    return self.sign_ciphers[algo].verify_sign(signature, message, bytes.fromhex(za), public_key)
                case _:
                    raise ValueError(f"不支持的验证算法: {algo}")
        except Exception as e:
            logger.error(f"验证签名失败: {str(e)}")
            raise

    def digest_message(self, message: Union[str, bytes],
                    algorithm: Optional[str] = None,
                    output_format: str = "hex",
                    length: int = 32) -> Union[str, bytes, int]:
        """
        生成消息摘要
        :param message: 原始消息
        :param algorithm: 指定摘要算法，不指定则使用第一个可用的算法
        :param output_format: 输出格式
        :param length: 消息摘要长度
        """
        try:
            algo = (algorithm or self.digest_algorithms[0]).upper()
            if algo not in self.digest_algorithms:
                raise ValueError(f"不支持的消息摘要算法: {algo}")

            return Hash.digest(message, algo, output_format, length)
        except Exception as e:
            logger.error(f"生成消息摘要失败: {str(e)}")
            raise

    def export_curve_params(self) -> Tuple['Curve', 'Point']:
        """导出当前曲线参数"""
        return self.curve, self.base_point

    def serialize_keypair(self, private_key: EllipticCurvePrivateKey, public_key: ec.EllipticCurvePublicKey) -> Dict[
        str, bytes]:
        """
        序列化密钥对为 PEM 格式
        :param private_key: 私钥对象
        :param public_key: 公钥对象
        :return: 包含 PEM 格式密钥对的字典
        """
        try:
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return {
                'private_key': private_pem,
                'public_key': public_pem
            }
        except Exception as e:
            logger.error(f"序列化密钥对失败: {str(e)}")
            raise

    def generate_keypair_file(self, data: Optional[Dict] = None, curve: ec.EllipticCurve = ec.SECP192R1()) -> Dict[
        str, bytes]:
        """
        生成密钥对文件
        :param data: 可选的密钥数据，包含公钥坐标 (x, y) 和私钥值
        :param curve: 椭圆曲线类型，默认 SECP192R1
        :return: 包含 PEM 格式密钥对的字典
        """
        try:
            if data:
                # 从提供的坐标构造密钥对
                x, y = data['public_key']
                public_numbers = EllipticCurvePublicNumbers(x, y, curve)
                private_numbers = EllipticCurvePrivateNumbers(data['private_key'], public_numbers)
                private_key = private_numbers.private_key(default_backend())
                public_key = private_key.public_key()
            else:
                # 生成新的密钥对
                private_key = ec.generate_private_key(curve, default_backend())
                public_key = private_key.public_key()

            return self.serialize_keypair(private_key, public_key)
        except Exception as e:
            logger.error(f"生成密钥对文件失败: {str(e)}")
            raise

    def extract_keypair_data(self, pem_data: Dict[str, bytes]) -> Dict[str, Union[int, Tuple[int, int]]]:
        """
        从 PEM 文件提取密钥对数据
        :param pem_data: 包含 PEM 格式密钥对的字典
        :return: 包含私钥值和公钥坐标的字典
        """
        try:
            # 加载私钥
            private_key = serialization.load_pem_private_key(
                pem_data['private_key'],
                password=None,
                backend=default_backend()
            )

            if not isinstance(private_key, EllipticCurvePrivateKey):
                raise ValueError("文件未包含有效的 ECC 私钥")

            # 提取私钥数值
            private_numbers = private_key.private_numbers()
            private_value = private_numbers.private_value
            public_numbers = private_numbers.public_numbers

            # 有公钥文件则进行公私钥匹配验证
            if pem_data.get('public_key'):
                external_public = serialization.load_pem_public_key(pem_data['public_key'],
                                                                    backend=default_backend()).public_numbers()
                if (public_numbers.x != external_public.x or
                        public_numbers.y != external_public.y):
                    raise ValueError("公钥与私钥不匹配，可能存在安全风险")

            return {
                "private_key": private_value,
                "public_key": (public_numbers.x, public_numbers.y)
            }
        except Exception as e:
            logger.error(f"提取密钥对数据失败: {str(e)}")
            raise

    @classmethod
    def ecc_point_to_pem_public_key(cls, point: tuple[int, int], curve: ec.EllipticCurve = ec.SECP192R1()) -> str:
        """将用户上传的 tuple 格式公钥转成 pem 形式"""
        x, y = point

        # 构造 EC 公钥对象
        public_numbers = ec.EllipticCurvePublicNumbers(x, y, curve)
        public_key = public_numbers.public_key(default_backend())

        # 导出为 PEM 格式
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return pem.decode()

    @classmethod
    def ecc_public_key_pem_to_point(cls, pem_data: str) -> Tuple[int, int]:
        """将用户上传的 pem 格式公钥转成坐标形式"""
        try:
            key = serialization.load_pem_public_key(
                pem_data.encode(),
                backend=default_backend()
            )

            if not isinstance(key, ec.EllipticCurvePublicKey):
                raise ValueError("提供的密钥不是 ECC 公钥")

            public_numbers = key.public_numbers()
            return public_numbers.x, public_numbers.y
        except Exception as e:
            logger.error(f"公钥转换失败: {str(e)}")
            raise

    def update_algorithm_params(self,
                                crypto_params: Optional[Dict[str, Dict]] = None,
                                sign_params: Optional[Dict[str, Dict]] = None) -> None:
        """
        更新算法参数
        :param crypto_params: 加密算法参数，如 {"AES": {"mode": "ECB", "iv": "...", "padding_type": "..."}}
        :param sign_params: 签名算法参数，如 {"SM2": {"user_id": "..."}}
        """
        if crypto_params:
            for algo, params in crypto_params.items():
                algo = algo.upper()
                if algo in self.crypto_ciphers:
                    # 合并默认参数和用户参数
                    algo_params = {**self.DEFAULT_ALGO_PARAMS.get(algo, {}), **params}
                    match algo:
                        case "AES":
                            self.crypto_ciphers[algo] = AES(
                                mode=algo_params['mode'],
                                iv=algo_params['iv'],
                                padding_type=algo_params['padding_type']
                            )
                        case "ECC":
                            curve = algo_params['curve'] or self.curve
                            base_point = algo_params['base_point'] or self.base_point
                            self.crypto_ciphers[algo] = ECC(curve, base_point)

        if sign_params:
            for algo, params in sign_params.items():
                algo = algo.upper()
                if algo in self.sign_ciphers:
                    # 合并默认参数和用户参数
                    algo_params = {**self.DEFAULT_ALGO_PARAMS.get(algo, {}), **params}
                    match algo:
                        case "SM2":
                            curve = algo_params['curve'] or self.curve
                            base_point = algo_params['base_point'] or self.base_point
                            self.sign_ciphers[algo] = SM2(curve, base_point, algo_params['user_id'])