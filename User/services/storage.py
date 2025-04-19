# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : services/storage.py
# @Description : 本地密钥对存储服务
import os
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger

class StorageService:
    def __init__(self, base_path: str = "storage"):
        """
        初始化存储服务
        :param base_path: 存储目录
        """
        self.base_path = Path(base_path)
        self._ensure_directory()

    def _ensure_directory(self):
        """确保存储目录存在"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"创建存储目录失败: {str(e)}")
            raise

    def _get_expired_files(self, max_age_days: int) -> List[Path]:
        """
        获取过期的文件列表
        :param max_age_days: 最大保留天数
        :return: 过期文件路径列表
        """
        expired_files = []
        current_time = datetime.now()
        max_age = timedelta(days=max_age_days)

        # 检查所有文件
        for file_path in self.base_path.glob('*'):
            if not file_path.is_file():
                continue

            try:
                # 获取文件最后修改时间
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if current_time - mtime > max_age:
                    expired_files.append(file_path)
            except OSError as e:
                logger.warning(f"无法获取文件 {file_path} 的修改时间: {str(e)}")

        return expired_files

    def clean_expired_data(self, max_age_days: int = 30) -> Dict[str, int]:
        """
        清理过期数据
        :param max_age_days: 最大保留天数，默认30天
        :return: 包含清理结果的字典，包括成功和失败的文件数量
        """
        result = {
            'success': 0,
            'failed': 0,
            'total': 0
        }

        try:
            # 获取过期文件列表
            expired_files = self._get_expired_files(max_age_days)
            result['total'] = len(expired_files)

            if not expired_files:
                logger.info("没有需要清理的过期文件")
                return result

            # 清理过期文件
            for file_path in expired_files:
                try:
                    file_path.unlink()
                    result['success'] += 1
                    logger.info(f"已删除过期文件: {file_path}")
                except OSError as e:
                    result['failed'] += 1
                    logger.error(f"删除文件 {file_path} 失败: {str(e)}")

            logger.info(f"清理完成: 成功 {result['success']} 个，失败 {result['failed']} 个，总计 {result['total']} 个文件")
            return result

        except Exception as e:
            logger.error(f"清理过期数据时发生错误: {str(e)}")
            raise

    @staticmethod
    def save_file(file_bytes: bytes, save_dir: str, file_name: str) -> str:
        """
        将字节内容保存为文件到指定目录

        :param file_bytes: 文件的字节内容
        :param save_dir: 要保存到的目录路径
        :param file_name: 文件名（包含扩展名）
        """
        # 如果目录不存在，自动创建
        os.makedirs(save_dir, exist_ok=True)

        # 拼接完整路径
        file_path = os.path.join(save_dir, file_name)
        print(save_dir)
        print(file_bytes)
        print(file_name)
        # 写入文件
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        return file_path

    @staticmethod
    def get_file(file_path: str) -> bytes:
        """
        传入一个文件路径，返回文件字节
        :param file_path: 文件路径
        :return: 文件信息字典
        """
        with open(file_path, 'rb') as f:
            file_bytes = f.read()
        return file_bytes