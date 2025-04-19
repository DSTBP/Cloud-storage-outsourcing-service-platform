# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : arithmetic.py
# @Description : 加密工具类
import json
import math
import hashlib
import secrets
from typing import Union, Optional
from gmssl import sm3
from loguru import logger
from utils.builtin_tools import arithmetic
from utils.builtin_tools.ellipticCurve import Util, Point, Curve
from Crypto.Cipher import AES as fastaes
from Crypto.Util import Padding
import base64

class Hash:
    """哈希算法类"""
    
    # 哈希算法映射字典
    _ALGORITHMS = {
        'SHA256': hashlib.sha256,  # SHA256 算法
        'MD5': hashlib.md5,        # MD5 算法
        "SM3": sm3.sm3_hash        # 国密 SM3 算法
    }

    @classmethod
    def __convert_to_bytes(cls, data: Union[str, bytes, int]) -> bytes:
        """将输入数据转换为字节数组"""
        if isinstance(data, int):
            return bytearray(data.to_bytes((data.bit_length() + 7) // 8, 'big'))
        if isinstance(data, str):
            return bytearray(data.encode())
        elif isinstance(data, (bytes, bytearray)):
            return bytearray(data)
        raise ValueError("Unsupported data type")

    @classmethod
    def digest(cls, data: Union[str, bytes, int],
              algorithm: str = 'SHA256',
              output_format: str = 'hex',
              length: int = 32
              ) -> Union[str, bytes, int]:
        """
        生成消息摘要
        :param data: 输入数据（支持字符串/字节/整数）
        :param algorithm: 哈希算法（SHA256/MD5/SM3）
        :param length: 消息摘要长度
        :param output_format: 输出格式（hex/bytes/int）
        :return: 指定格式的哈希值
        """
        # 统一转换为字节数组
        data_bytes = cls.__convert_to_bytes(data)
        
        # 根据算法类型计算哈希值
        algo = cls._ALGORITHMS.get(algorithm.upper())
        if not algo:
            raise ValueError(f"不支持的哈希算法: {algorithm}")

        # 计算哈希
        if algorithm.upper() == 'SM3':
            hash_bytes = bytes.fromhex(algo(data_bytes))
        else:
            hash_bytes = algo(data_bytes).digest()

        # 处理哈希值长度（用于 MD5-64）
        if length == 16:
            hash_bytes = hash_bytes[4:12]

        # 格式转换
        return cls._format_output(hash_bytes, output_format)

    @staticmethod
    def _format_output(hash_bytes: bytes, type_format: str) -> Union[str, bytes, int]:
        """格式化输出结果"""
        if type_format == 'hex':
            return hash_bytes.hex().upper()
        if type_format == 'int':
            return int.from_bytes(hash_bytes, 'big')
        return hash_bytes

class ECC:
    """椭圆曲线加密类，实现基于 Koblitz 编码的 ECC 加密"""
    def __init__(self, curve: 'Curve', G: 'Point', K: int = 100000):
        """
        初始化 ECC 加密类
        :param curve: 椭圆曲线对象
        :param G: 基点
        :param K: Koblitz 编码参数，用于调整编码成功率，默认值 100000
        """
        self.curve = curve  # 椭圆曲线
        self.G = G         # 基点
        self.K = K         # Koblitz 编码参数
        self.p = curve.p() # 曲线模数
        # 计算编码相关参数
        self.coord_len = math.ceil(self.p.bit_length() / 8)  # 坐标字节长度
        self.max_block = (self.p // K) - 1                   # 最大块大小
        self.block_size = (self.max_block.bit_length() + 7) // 8  # 字节块大小

    def __serialize_cipher(self, cipher_data: dict) -> str:
        """将密文数据序列化为 Base64 字符串"""
        return Base64.b64encode(json.dumps(cipher_data))

    def __deserialize_cipher(self, cipher_str: str) -> dict:
        """将 Base64 字符串反序列化为密文数据"""
        return json.loads(Base64.b64decode(cipher_str))

    def __encode_block(self, m: int) -> 'Point':
        """
        将单个数据块编码为椭圆曲线上的点
        :param m: 待编码的整数
        :return: 编码后的椭圆曲线点
        """
        x_base = m * self.K
        for j in range(self.K):
            x = x_base + j
            if x >= self.p:
                break
            # 尝试找到合适的 y 坐标
            if y_coords := Util.calc_y_coord(self.curve, x):
                return Point(self.curve, x, y_coords[0])
        raise ValueError(f"编码失败：无法在 {self.K} 次尝试内找到有效点")

    def koblitz_encode(self, message: str) -> list:
        """
        将消息编码为椭圆曲线点列表
        :param message: 待编码的消息字符串
        :return: 编码后的点列表
        """
        # PKCS7 填充
        data = message.encode('utf-8')
        pad_len = self.block_size - (len(data) % self.block_size)
        padded = data + bytes([pad_len] * pad_len)
        
        # 分块编码
        return [self.__encode_block(int.from_bytes(padded[i:i+self.block_size], 'big'))
                for i in range(0, len(padded), self.block_size)]

    def koblitz_decode(self, points: list) -> str:
        """
        将椭圆曲线点列表解码为原始消息
        :param points: 椭圆曲线点列表
        :return: 解码后的消息字符串
        """
        # 将所有点的 x 坐标转换回字节流
        bytes_stream = b''.join(
            (point.x() // self.K).to_bytes(self.block_size, 'big')
            for point in points
        )
        
        # 处理 PKCS7 填充
        pad_len = bytes_stream[-1]
        if not (1 <= pad_len <= self.block_size and 
                bytes_stream[-pad_len:] == bytes([pad_len] * pad_len)):
            raise ValueError("填充无效")
        return bytes_stream[:-pad_len].decode('utf-8')

    def ecc_encrypt(self, plaintext: str, public_key: tuple) -> str:
        """
        加密消息
        :param plaintext: 明文字符串
        :param public_key: 公钥元组 (x, y)
        :return: Base64 编码的密文
        """
        pubkey_point = Util.tuple_to_point(self.curve, public_key)
        points = self.koblitz_encode(plaintext)
        r = secrets.randbelow(self.G.order() - 1) + 1  # 随机数

        return self.__serialize_cipher({
            'c1': Util.point_to_tuple(r * self.G),
            'cts': [Util.point_to_tuple(p + r * pubkey_point) for p in points]
        })

    def ecc_decrypt(self, base64_cipher: str, private_key: int) -> str:
        """
        解密消息
        :param base64_cipher: Base64 编码的密文
        :param private_key: 私钥整数
        :return: 解密后的明文
        """
        cipher_data = self.__deserialize_cipher(base64_cipher)
        if len(cipher_data.keys()) > 2:
            raise ValueError("密文层数错误")

        # 获取辅助点并解密
        key = next(k for k in cipher_data.keys() if k != 'cts')
        cipher1 = Util.tuple_to_point(self.curve, cipher_data[key])
        points = [Util.tuple_to_point(self.curve, ct) - (private_key * cipher1) for ct in cipher_data['cts']]
        return self.koblitz_decode(points)

    def ecc_multi_encrypt(self, base64_cipher: str, public_key: tuple) -> str:
        """
        多层加密：在现有密文上添加一层加密
        :param base64_cipher: 现有的 Base64 编码密文
        :param public_key: 新的公钥
        :return: 多层加密后的密文
        """
        cipher_data = self.__deserialize_cipher(base64_cipher)
        r = secrets.randbelow(self.G.order() - 1) + 1
        pubkey_point = Util.tuple_to_point(self.curve, public_key)

        # 确定新的层数
        c_keys = [k for k in cipher_data if k.startswith('c') and k[1:].isdigit()]
        layer_num = max(int(k[1:]) for k in c_keys) + 1 if c_keys else 1

        # 添加新层加密
        cipher_data[f'c{layer_num}'] = Util.point_to_tuple(r * self.G)
        cipher_data['cts'] = [
            Util.point_to_tuple(Util.tuple_to_point(self.curve, ct) + r * pubkey_point)
            for ct in cipher_data['cts']
        ]
        return self.__serialize_cipher(cipher_data)

    def ecc_multi_decrypt(self, base64_cipher: str, private_key: int, blinding: str) -> str:
        """
        多层解密：移除一层加密
        :param base64_cipher: Base64 编码的多层密文
        :param private_key: 当前层的私钥
        :param blinding: 当前层的辅助密文标识
        :return: 解密一层后的密文
        """
        cipher_data = self.__deserialize_cipher(base64_cipher)
        if blinding not in cipher_data:
            raise KeyError(f"找不到辅助密文 {blinding}")

        # 解密当前层
        cipher_point = Util.tuple_to_point(self.curve, cipher_data[blinding])
        cipher_data['cts'] = [
            Util.point_to_tuple(Util.tuple_to_point(self.curve, ct) - (private_key * cipher_point))
            for ct in cipher_data['cts']
        ]
        del cipher_data[blinding]
        return self.__serialize_cipher(cipher_data)


class SM2:
    """SM2 签名算法实现类"""
    def __init__(self, curve: Curve, G: "Point", user_id: Optional[str] = None):
        """
        初始化 SM2 签名类
        :param curve: 椭圆曲线对象
        :param G: 基点
        """
        self.curve = curve  # 椭圆曲线
        self.G = G          # 基点
        self.p = curve.p()  # 曲线模数
        self.user_id = user_id

    def compute_sm2_za(self, public_key: tuple[int, int], user_id: Optional[str] = None) -> str:
        """计算 SM2 ZA 值"""
        user_id = user_id if user_id else self.user_id
        entlen = len(bytes.fromhex(user_id))*8                 # 转换为16字节
        ENTL = entlen.to_bytes(2, byteorder='big')      # 转换为 16 进制表示的两个字节

        message = b''.join([
            ENTL,
            bytes.fromhex(user_id),
            (self.curve.a() % self.curve.p()).to_bytes(32, byteorder='big'),
            self.curve.b().to_bytes(32, byteorder='big'),
            self.G.x().to_bytes(32, byteorder='big'),
            self.G.y().to_bytes(32, byteorder='big'),
            public_key[0].to_bytes(32, byteorder='big'),
            public_key[1].to_bytes(32, byteorder='big')
        ])
        return Hash.digest(message, "sha256")

    def signature(self, plaintext: bytes, ZA: bytes, private_key: int) -> tuple:
        """
        生成 SM2 数字签名
        :param plaintext: 待签名的明文字节串
        :param ZA: 用户身份标识字节串
        :param private_key: 私钥整数
        :return: 签名值元组 (r, s)
        """
        try:
            # 计算消息摘要
            message = b''.join([ZA, plaintext])
            e = Hash.digest(message, "md5", "int")
            n = self.G.order()  # 获取基点的阶
            r, s = 0, 0

            # 生成签名
            while True:
                k = secrets.randbelow(n-1) + 1  # 生成随机数 k
                x = (k * self.G).x()            # 计算 k*G 的 x 坐标
                r = (x + e) % n                 # 计算 r 值
                
                # 检查 r 值是否有效
                if r == 0 or r + k == n:
                    continue
                
                # 计算 s 值
                s = (arithmetic.mod_inverse((1+private_key), n) * (k-r*private_key)) % n
                if s != 0:  # s 值有效，结束循环
                    break
                    
            return r, s

        except Exception as e:
            logger.error(f"签名过程中发生错误: {e}")
            return None, None

    def verify_sign(self, signature: Union[tuple[int, int], list[int]], message: bytes, ZA: bytes, public_key: Union[tuple[int, int], list[int]]) -> bool:
        """
        验证 SM2 数字签名
        :param signature: 签名数据
        :param message: 原始明文字节串
        :param ZA: 用户身份标识字节串
        :param public_key: 公钥点坐标元组 (x, y)
        :return: 签名验证结果（布尔值）
        """
        try:
            # 准备验证参数
            r, s = tuple(signature)

            pubkey_point = Util.tuple_to_point(self.curve, tuple(public_key))
            message = b''.join([ZA, message])
            n = self.G.order()
            e = Hash.digest(message, "md5", "int")

            # 验证 r 和 s 的范围
            if not (1 <= r <= n - 1 and 1 <= s <= n - 1):
                return False

            # 计算验证值
            t = (r + s) % n
            result_point = s * self.G + t * pubkey_point
            if result_point.x() is None:
                return False
                
            # 验证签名
            R = (e + result_point.x()) % n
            return R == r

        except Exception as e:
            logger.error(f"验签过程中发生错误: {e}")
            return False


class Base64:
    @staticmethod
    def b64encode(data) -> str:
        """
        将字节数据编码为 Base64 字符串
        :param data: 输入数据（字节或字符串）
        :return: Base64编码字符串（字符串）
        """
        base64EncodeChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        if isinstance(data, str):
            data = data.encode('utf-8')
        encoded = []
        for i in range(0, len(data), 3):
            # 每次处理3个字节
            chunk = data[i:i + 3]
            char1 = chunk[0]
            char2 = chunk[1] if len(chunk) > 1 else 0
            char3 = chunk[2] if len(chunk) > 2 else 0

            # 将3个字节转换为4个6位索引
            out1 = (char1 & 0xFC) >> 2
            out2 = ((char1 & 0x03) << 4) | ((char2 & 0xF0) >> 4)
            out3 = ((char2 & 0x0F) << 2) | ((char3 & 0xC0) >> 6)
            out4 = char3 & 0x3F

            # 根据数据长度处理填充
            if len(chunk) == 3:
                encoded.extend([
                    base64EncodeChars[out1],
                    base64EncodeChars[out2],
                    base64EncodeChars[out3],
                    base64EncodeChars[out4]
                ])
            elif len(chunk) == 2:
                encoded.extend([
                    base64EncodeChars[out1],
                    base64EncodeChars[out2],
                    base64EncodeChars[out3],
                    '='
                ])
            else:  # 1个字节
                encoded.extend([
                    base64EncodeChars[out1],
                    base64EncodeChars[out2],
                    '=',
                    '='
                ])
        return ''.join(encoded)

    @staticmethod
    def b64decode(ct: str) -> bytes:
        """
        将Base64字符串解码为原始字节
        :param ct: Base64编码字符串
        :return: 解码后的字节数据
        """
        base64EncodeChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
        base64DecodeChars = {char: idx for idx, char in enumerate(base64EncodeChars)}
        # 移除末尾填充并计算填充量
        s = ct.rstrip('=')
        num_padding = 4 - (len(s) % 4) if len(s) % 4 != 0 else 0
        s += 'A' * num_padding  # 填充无效字符以便统一处理

        decoded = bytearray()
        for i in range(0, len(s), 4):
            chunk = s[i:i + 4]
            if len(chunk) != 4:
                raise ValueError("Invalid Base64 string length")

            # 将字符转换为索引值（无效字符会抛出异常）
            indices = []
            for c in chunk:
                if c == '=':
                    indices.append(0)
                else:
                    try:
                        indices.append(base64DecodeChars[c])
                    except KeyError:
                        raise ValueError(f"Invalid character '{c}' in Base64 string")

            # 合并4个6位值为24位整型
            combined = (indices[0] << 18) | (indices[1] << 12) | (indices[2] << 6) | indices[3]

            # 提取3个字节（根据实际填充量调整）
            decoded.append((combined >> 16) & 0xFF)
            decoded.append((combined >> 8) & 0xFF)
            decoded.append(combined & 0xFF)

        # 移除填充字节
        if num_padding:
            del decoded[-num_padding:]
        return bytes(decoded)


class AES:
    """
    AES 加密算法实现类
    功能特性：
    - 支持 128 位密钥
    - 支持 ECB/CBC/CFB/OFB/CTR 五种工作模式
    - 支持 Zero/PKCS7/ISO10126 三种填充方式
    - 支持多种输入格式：Base64/str/bytes
    - 统一输出格式：Base64
    """
    # AES 标准块大小（16字节）
    BLOCK_SIZE = 16
    
    # 列混合运算矩阵
    MIX_C = (
        (0x02, 0x03, 0x01, 0x01),  # 正向列混合矩阵
        (0x01, 0x02, 0x03, 0x01),
        (0x01, 0x01, 0x02, 0x03),
        (0x03, 0x01, 0x01, 0x02)
    )
    
    # 逆列混合运算矩阵
    I_MIXC = (
        (0x0E, 0x0B, 0x0D, 0x09),  # 逆向列混合矩阵
        (0x09, 0x0E, 0x0B, 0x0D),
        (0x0D, 0x09, 0x0E, 0x0B),
        (0x0B, 0x0D, 0x09, 0x0E)
    )
    
    # AES 轮常数，用于密钥扩展
    RCON = (
        0x01000000, 0x02000000, 0x04000000, 0x08000000,
        0x10000000, 0x20000000, 0x40000000, 0x80000000,
        0x1B000000, 0x36000000
    )
    
    # S 盒（简化为元组形式，提高访问效率）
    S_BOX = tuple(tuple(row) for row in [
        [0x63, 0x7C, 0x77, 0x7B, 0xF2, 0x6B, 0x6F, 0xC5, 0x30, 0x01, 0x67, 0x2B, 0xFE, 0xD7, 0xAB, 0x76],
        [0xCA, 0x82, 0xC9, 0x7D, 0xFA, 0x59, 0x47, 0xF0, 0xAD, 0xD4, 0xA2, 0xAF, 0x9C, 0xA4, 0x72, 0xC0],
        [0xB7, 0xFD, 0x93, 0x26, 0x36, 0x3F, 0xF7, 0xCC, 0x34, 0xA5, 0xE5, 0xF1, 0x71, 0xD8, 0x31, 0x15],
        [0x04, 0xC7, 0x23, 0xC3, 0x18, 0x96, 0x05, 0x9A, 0x07, 0x12, 0x80, 0xE2, 0xEB, 0x27, 0xB2, 0x75],
        [0x09, 0x83, 0x2C, 0x1A, 0x1B, 0x6E, 0x5A, 0xA0, 0x52, 0x3B, 0xD6, 0xB3, 0x29, 0xE3, 0x2F, 0x84],
        [0x53, 0xD1, 0x00, 0xED, 0x20, 0xFC, 0xB1, 0x5B, 0x6A, 0xCB, 0xBE, 0x39, 0x4A, 0x4C, 0x58, 0xCF],
        [0xD0, 0xEF, 0xAA, 0xFB, 0x43, 0x4D, 0x33, 0x85, 0x45, 0xF9, 0x02, 0x7F, 0x50, 0x3C, 0x9F, 0xA8],
        [0x51, 0xA3, 0x40, 0x8F, 0x92, 0x9D, 0x38, 0xF5, 0xBC, 0xB6, 0xDA, 0x21, 0x10, 0xFF, 0xF3, 0xD2],
        [0xCD, 0x0C, 0x13, 0xEC, 0x5F, 0x97, 0x44, 0x17, 0xC4, 0xA7, 0x7E, 0x3D, 0x64, 0x5D, 0x19, 0x73],
        [0x60, 0x81, 0x4F, 0xDC, 0x22, 0x2A, 0x90, 0x88, 0x46, 0xEE, 0xB8, 0x14, 0xDE, 0x5E, 0x0B, 0xDB],
        [0xE0, 0x32, 0x3A, 0x0A, 0x49, 0x06, 0x24, 0x5C, 0xC2, 0xD3, 0xAC, 0x62, 0x91, 0x95, 0xE4, 0x79],
        [0xE7, 0xC8, 0x37, 0x6D, 0x8D, 0xD5, 0x4E, 0xA9, 0x6C, 0x56, 0xF4, 0xEA, 0x65, 0x7A, 0xAE, 0x08],
        [0xBA, 0x78, 0x25, 0x2E, 0x1C, 0xA6, 0xB4, 0xC6, 0xE8, 0xDD, 0x74, 0x1F, 0x4B, 0xBD, 0x8B, 0x8A],
        [0x70, 0x3E, 0xB5, 0x66, 0x48, 0x03, 0xF6, 0x0E, 0x61, 0x35, 0x57, 0xB9, 0x86, 0xC1, 0x1D, 0x9E],
        [0xE1, 0xF8, 0x98, 0x11, 0x69, 0xD9, 0x8E, 0x94, 0x9B, 0x1E, 0x87, 0xE9, 0xCE, 0x55, 0x28, 0xDF],
        [0x8C, 0xA1, 0x89, 0x0D, 0xBF, 0xE6, 0x42, 0x68, 0x41, 0x99, 0x2D, 0x0F, 0xB0, 0x54, 0xBB, 0x16]
    ])
    
    # 逆 S 盒（简化为元组形式，提高访问效率）
    I_SBOX = tuple(tuple(row) for row in [
        [0x52, 0x09, 0x6A, 0xD5, 0x30, 0x36, 0xA5, 0x38, 0xBF, 0x40, 0xA3, 0x9E, 0x81, 0xF3, 0xD7, 0xFB],
        [0x7C, 0xE3, 0x39, 0x82, 0x9B, 0x2F, 0xFF, 0x87, 0x34, 0x8E, 0x43, 0x44, 0xC4, 0xDE, 0xE9, 0xCB],
        [0x54, 0x7B, 0x94, 0x32, 0xA6, 0xC2, 0x23, 0x3D, 0xEE, 0x4C, 0x95, 0x0B, 0x42, 0xFA, 0xC3, 0x4E],
        [0x08, 0x2E, 0xA1, 0x66, 0x28, 0xD9, 0x24, 0xB2, 0x76, 0x5B, 0xA2, 0x49, 0x6D, 0x8B, 0xD1, 0x25],
        [0x72, 0xF8, 0xF6, 0x64, 0x86, 0x68, 0x98, 0x16, 0xD4, 0xA4, 0x5C, 0xCC, 0x5D, 0x65, 0xB6, 0x92],
        [0x6C, 0x70, 0x48, 0x50, 0xFD, 0xED, 0xB9, 0xDA, 0x5E, 0x15, 0x46, 0x57, 0xA7, 0x8D, 0x9D, 0x84],
        [0x90, 0xD8, 0xAB, 0x00, 0x8C, 0xBC, 0xD3, 0x0A, 0xF7, 0xE4, 0x58, 0x05, 0xB8, 0xB3, 0x45, 0x06],
        [0xD0, 0x2C, 0x1E, 0x8F, 0xCA, 0x3F, 0x0F, 0x02, 0xC1, 0xAF, 0xBD, 0x03, 0x01, 0x13, 0x8A, 0x6B],
        [0x3A, 0x91, 0x11, 0x41, 0x4F, 0x67, 0xDC, 0xEA, 0x97, 0xF2, 0xCF, 0xCE, 0xF0, 0xB4, 0xE6, 0x73],
        [0x96, 0xAC, 0x74, 0x22, 0xE7, 0xAD, 0x35, 0x85, 0xE2, 0xF9, 0x37, 0xE8, 0x1C, 0x75, 0xDF, 0x6E],
        [0x47, 0xF1, 0x1A, 0x71, 0x1D, 0x29, 0xC5, 0x89, 0x6F, 0xB7, 0x62, 0x0E, 0xAA, 0x18, 0xBE, 0x1B],
        [0xFC, 0x56, 0x3E, 0x4B, 0xC6, 0xD2, 0x79, 0x20, 0x9A, 0xDB, 0xC0, 0xFE, 0x78, 0xCD, 0x5A, 0xF4],
        [0x1F, 0xDD, 0xA8, 0x33, 0x88, 0x07, 0xC7, 0x31, 0xB1, 0x12, 0x10, 0x59, 0x27, 0x80, 0xEC, 0x5F],
        [0x60, 0x51, 0x7F, 0xA9, 0x19, 0xB5, 0x4A, 0x0D, 0x2D, 0xE5, 0x7A, 0x9F, 0x93, 0xC9, 0x9C, 0xEF],
        [0xA0, 0xE0, 0x3B, 0x4D, 0xAE, 0x2A, 0xF5, 0xB0, 0xC8, 0xEB, 0xBB, 0x3C, 0x83, 0x53, 0x99, 0x61],
        [0x17, 0x2B, 0x04, 0x7E, 0xBA, 0x77, 0xD6, 0x26, 0xE1, 0x69, 0x14, 0x63, 0x55, 0x21, 0x0C, 0x7D]
    ])

    def __init__(self, mode='ECB', iv=None, padding_type='PKCS7Padding'):
        """
        初始化 AES 加密器
        :param mode: 加密模式，支持 ECB/CBC/CFB/OFB/CTR
        :param iv: 初始化向量，CBC/CFB/OFB/CTR 模式需要
        :param padding_type: 填充方式，支持 Zero/PKCS7/ISO10126
        """
        self.mode = mode                    # 加密模式
        self.iv = iv                        # 初始化向量
        self.padding_type = padding_type    # 填充方式

    # ------------------------- 辅助方法 -------------------------
    def __16bytes_xor(self, a, b):
        """对两个16字节数据进行按位异或操作"""
        return [a[i] ^ b[i] for i in range(16)]

    def __iv_hex_to_bytes(self, hex_str):
        """将IV（初始化向量）的十六进制字符串转换为字节列表"""
        if len(hex_str) != 32:
            raise ValueError("IV必须为16字节（32个十六进制字符）。")
        return [int(hex_str[i:i + 2], AES.BLOCK_SIZE) for i in range(0, len(hex_str), 2)]

    # ------------------------- 填充方法 -------------------------
    def __pad(self, byte_list):
        """对数据进行填充，支持多种填充方式"""
        padding_size = AES.BLOCK_SIZE - len(byte_list) % AES.BLOCK_SIZE
        if self.padding_type == 'ZeroPadding':
            return byte_list + [0] * padding_size
        elif self.padding_type == 'PKCS7Padding':
            return byte_list + [padding_size] * padding_size
        elif self.padding_type == 'ISO10126Padding':
            padding = [secrets.randbelow(255) for _ in range(padding_size - 1)]
            padding.append(padding_size)
            return byte_list + padding
        return byte_list

    def __unpad(self, byte_list):
        """去除数据填充"""
        if self.padding_type == 'ZeroPadding':
            return [byte for byte in byte_list if byte != 0]
        elif self.padding_type in ['PKCS7Padding', 'ISO10126Padding']:
            padding_size = byte_list[-1]
            return byte_list[:-padding_size]
        return byte_list

    # ------------------------- 分组方法 -------------------------
    def __xor_block(self, block, output):
        """CFB、OFB、CTR模式需要将AES的输出与明文进行异或"""
        return [b ^ o for b, o in zip(block, output)]

    def __increment_counter(self, counter):
        """增加计数器（用于CTR模式）"""
        counter_int = int.from_bytes(counter, 'big') + 1
        return counter_int.to_bytes(AES.BLOCK_SIZE, 'big')

    # ------------------------- AES核心操作 -------------------------
    def __mul(self, poly1, poly2):
        """多项式相乘"""
        result = 0
        for index in range(poly2.bit_length()):
            if poly2 & 1 << index:
                result ^= poly1 << index
        return result

    def __mod(self, poly, mod=0b100011011):
        """poly模多项式mod"""
        while poly.bit_length() > 8:
            poly ^= mod << poly.bit_length() - 9
        return poly

    def __sub_bytes(self, State):
        """字节替换操作（__sub_bytes）"""
        return [self.S_BOX[i >> 4][i & 0xF] for i in State]

    def __sub_bytes_inv(self, State):
        """逆字节替换操作（__sub_bytes）"""
        return [self.I_SBOX[i >> 4][i & 0xF] for i in State]

    def __shift_rows(self, S):
        """行位移操作（__shift_rows）"""
        return [S[0], S[5], S[10], S[15], S[4], S[9], S[14], S[3],
                S[8], S[13], S[2], S[7], S[12], S[1], S[6], S[11]]

    def __shift_rows_inv(self, S):
        """逆行位移操作（__shift_rows）"""
        return [S[0], S[13], S[10], S[7], S[4], S[1], S[14], S[11],
                S[8], S[5], S[2], S[15], S[12], S[9], S[6], S[3]]

    def __mix_columns(self, State):
        """列混合操作（__mix_columns）"""
        return self.__matrix_mul(self.MIX_C, State)

    def __mix_columns_inv(self, State):
        """逆列混合操作（__mix_columns）"""
        return self.__matrix_mul(self.I_MIXC, State)

    def __matrix_mul(self, M1, M2):
        """矩阵乘法（用于列混合）"""
        M = [0] * AES.BLOCK_SIZE
        for row in range(4):
            for col in range(4):
                for Round in range(4):
                    M[row + col * 4] ^= self.__mul(M1[row][Round], M2[Round + col * 4])
                M[row + col * 4] = self.__mod(M[row + col * 4])
        return M

    def __add_round_key(self, State, RoundKeys, index):
        """轮密钥加法操作"""
        return self.__16bytes_xor(State, RoundKeys[index])

    def __sub_word(self, _4byte_block):
        """4字节块的字节替换，用于密钥扩展"""
        result = 0
        for position in range(4):
            i = _4byte_block >> position * 8 + 4 & 0xf
            j = _4byte_block >> position * 8 & 0xf
            result ^= self.S_BOX[i][j] << position * 8
        return result

    def __rot_word(self, _4byte_block):
        """轮密钥扩展中的字移位操作"""
        return ((_4byte_block & 0xffffff) << 8) + (_4byte_block >> 24)

    def __round_key_generator(self, key):
        """生成AES的轮密钥"""
        w = [key >> 96, key >> 64 & 0xFFFFFFFF, key >> 32 & 0xFFFFFFFF, key & 0xFFFFFFFF] + [0] * 40
        for i in range(4, 44):
            temp = w[i - 1]
            if i % 4 == 0:
                temp = self.__sub_word(self.__rot_word(temp)) ^ self.RCON[i // 4 - 1]
            w[i] = w[i - 4] ^ temp
        return [sum([w[4 * i] << 96, w[4 * i + 1] << 64, w[4 * i + 2] << 32, w[4 * i + 3]]).to_bytes(AES.BLOCK_SIZE, byteorder='big') for i in range(11)]

    # ------------------------- 数据块加解密 -------------------------
    def __aes_encrypt_block(self, block, RoundKeys):
        """
        AES 单个数据块加密
        :param block: 16字节明文块
        :param RoundKeys: 轮密钥列表
        :return: 16字节密文块
        """
        # 初始轮密钥加
        State = self.__add_round_key(block, RoundKeys, 0)
        
        # 9轮标准变换
        for Round in range(1, 10):
            State = self.__sub_bytes(State)      # 字节替换：通过S盒替换每个字节
            State = self.__shift_rows(State)     # 行移位：循环移动状态矩阵的行
            State = self.__mix_columns(State)    # 列混合：通过矩阵乘法混淆每列
            State = self.__add_round_key(State, RoundKeys, Round)  # 轮密钥加
        
        # 最后一轮变换（无列混合）
        State = self.__sub_bytes(State)          # 字节替换
        State = self.__shift_rows(State)         # 行移位
        return self.__add_round_key(State, RoundKeys, 10)  # 最后轮密钥加

    def __aes_decrypt_block(self, block, RoundKeys):
        """
        AES 单个数据块解密
        :param block: 16字节密文块
        :param RoundKeys: 轮密钥列表
        :return: 16字节明文块
        """
        # 初始轮密钥加（使用最后一轮密钥）
        State = self.__add_round_key(block, RoundKeys, 10)
        
        # 9轮逆向变换
        for Round in range(1, 10):
            State = self.__shift_rows_inv(State)     # 逆行移位
            State = self.__sub_bytes_inv(State)      # 逆字节替换
            State = self.__add_round_key(State, RoundKeys, 10 - Round)  # 轮密钥加
            State = self.__mix_columns_inv(State)    # 逆列混合
        
        # 最后一轮逆向变换（无列混合）
        State = self.__shift_rows_inv(State)         # 逆行移位
        State = self.__sub_bytes_inv(State)          # 逆字节替换
        return self.__add_round_key(State, RoundKeys, 0)  # 最后轮密钥加

    # ------------------------- 加解密主函数 -------------------------
    def aes_encrypt(self, plaintext, hex_key: str) -> str:
        """
        AES加密主函数
        :param plaintext: 明文（支持str/bytes字符串）
        :param hex_key: 16字节的十六进制密钥字符串
        :return: Base64编码的密文
        """
        # 初始化
        ciphertext = []
        RoundKeys = self.__round_key_generator(int(hex_key, 16))

        # 处理输入数据
        try:
            pt_bytes = list(plaintext.encode('utf-8')) if isinstance(plaintext, str) else list(plaintext)
        except:
            raise TypeError('明文必须是str或bytes类型')

        # 填充处理
        plaintext = self.__pad(pt_bytes)

        # 检查IV
        if self.mode in ['CFB', 'OFB', 'CTR'] and not self.iv:
            raise ValueError(f"{self.mode}模式需要IV")

        # 获取初始向量
        prev_block = (self.__iv_hex_to_bytes(self.iv) if self.mode in ['CBC', 'CFB', 'OFB', 'CTR'] else None)

        # 分块加密
        cipher_block = ''
        for i in range(0, len(plaintext), AES.BLOCK_SIZE):
            block = plaintext[i:i + AES.BLOCK_SIZE]

            if self.mode == 'ECB':
                # ECB模式：直接加密
                ciphertext.extend(self.__aes_encrypt_block(block, RoundKeys))

            elif self.mode == 'CBC':
                # CBC模式：先异或后加密
                block_xored = self.__16bytes_xor(block, prev_block)
                block_encrypted = self.__aes_encrypt_block(block_xored, RoundKeys)
                ciphertext.extend(block_encrypted)
                prev_block = block_encrypted

            else:  # CFB/OFB/CTR 模式
                if self.mode == 'CFB':
                    # CFB模式：加密前一密文块后与明文异或
                    output = self.__aes_encrypt_block(prev_block, RoundKeys)
                    cipher_block = self.__xor_block(block, output)
                    prev_block = cipher_block

                elif self.mode == 'OFB':
                    # OFB模式：加密前一输出后与明文异或
                    output = self.__aes_encrypt_block(prev_block, RoundKeys)
                    cipher_block = self.__xor_block(block, output)
                    prev_block = output

                elif self.mode == 'CTR':
                    # CTR模式：加密计数器后与明文异或
                    output = self.__aes_encrypt_block(prev_block, RoundKeys)
                    cipher_block = self.__xor_block(block, output)
                    prev_block = self.__increment_counter(prev_block)

                ciphertext.extend(cipher_block)

        return Base64.b64encode(bytes(ciphertext))

    def aes_decrypt(self, ciphertext, hex_key: str) -> bytes:
        """
        AES解密主函数
        :param ciphertext: Base64编码的密文
        :param hex_key: 16字节的十六进制密钥字符串
        :return: Base64编码的明文
        """
        # 初始化
        plaintext = []
        ciphertext = list(Base64.b64decode(ciphertext))
        RoundKeys = self.__round_key_generator(int(hex_key, 16))

        # 检查IV
        if self.mode in ['CFB', 'OFB', 'CTR'] and not self.iv:
            raise ValueError(f"{self.mode}模式需要IV")

        # 获取初始向量
        prev_block = (self.__iv_hex_to_bytes(self.iv) if self.mode in ['CBC', 'CFB', 'OFB', 'CTR'] else None)

        # 分块解密
        for i in range(0, len(ciphertext), AES.BLOCK_SIZE):
            block = ciphertext[i:i + AES.BLOCK_SIZE]

            if self.mode == 'ECB':
                # ECB模式：直接解密
                plaintext.extend(self.__aes_decrypt_block(block, RoundKeys))

            elif self.mode == 'CBC':
                # CBC模式：先解密后异或
                block_decrypted = self.__aes_decrypt_block(block, RoundKeys)
                plaintext.extend(self.__16bytes_xor(block_decrypted, prev_block))
                prev_block = block

            elif self.mode == 'CFB':
                # CFB模式：加密前一密文块后与当前密文异或
                output = self.__aes_encrypt_block(prev_block, RoundKeys)
                plaintext.extend(self.__xor_block(block, output))
                prev_block = block

            elif self.mode == 'OFB':
                # OFB模式：加密前一输出后与密文异或
                output = self.__aes_encrypt_block(prev_block, RoundKeys)
                plaintext.append(self.__xor_block(block, output))
                prev_block = output

            elif self.mode == 'CTR':
                # CTR模式：加密计数器后与密文异或
                output = self.__aes_encrypt_block(prev_block, RoundKeys)
                plaintext.extend(self.__xor_block(block, output))
                prev_block = self.__increment_counter(prev_block)

        # 去除填充并返回
        return bytes(self.__unpad(plaintext))


class FASTAES:
    def __init__(self, mode='ECB', iv=None, padding_type='PKCS7'):
        """
        初始化 AES 加密器
        :param mode: 加密模式，支持 ECB/CBC/CFB/OFB/CTR
        :param iv: 初始化向量，CBC/CFB/OFB/CTR 模式需要
        :param padding_type: 填充方式，支持 Zero/PKCS7/ISO10126
        """
        self.mode_str = mode.upper()
        self.iv = iv[:16] if isinstance(iv, bytes) else iv[:16].encode('utf-8')
        self.padding_type = padding_type.upper()

        self.mode_map = {
            'ECB': fastaes.MODE_ECB,
            'CBC': fastaes.MODE_CBC,
            'CFB': fastaes.MODE_CFB,
            'OFB': fastaes.MODE_OFB,
            'CTR': fastaes.MODE_CTR,
        }

        if self.mode_str not in self.mode_map:
            raise ValueError(f"不支持的加密模式: {self.mode_str}")

    def _pad(self, data: bytes, block_size=16):
        if self.padding_type == 'PKCS7PADDING':
            return Padding.pad(data, block_size, style='pkcs7')
        elif self.padding_type == 'ZEROPADDING':
            return Padding.pad(data, block_size, style='zero')
        elif self.padding_type == 'ISO10126PADDING':
            return Padding.pad(data, block_size, style='iso7816')
        else:
            raise ValueError(f"不支持的填充类型: {self.padding_type}")

    def _unpad(self, data: bytes, block_size=16):
        if self.padding_type == 'PKCS7PADDING':
            return Padding.unpad(data, block_size, style='pkcs7')
        elif self.padding_type == 'ZEROPADDING':
            return Padding.unpad(data, block_size, style='zero')
        elif self.padding_type == 'ISO10126PADDING':
            return Padding.unpad(data, block_size, style='iso7816')
        else:
            raise ValueError(f"不支持的填充类型: {self.padding_type}")

    def aes_encrypt(self, plaintext: bytes, hex_key: str) -> str:
        """
        加密并返回 base64 编码的密文字符串
        """
        key = hex_key[2:] if hex_key.startswith('0x') else hex_key
        key = bytes.fromhex(key)
        mode = self.mode_map[self.mode_str]

        if mode == fastaes.MODE_ECB:
            cipher = fastaes.new(key, mode)
        elif mode in (fastaes.MODE_CBC, fastaes.MODE_CFB, fastaes.MODE_OFB):
            if not self.iv:
                raise ValueError(f"{self.mode_str} 模式需要 iv")
            cipher = fastaes.new(key, mode, iv=self.iv)
        elif mode == fastaes.MODE_CTR:
            cipher = fastaes.new(key, mode)
        else:
            raise ValueError("不支持的模式")

        padded_data = self._pad(plaintext)
        encrypted_bytes = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_bytes).decode('utf-8')  # 返回 base64 字符串

    def aes_decrypt(self, b64_ciphertext: str, hex_key: str) -> bytes:
        """
        解密 base64 密文并返回原始明文
        """
        key = hex_key[2:] if hex_key.startswith('0x') else hex_key
        key = bytes.fromhex(key)
        mode = self.mode_map[self.mode_str]

        ciphertext = base64.b64decode(b64_ciphertext)

        if mode == fastaes.MODE_ECB:
            cipher = fastaes.new(key, mode)
        elif mode in (fastaes.MODE_CBC, fastaes.MODE_CFB, fastaes.MODE_OFB):
            if not self.iv:
                raise ValueError(f"{self.mode_str} 模式需要 iv")
            cipher = fastaes.new(key, mode, iv=self.iv)
        elif mode == fastaes.MODE_CTR:
            cipher = fastaes.new(key, mode)
        else:
            raise ValueError("不支持的模式")

        decrypted = cipher.decrypt(ciphertext)
        return self._unpad(decrypted)
