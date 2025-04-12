# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : utils/network.py
# @Description : 通信处理工具
import requests
from typing import Optional, Dict, Any, List, Tuple, Union
from utils.config.error_codes import ERROR_MESSAGES, SUCCESS_CODE, RESPONSE_FORMAT


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
                'data': data,
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
        try:
            response_data = response.json()
        except ValueError:
            return self.create_standard_response(error_code=101)

        if response.status_code == 404:
            return self.create_standard_response(error_code=117)

        if response.status_code != 200:
            error_code = response_data.get('error_code', 118)
            return self.create_standard_response(error_code=error_code)

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
            return self.create_standard_response(error_code=119)
        except requests.exceptions.RequestException as e:
            return self.create_standard_response(error_code=120)

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

    def broadcast_request(
        self,
        method: str,
        endpoint: str,
        address_list: List[str],
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: Optional[int] = None
    ) -> List[Tuple[str, Dict]]:
        """
        向多个服务器广播请求
        :param method: HTTP方法
        :param endpoint: API端点
        :param address_list: 服务器地址列表
        :param data: 请求数据（POST/PUT请求使用）
        :param params: 请求参数（GET/DELETE请求使用）
        :param timeout: 超时时间（可选）
        :return: 包含(服务器地址, 响应数据)的列表
        """
        results = []
        timeout = timeout or self.timeout

        for server in address_list:
            # 确保服务器地址格式正确
            if not server.startswith(('http://', 'https://')):
                server = f"http://{server}"

            # 创建新的网络服务实例
            api = NetworkAPI(base_url=server, timeout=timeout)

            try:
                # 根据请求方法发送请求
                if method.upper() in ['POST', 'PUT']:
                    response = api.post(endpoint, data) if method.upper() == 'POST' else api.put(endpoint, data)
                else:
                    response = api.get(endpoint, params) if method.upper() == 'GET' else api.delete(endpoint, params)

                results.append((server, response))

            except Exception as e:
                # 记录错误响应
                results.append((
                    server,
                    self.create_standard_response(error_code=120)
                ))

        return results

    def system_center_batch_request(
        self,
        method: str,
        endpoint: str,
        address_data_map: Dict[str, Dict],
        timeout: Optional[int] = None
    ) -> List[Tuple[str, Dict]]:
        """
        SystemCenter 专属批量请求方法
        :param method: HTTP方法
        :param endpoint: API端点
        :param address_data_map: 地址-数据映射字典，格式为 {address: data}
        :param timeout: 超时时间（可选）
        :return: 包含(服务器地址, 响应数据)的列表
        """
        results = []
        timeout = timeout or self.timeout

        for address, data in address_data_map.items():
            # 确保服务器地址格式正确
            if not address.startswith(('http://', 'https://')):
                address = f"http://{address}"

            # 创建新的网络服务实例
            api = NetworkAPI(base_url=address, timeout=timeout)

            try:
                # 根据请求方法发送请求
                if method.upper() in ['POST', 'PUT']:
                    response = api.post(endpoint, data) if method.upper() == 'POST' else api.put(endpoint, data)
                else:
                    response = api.get(endpoint, data) if method.upper() == 'GET' else api.delete(endpoint, data)

                results.append((address, response))

            except Exception as e:
                # 记录错误响应
                results.append((
                    address,
                    self.create_standard_response(error_code=120)
                ))

        return results

    def extract_response_data(self, response: Union[Dict, List[Tuple[str, Dict]]]) -> Union[Dict, List[Tuple[str, Dict]]]:
        """
        提取响应数据，支持单个响应和广播响应
        :param response: 响应数据，可以是单个响应或广播响应列表
        :return: 提取后的数据
        """
        if isinstance(response, dict):
            # 处理单个响应
            if 'data' not in response:
                raise NetworkError(101, ERROR_MESSAGES[101])
            return response['data']
        elif isinstance(response, list):
            # 处理广播响应
            results = {}
            for server, res in response:
                if isinstance(res, dict) and 'data' in res:
                    results[server] = res['data']
                else:
                    results[server] = None
            return results
        else:
            raise NetworkError(101, ERROR_MESSAGES[101])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
