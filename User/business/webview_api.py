"""
Description:
Author: DSTBP
Date: 2025-04-18 16:36:51
LastEditTime: 2025-04-19 09:05:29
LastEditors: DSTBP
"""
import os
import secrets
from typing import Union
from business.schema import FileUploadRequest, FileUploadResponse, FileDetailRequest, FileDetailResponse, \
    FileDownloadRequest, FileDownloadResponse, SystemParameters
from services.crypto import CryptoService
from services.storage import StorageService
from utils.builtin_tools.ellipticCurve import Util, INFINITY
from utils.builtin_tools.polynomial import Polynomial
from utils.converter import TypeConverter as tc
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePrivateKey
from utils.network import NetworkAPI
import webview

AES_mode: str = 'CBC'  # AES 分组模式
AES_padding: str = 'PKCS7Padding'  # AES 填充模式
AES_iv: str = '12121212121212121212121212121212'  # AES 初始化向量

def update_upload_progress(progress: int, message: str):
    """更新上传进度"""
    window = webview.windows[0]
    window.evaluate_js(f'updateUploadProgress({progress}, "{message}")')


def set_download_progress_callback(callback):
    """设置下载进度回调函数"""
    global download_progress_callback
    download_progress_callback = callback

def update_download_progress(progress: float, message: str):
    """更新下载进度"""
    # 确保进度在0-100之间
    progress = max(0, min(100, progress))
    window = webview.windows[0]
    if 'download_progress_callback' in globals():
        window.evaluate_js(f'window.download_progress_callback({progress}, "{message}")')
    else:
        window.evaluate_js(f'updateDownloadProgress({progress}, "{message}")')

def generate_keypair(system_params):
    cryptoservice = CryptoService(curve_params=tc.unified_format(system_params, 'h2i'))

    private_key, public_key = cryptoservice.generate_keypair()
    pem_keypair = cryptoservice.generate_keypair_file(
        data={'private_key': private_key, 'public_key': public_key})
    
    return {k: v.decode('utf-8') for k, v in pem_keypair.items()}

def match_keypair(private_key: Union[str, bytes], public_key: Union[str, bytes]):
    if isinstance(private_key, str):
        private_key = private_key.encode('utf-8')
    if isinstance(public_key, str):
        public_key = public_key.encode('utf-8')

    # 加载私钥
    private_key = serialization.load_pem_private_key(
        private_key,
        password=None,
        backend=default_backend()
    )

    if not isinstance(private_key, EllipticCurvePrivateKey):
        raise ValueError("文件未包含有效的 ECC 私钥")

    # 提取私钥数值
    private_numbers = private_key.private_numbers()
    public_numbers = private_numbers.public_numbers

    # 有公钥文件则进行公私钥匹配验证
    external_public = serialization.load_pem_public_key(public_key, backend=default_backend()).public_numbers()

    if public_numbers.x != external_public.x or public_numbers.y != external_public.y:
        raise ValueError("公钥与私钥不匹配，可能存在安全风险")

    return True

def keypair_format_conversion(keypair: Union[str, tuple[int, int], tuple[str, str]], method: str):
    method = method.upper()
    try:
        if method == 'PEM':
            keypair = tc.unified_format(keypair, 'h2i')
            return CryptoService.ecc_point_to_pem_public_key(keypair)
        elif method == 'POINT':
            return CryptoService.ecc_public_key_pem_to_point(keypair)
        else:
            raise ValueError("未定义的格式")
    except Exception as e:
        raise ValueError(f"转换失败: {str(e)}")

def select_file():
    """打开文件选择对话框"""
    file_types = ('All Files (*.*)',)
    result = webview.windows[0].create_file_dialog(webview.OPEN_DIALOG, file_types=file_types)
    if result and len(result) > 0:
        return result[0]
    return None

def upload_file(system_center_url: str, system_params: dict, file_path: str, username: str) -> str:
    try:
        update_upload_progress(10, "正在初始化上传...")
        
        net = NetworkAPI(base_url=system_center_url)
        cryptoservice = CryptoService(
            curve_params=tc.unified_format(system_params, 'h2i'),
            digest_algorithms=['SHA256'],
            crypto_algorithms={
                'FASTAES': {
                    'mode': AES_mode,
                    'iv': AES_iv,
                    'padding_type': AES_padding
                },
                'ECC': {}
            }
        )
        storageservice = StorageService()
        
        update_upload_progress(20, "正在读取文件...")
        # 读取文件为字节形式
        file_bytes = storageservice.get_file(file_path)
        file_hash = cryptoservice.digest_message(file_bytes)
        file_size = len(file_bytes)

        # 步骤一：获取文件基本信息
        file_path, file_name = os.path.split(file_path)

        update_upload_progress(30, "正在生成加密密钥...")
        # 步骤二：生成32字节的随机密钥
        key = secrets.token_hex(16)

        update_upload_progress(50, "正在加密文件...")
        # 步骤三：加密文件
        file_ciphertext = cryptoservice.encrypt_data(file_bytes, key, algorithm="FASTAES")

        update_upload_progress(70, "正在上传文件...")
        # 步骤四：上传文件
        req = FileUploadRequest(
            file_name=file_name,
            file_path=file_path,
            file_ciphertext=file_ciphertext,
            file_hash=file_hash,
            file_size=file_size,
            file_key=key,
            upload_user=username
        )
        print(f'upload key: {key}')
        resp = FileUploadResponse(**net.extract_response_data(net.post("file/upload", req.__dict__)))
        
        update_upload_progress(100, "上传成功")
        return resp.file_uuid
    except Exception as e:
        update_upload_progress(0, f"上传失败: {str(e)}")
        raise e

