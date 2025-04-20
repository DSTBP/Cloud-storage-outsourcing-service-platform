# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : services/storage.py
# @Description : 本地密钥对存储服务
import json
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

    def save_keypair(self, key_data: Dict, overwrite: bool = False) -> bool:
        """
        保存密钥对到 PEM 文件
        :param key_data: 包含 'private_key' 和 'public_key' 的字典，值为字节串
        :param overwrite: 是否覆盖已存在的文件
        :return: 保存成功返回 True，否则 False
        """
        private_key_path = self.base_path / 'private.pem'
        public_key_path = self.base_path / 'public.pem'

        if not overwrite and (private_key_path.exists() or public_key_path.exists()):
            logger.warning("密钥文件已存在，未启用覆盖选项")
            return False

        try:
            private_key = key_data.get('private_key')
            public_key = key_data.get('public_key')

            if not private_key or not public_key:
                logger.error("缺失密钥数据")
                return False

            private_key_path.write_bytes(private_key)
            public_key_path.write_bytes(public_key)

            logger.info("密钥文件保存成功")
            return True

        except Exception as e:
            logger.error(f"密钥保存失败: {str(e)}")
            return False

    def load_keypair(self) -> Optional[Dict[str, bytes]]:
        """
        从 PEM 文件中加载密钥对
        :return: 包含 'private_key' 和 'public_key' 的字典，值为字节串，如果失败返回 None
        """
        base_path = self.base_path or Path('.')
        private_key_path = base_path / 'private.pem'
        public_key_path = base_path / 'public.pem'

        if not private_key_path.exists() or not public_key_path.exists():
            logger.warning("密钥文件不存在")
            return None

        try:
            private_key = private_key_path.read_bytes()
            public_key = public_key_path.read_bytes()

            logger.info("密钥文件加载成功")
            return {
                'private_key': private_key,
                'public_key': public_key
            }

        except Exception as e:
            logger.error(f"密钥加载失败: {str(e)}")
            return None

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