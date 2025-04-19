# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : utils/validator.py
# @Description : 数据校验与完整性检查
from builtin_tools import arithmetic
from builtin_tools.ellipticCurve import Curve, Point, INFINITY


def validate_system_parameters(params: dict) -> None:
    """
    验证系统参数有效性
    :param params: 包含系统参数的字典
    """
    curve = Curve(params['p'], params['a'] - params['p'], params['b'])

    if not all(isinstance(v, int) for v in [params['n'], params['t'], params['p']]):
        raise ValueError("参数必须为整数")
    if params['n'] <= 0 or params['n'] > params['p']:
        raise ValueError("n 必须是正整数且 n <= p")
    if params['t'] <= 0 or params['t'] > params['n']:
        raise ValueError("t 必须是正整数且 t <= n")
    if not arithmetic.isprime(params['p']):
        raise ValueError("p 必须是正奇素数")
    if not curve.contains_point(params['Gx'], params['Gy']):
        raise ValueError("基点不在椭圆曲线上")
    if params['N'] * Point(curve, params['Gx'], params['Gy']) != INFINITY:
        raise ValueError("基点的阶不正确")
