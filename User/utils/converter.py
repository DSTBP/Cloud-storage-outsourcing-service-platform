# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : utils/network.py
# @Description : 类型转换工具
from typing import Any


class TypeConverter:
    @classmethod
    def int_to_hex(cls, value: int, chunk: int = 8, length: int = 48) -> str:
        """将大整数转为无前缀的十六进制字符串，并按指定长度分段."""
        hex_str = format(value, 'X').zfill(length)  # 转大写并补零到总长度为48字符（192位）
        # 按chunk长度分段（默认8字符）
        return ' '.join([hex_str[i:i + chunk] for i in range(0, len(hex_str), chunk)])

    @classmethod
    def hex_to_int(cls, hex_str: str) -> int:
        """将十六进制字符串（允许空格分隔）转为十进制整数."""
        # 移除所有空格和可能的 '0x' 前缀
        hex_clean = hex_str.replace(" ", "").lower().lstrip("0x")
        return int(hex_clean, 16) if hex_clean else 0

    @classmethod
    def unified_format(cls, data: Any, method: str) -> Any:
        """
        统一数据格式转换
        :param data: 待转换的数据
        :param method: 转换方法 ('i2h': int转hex, 'h2i': hex转int)
        :return: 处理后的数据
        """
        if method not in {"i2h", "h2i"}:
            raise ValueError("Invalid method")

        def convert(value):
            """递归转换各种数据类型"""
            match value:
                case int():
                    return cls.int_to_hex(value) if method == "i2h" else value
                case str() if method == "h2i" and len(value) == 48 + 5:     # hex长度 + 空格数
                    return cls.hex_to_int(value)
                case list() | tuple() | set():
                    return type(value)(convert(v) for v in value)
                case dict():
                    return {convert(k): convert(v) for k, v in value.items()}
                case _:
                    return value
        return convert(data)