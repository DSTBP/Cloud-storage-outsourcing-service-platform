# -*- coding: utf-8 -*-
# @Time    : 2025/04/19 07:23
# @Author  : DSTBP
# @File    : utils/network.py
# @Description : 通信处理工具
import requests
from typing import Optional, Dict, Any, List, Tuple, Union
from utils.converter import TypeConverter as tc
from OpenSSL import crypto
import urllib3
import os
import socket

# 错误码定义
ERROR_MESSAGES = {
    # 100: "请求必须为JSON格式",
    101: "无效的JSON格式",
    102: "上传请求缺少必要参数",
    103: "云服务器 ID 重复，超过最大尝试次数，服务器注册失败",
    104: "用户 ID 重复，超过最大尝试次数，用户注册失败",
    105: "网络连接超时",
    106: "服务器响应错误",
    107: "请求过于频繁",
    108: "无权限删除文件",
    109: "部分服务器删除份额失败",
    110: "份额信息不存在",
    112: "SM2 解签失败",
    114: "文件已存在，请勿重复上传",
    115: "用户名已存在",
    116: "用户名不存在",
    117: "资源不存在",
    118: "系统内部未知错误",
    119: '文件不存在',
    120: '未指定 file uuid',
    123: "权限不足",
    124: "请求频率超限",
    125: "服务不可用",
    126: '服务器处理签密请求发生未知异常',
    127: '处理下载请求发生未知异常',
    128: '密码错误',
    200: "无错误"
}

# 成功状态码
SUCCESS_CODE = 200

# 标准响应格式
RESPONSE_FORMAT = {
    'data': None,
    'status': 'success',
    'error_code': SUCCESS_CODE
}

