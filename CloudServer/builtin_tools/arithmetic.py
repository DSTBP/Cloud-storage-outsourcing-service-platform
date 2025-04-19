# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : arithmetic.py
# @Description : 数论工具函数
import secrets


def qpow(x: int, p: int, mod: int) -> int:
    """
    计算 x^p % mod 的值，使用快速幂算法。
    :param x: 底数
    :param p: 指数
    :param mod: 模 mod
    :return: x^p % mod 的值
    """
    ans = 1
    while p:
        if p & 1:
            ans = (ans * x) % mod
        x = pow(x, 2, mod)
        p >>= 1
    return ans


def exgcd(a: int, b: int) -> tuple[int, int, int]:
    """
    矩阵迭代实现扩展欧几里得算法，求解 a*x + b*y = gcd(a, b) 的解。
    :param a: 整数 a
    :param b: 整数 b
    :return: (g, x, y)，其中 g 是 a 和 b 的最大公约数，x 和 y 满足 Bezout 等式：a*x + b*y = g
    """
    x, last_x = 0, 1
    y, last_y = 1, 0
    while b:
        quot = a // b 
        a, b = b, a % b
        x, last_x = last_x - quot * x, x
        y, last_y = last_y - quot * y, y
    g = a
    return g, last_x, last_y


def mod_inverse(a: int, m: int) -> int:
    """
    计算 a 关于模 m 的逆元，即 ax ≡ 1 (mod m) 的解。
    :param a: 整数 a
    :param m: 模 m
    :return: a 的逆元 x
    """
    _, x, y = exgcd(a, m)
    if x < 0:
        x += m  # 确保逆元为正数
    return x


def mod_divide(num: int, den: int, p: int) -> int:
    """
    计算模 p 下的除法 num / den % p
    :param num: 被除数
    :param den: 除数
    :param p: 模 p
    :return: num / den % p 的值
    """
    _, inv, _ = exgcd(den, p)  # 计算 den 关于 p 的模逆
    return num * inv % p  # 返回模 p 下的结果


def isprime(p: int) -> bool:
    """
    使用 Miller-Rabin 素性测试判断 p 是否为素数。
    :param p: 待检测的数
    :return: True 如果 p 是素数，False 如果 p 不是素数
    """
    # 处理小于 2 的数和 2,3 这两个特殊的素数
    if p < 2:
        return False
    if p == 2 or p == 3:
        return True

    # 将 p-1 分解为 d * 2^r 的形式，其中 d 为奇数
    d = p - 1
    r = 0
    while d % 2 == 0:
        r += 1
        d //= 2

    # 进行 10 轮 Miller-Rabin 测试
    for _ in range(10):
        # 随机选择一个在 [2, p-2] 范围内的基数 a
        a = secrets.randbelow(p - 4) + 2
        
        # 计算 a^d mod p
        x = qpow(a, d, p)
        
        # 如果 x 等于 1 或 p-1，则通过这轮测试
        if x == 1 or x == p - 1:
            continue

        # 进行 r-1 次平方操作
        for _ in range(r - 1):
            x = pow(x, 2, p)
            # 如果在平方过程中遇到 -1，则通过这轮测试
            if x == p - 1:
                break
        # 如果没有在平方过程中遇到 -1，则 p 一定是合数
        else:
            return False

    # 通过所有测试轮次，p 很可能是素数
    return True