def download_file(system_center_url: str, system_params: dict, username: str, file_uuid: str, private_key, file_dir):
    try:
        update_download_progress(10, "正在初始化下载...")
        system_params = SystemParameters(**tc.unified_format(system_params, 'h2i'))
        net = NetworkAPI(base_url=system_center_url)
        cryptoservice = CryptoService(
            curve_params=system_params.__dict__,
            digest_algorithms=['SHA256'],
            crypto_algorithms={
                'FASTAES': {
                    'mode': AES_mode,
                    'iv': AES_iv,
                    'padding_type': AES_padding
                },
                'ECC': {}
            }
        )
        storageservice = StorageService()

        update_download_progress(20, "正在下载加密文件...")
        req = FileDetailRequest(file_uuid=file_uuid)
        file_info = FileDetailResponse(**net.extract_response_data(net.get("file/detail", req.__dict__)))

        update_download_progress(30, "正在下载加密密钥...")
        req = FileDownloadRequest(file_uuid=file_uuid, download_user=username)
        resp = FileDownloadResponse(**net.extract_response_data(net.post("file/download", req.__dict__)))
        curve, base_point = cryptoservice.export_curve_params()

        update_download_progress(40, "正在验证响应信息...")
        recovery_points = __process_shares(
            system_params=system_params,
            curve=curve,
            base_point=base_point,
            commits=file_info.commits,
            shares_data=resp.enc_shares_list,
            cryptoservice=cryptoservice,
            private_key=cryptoservice.ecc_private_key_pem_to_int(private_key)
        )

        update_download_progress(50, "正在恢复密钥...")
        recovered_key = __recover_key(system_params, recovery_points)

        update_download_progress(70, "正在解密文件...")
        file_bytes = __decrypt_data(file_info.file_ciphertext, recovered_key, cryptoservice)

        update_download_progress(80, "正在验证文件哈希...")
        if cryptoservice.digest_message(file_bytes) == file_info.file_hash:
            update_download_progress(90, "正在保存文件...")
            storageservice.save_file(file_bytes, file_dir, file_info.file_name)
            update_download_progress(100, "下载成功")

    except Exception as e:
        update_download_progress(0, f"上传失败: {str(e)}")
        raise e


# 保存文件对话框
def save_file(filename):
    """通过窗口实例调用保存对话框"""
    try:
        # 获取当前窗口实例
        window = webview.windows[0]
        
        # 调用对话框方法
        save_paths = window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=filename,
            file_types=('PEM Files (*.pem)',)
        )
        return save_paths
    except Exception as e:
        raise RuntimeError(f'保存失败: {str(e)}')


# 写入内容到文件
def write_file(file_path, content):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        raise RuntimeError(f'文件写入失败: {str(e)}')


def __process_shares(system_params, curve, base_point, commits: dict, shares_data: list, cryptoservice, private_key):
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
        decrypted_share = tc.hex_to_int(cryptoservice.decrypt_data(info['enc_share'], private_key, algorithm="ecc"))  # ECC 解密加密份额
        if __verify_share(system_params, base_point, tc.hex_to_int(info['server_id']), commit_points, decrypted_share):  # TODO int(info['server_id'], 16)
            recovery_points.append((int(info['server_id'], 16), decrypted_share))
        else:
            return None
    return recovery_points


def __verify_share(system_params, base_point, sid: int, commits: dict, share: int):
    """
    验证单个分片的承诺
    :param sid: 分片ID
    :param commits: 承诺点字典
    :param share: 分片值
    :return: 验证是否通过
    """
    N = system_params.N
    powers = {idx: pow(sid, int(idx), N) for idx in commits.keys()}

    left = share * base_point
    right = sum((powers[idx] * commit for idx, commit in commits.items()), INFINITY)

    return Util.point_to_tuple(left) == Util.point_to_tuple(right)


def __recover_key(system_params, points: list):
    """
    恢复加密密钥
    :param points: 恢复点列表
    :return: 恢复的密钥
    """
    coeffs = Polynomial.lagrange_poly_coeffs(points, system_params.N)

    mask = [int(x) for x in bin(coeffs[0])[2:].zfill(system_params.t - 1)]
    key = ''.join(str(coeffs[i + 1]) for i, v in enumerate(mask) if v)
    return hex(int(key))


def __decrypt_data(ciphertext: str, key: str, cryptoservice) -> bytes:
    """
    解密数据
    :param ciphertext: Base64编码密文
    :param key: 解密密钥
    :return: 解密后的数据
    """
    res = cryptoservice.decrypt_data(ciphertext, key, algorithm="FASTAES")
    return res.encode() if isinstance(res, str) else res