class NetworkError(Exception):
    """网络通信错误基类"""
    def __init__(self, error_code: int, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(f"Error {error_code}: {message}")


class NetworkAPI:
    def __init__(self, base_url: str = '', timeout: int = 30):
        """
        初始化网络服务
        :param base_url: 基础API地址
        :param timeout: 默认超时时间(秒)
        """
        self.session = requests.Session()
        self.base_url = base_url.rstrip('/') if base_url else None
        self.timeout = timeout
        self._setup_session()

    def _setup_session(self):
        """配置会话默认参数"""
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        # 禁用SSL证书验证
        self.session.verify = False
        # 禁用SSL警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def create_standard_response(self, data: Any = None, error_code: int = SUCCESS_CODE) -> Dict:
        """
        创建标准响应格式
        :param data: 响应数据
        :param error_code: 错误码
        :return: 标准响应格式
        """
        response = RESPONSE_FORMAT.copy()
        if error_code == SUCCESS_CODE:
            response.update({
                'data': tc.unified_format(data, 'i2h'),
                'status': 'success',
                'error_code': SUCCESS_CODE
            })
        else:
            response.update({
                'error_message': ERROR_MESSAGES.get(error_code, ERROR_MESSAGES[118]),
                'status': 'error',
                'error_code': error_code
            })
        return response

    def _handle_response(self, response: requests.Response) -> Dict:
        """
        统一处理响应
        :param response: 响应对象
        :return: 处理后的响应数据
        """
        if response.status_code == 429:
            return self.create_standard_response(error_code=107)

        if response.status_code == 404:
            return self.create_standard_response(error_code=117)

        # 检查响应头中的Content-Type
        content_type = response.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            # 如果不是JSON响应，直接返回原始响应内容
            return self.create_standard_response(data=response.text)

        try:
            response_data = response.json()
        except ValueError:
            return self.create_standard_response(error_code=101)

        # 处理错误情况
        if response_data['error_code'] != SUCCESS_CODE:
            return self.create_standard_response(error_code=response_data['error_code'])

        # 成功响应
        return self.create_standard_response(response_data['data'])

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        发送请求的通用方法
        :param method: HTTP方法
        :param endpoint: API端点
        :param kwargs: 请求参数
        :return: 响应数据
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            return self._handle_response(response)
        except requests.exceptions.Timeout:
            return self.create_standard_response(error_code=105)
        except requests.exceptions.SSLError:
            self.session.verify = False
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                return self._handle_response(response)
            except requests.exceptions.RequestException:
                return self.create_standard_response(error_code=106)
        except requests.exceptions.RequestException:
            return self.create_standard_response(error_code=106)

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送GET请求
        :param endpoint: API端点
        :param params: 请求参数
        :return: 响应数据
        """
        return self._make_request('GET', endpoint, params=params)

    def post(self, endpoint: str, data: Dict) -> Dict:
        """
        发送POST请求
        :param endpoint: API端点
        :param data: 请求数据
        :return: 响应数据
        """
        return self._make_request('POST', endpoint, json=data)

    def put(self, endpoint: str, data: Dict) -> Dict:
        """
        发送PUT请求
        :param endpoint: API端点
        :param data: 请求数据
        :return: 响应数据
        """
        return self._make_request('PUT', endpoint, json=data)

    def delete(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送DELETE请求
        :param endpoint: API端点
        :param params: 请求参数
        :return: 响应数据
        """
        return self._make_request('DELETE', endpoint, params=params)

    def extract_response_data(self, response: Union[Dict, List[Tuple[str, Dict]]]) -> Union[Dict, List[Tuple[str, Dict]]]:
        """
        提取响应数据，支持单个响应和广播响应
        :param response: 响应数据，可以是单个响应或广播响应列表
        :return: 提取后的数据
        """
        if isinstance(response, dict):
            # 处理单个响应
            if 'error_message' in response:
                raise ValueError(response['error_message'])
            return tc.unified_format(response['data'], 'h2i')
        elif isinstance(response, list):
            # 处理广播响应
            results = {}
            for server, res in response:
                if isinstance(res, dict) and 'data' in res:
                    results[server] = tc.unified_format(res['data'], 'h2i')
                else:
                    results[server] = None
            return results
        else:
            raise NetworkError(101, ERROR_MESSAGES[101])

    @staticmethod
    def generate_key_and_cert(base_path='.'):
        """生成SSL证书和私钥"""
        # 创建私钥
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        # 创建证书
        cert = crypto.X509()
        cert.get_subject().C = "CN"
        cert.get_subject().ST = "Beijing"
        cert.get_subject().L = "Beijing"
        cert.get_subject().O = "MyCompany"
        cert.get_subject().OU = "Dev"
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # 有效期为一年
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')

        # 确保目录存在
        os.makedirs(base_path, exist_ok=True)

        # 保存私钥和证书
        key_file_path = os.path.join(base_path, 'ssl.key')
        cert_file_path = os.path.join(base_path, 'ssl.crt')

        with open(key_file_path, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
        with open(cert_file_path, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    @staticmethod
    def is_port_available(port: int) -> bool:
        """
        检查端口是否可用
        :param port: 要检查的端口号
        :return: 如果端口可用返回True，否则返回False
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                return True
            except socket.error:
                return False

    @staticmethod
    def find_available_port(start_port: int = 7777, max_attempts: int = 100) -> int:
        """
        查找可用的端口
        :param start_port: 起始端口号
        :param max_attempts: 最大尝试次数
        :return: 找到的可用端口号，如果没找到则返回-1
        """
        for port in range(start_port, start_port + max_attempts):
            if NetworkAPI.is_port_available(port):
                return port
        return -1

    @staticmethod
    def get_local_ip():
        """
        获取本机IP地址
        """
        try:
            # 创建一个临时socket连接
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))  # 连接到Google的DNS服务器
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            # 如果上述方法失败，尝试获取所有网络接口的IP
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname_ex(hostname)[2][0]
                return local_ip
            except Exception:
                return '127.0.0.1'  # 如果都失败，返回本地回环地址

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
