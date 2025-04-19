# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : ellipticCurve.py
# @Description : 椭圆曲线工具类
from typing import Optional
from loguru import logger
from builtin_tools import arithmetic


class Curve:
    """
    椭圆曲线类
    """
    def __init__(self, p: int, a: int, b: int):
        """
        初始化椭圆曲线
        :param p: 曲线的模数
        :param a: 曲线方程中的系数 a
        :param b: 曲线方程中的系数 b
        """
        self.__p = p
        self.__a = a
        self.__b = b

    def contains_point(self, x: int, y: int) -> bool:
        """检查点 (x, y) 是否在曲线上"""
        return (y ** 2 - x ** 3 - self.__a * x - self.__b) % self.__p == 0

    def p(self):
        """返回曲线的模数"""
        return self.__p

    def a(self):
        """返回曲线方程中的系数 a"""
        return self.__a

    def b(self):
        """返回曲线方程中的系数 b"""
        return self.__b


class Point:
    """
    椭圆曲线上的点类
    """
    def __init__(self, curve: Optional['Curve'], x: Optional[int], y: Optional[int], order=None):
        """
        初始化点
        :param curve: 所在椭圆曲线
        :param x: 点的 x 坐标
        :param y: 点的 y 坐标
        :param order: 点的阶（可选）
        """
        self.__curve = curve
        self.__x = x
        self.__y = y
        self.__order = order

        # 确认点是否在曲线上
        if curve and (x is not None or y is not None):
            assert curve.contains_point(x, y)

    def __eq__(self, other: 'Point') -> bool:
        """
        判断两个点是否相等
        :param other: 另一个点，类型为 EllipticPoint
        :return: 如果两个点相等则返回 True，否则返回 False
        """
        if isinstance(other, Point):
            return (
                    self.__curve == other.__curve
                    and self.__x == other.__x
                    and self.__y == other.__y
            )
        return NotImplemented

    def __neg__(self) -> 'Point':
        """
        计算点的负值，即点 P 的相反数
        :return: 返回点的负值 (-P)
        """
        if self == INFINITY:
            return INFINITY
        return Point(self.__curve, self.__x, self.__curve.p() - self.__y)

    def __add__(self, other: 'Point') -> 'Point':
        """
        实现椭圆曲线上的点加法
        如果两个点相等，使用椭圆曲线的公式计算斜率并得到新的点。
        如果两个点不同，则按照椭圆曲线点加法的规则计算斜率。
        :param other: 另一个点
        :return: 返回点加法的结果
        """
        # 处理无穷远点
        if other == INFINITY:
            return self
        if self == INFINITY:
            return other

        # 错误处理
        if not isinstance(other, Point):
            return NotImplemented
        assert self.__curve == other.__curve

        p = self.__curve.p()

        # 如果两个点的 x 坐标相等但 y 坐标互为相反数，则返回无穷远点
        if self.__x == other.__x and (self.__y + other.__y) % p == 0:
            return INFINITY

        if self.__x == other.__x:
            # 处理自加的情况
            l = (3 * self.__x ** 2 + self.__curve.a()) * arithmetic.mod_inverse(2 * self.__y, p) % p
        else:
            # 普通点加法
            l = (other.__y - self.__y) * arithmetic.mod_inverse(other.__x - self.__x, p) % p

        x3 = (l ** 2 - self.__x - other.__x) % p
        y3 = (l * (self.__x - x3) - self.__y) % p

        return Point(self.__curve, x3, y3)

    def __sub__(self, other: 'Point') -> 'Point':
        """
        实现椭圆曲线上的点减法
        :param other: 另一个点，类型为 EllipticPoint
        :return: 返回点减法的结果
        """
        return self + (-other)

    def __mul__(self, multiple: int) -> 'Point':
        """
        实现标量乘法 (点乘)，使用二进制加法方法进行优化，逐位处理点乘。
        :param multiple: 标量，整数类型
        :return: 返回标量乘法的结果。如果标量为零或涉及无穷远点，则返回无穷远点
        """
        if multiple == 0 or self == INFINITY:
            return INFINITY
        if self.__order and multiple % self.__order == 0:
            return INFINITY
        if multiple < 0:
            return -self * -multiple

        result = INFINITY   # 无穷远点
        temp = self         # 临时点

        while multiple:
            if multiple & 1:           # 如果当前二进制位为1，累加结果
                result += temp
            temp += temp            # 点加自己（相当于倍点）
            multiple >>= 1          # 移动到下一个二进制位

        return result

    def __rmul__(self, multiple: int) -> 'Point':
        """
        支持右乘 (multiple * self)
        :param multiple: 标量，整数类型
        :return: 返回标量乘法的结果
        """
        return self * multiple

    def x(self):
        """返回点的 x 坐标"""
        return self.__x

    def y(self):
        """返回点的 y 坐标"""
        return self.__y

    def curve(self):
        """返回点所在的曲线"""
        return self.__curve

    def order(self):
        """返回点的阶"""
        return self.__order


class Util:
    """
    椭圆曲线工具类
    """
    @staticmethod
    def point_to_tuple(point: 'Point') -> tuple:
        """
        将点对象转换为元组 (x, y)。根据传入的参数，可以选择以十六进制或整数的形式返回点的坐标。
        :param point: 要转换的 EllipticPoint 对象
        :return: 点的坐标元组。若为无穷远点，返回 (None, None)
        """
        if point == INFINITY:
            return None, None
        else:
            return point.x(), point.y()

    @staticmethod
    def tuple_to_point(curve: 'Curve', tup: tuple) -> 'Point':
        """
        将元组 (x, y) 转换为点对象，如果是 (None, None)，则返回无穷远点
        :param tup: (x, y) 坐标元组
        :param curve: 椭圆曲线对象
        :return: EllipticPoint 对象，或无穷远点
        """
        # 确认点是否在曲线上
        x, y = tup
        if curve and (x is not None or y is not None):
            assert curve.contains_point(x, y)

        # 如果是 (None, None)，表示无穷远点
        if tup == (None, None):
            return INFINITY

        return Point(curve, x, y)

    @classmethod
    def jacobi(cls, a: int, n: int) -> int:
        """
        计算 Jacobi 符号 (a/n)
        :param a: 整数 a，表示分子
        :param n: 整数 n，必须是正奇数，表示分母
        :return: 返回 Jacobi 符号的值（1、-1 或 0）
        """
        # 确保 n 是正奇数
        assert n > 0 and n % 2 == 1, 'The second input integer should be POSITIVE and ODD'

        a %= n  # 将 a 归约到 n 的范围内
        t = 1  # 初始化结果符号
        while a:
            # 处理 a 为偶数的情况
            while a % 2 == 0:
                a //= 2
                if n % 8 in [3, 5]:  # 根据 n mod 8 决定符号翻转
                    t = -t
            # 互反律：交换 a 和 n，同时根据条件调整符号
            if a % 4 == 3 and n % 4 == 3:
                t = -t
            a, n = n % a, a  # 交换并取模
        return t if n == 1 else 0  # 如果 n 归约到 1，则返回符号 t，否则返回 0

    @classmethod
    def Legendre(cls, n: int, p: int) -> int:
        """
        计算勒让德符号 (n/p)，用于判断 n 是否为模 p 的二次剩余。
        :param n: 待判断的数
        :param p: 奇素数模数
        :return: 返回值含义：
                1  表示 n 是模 p 的二次剩余
                -1 表示 n 是模 p 的二次非剩余
                0  表示 n 能被 p 整除
        """
        return pow(n, (p - 1) // 2, p)

    @staticmethod
    def Tonelli_Shanks(n: int, p: int) -> int:
        """
        Tonelli-Shanks 算法求解模平方根 y^2 ≡ n mod p
        :param n: 要求解平方根的整数
        :param p: 素数模数
        :return: 满足 y^2 ≡ n mod p 的整数 y，若不存在则抛出 ValueError
        """
        # 处理简单情况
        if n == 0:
            return 0
        if p == 2:
            return n  # 只有 p=2 时，0和1的平方根分别是0和1

        # 欧拉准则判断是否为二次剩余
        if Util.Legendre(n, p) != 1:
            # logger.error(f"{n} Quadratic residue that is not modulo {p}")
            return -1

        # p ≡ 3 mod4 时使用快速算法
        if p % 4 == 3:
            y = pow(n, (p + 1) // 4, p)
            return y

        # 分解 p-1 为 Q * 2^S
        Q = p - 1
        S = 0
        while Q % 2 == 0:
            Q //= 2
            S += 1

        # 寻找二次非剩余 z
        z = 2
        while Util.Legendre(z, p) != p - 1:
            z += 1

        # 初始化变量
        c = pow(z, Q, p)
        t = pow(n, Q, p)
        R = pow(n, (Q + 1) // 2, p)
        M = S

        # 主循环
        while t != 1:
            # 寻找最小的 i 使得 t^{2^i} ≡1 mod p
            i, temp = 0, t
            while temp != 1 and i < M:
                temp = pow(temp, 2, p)
                i += 1

            if i == M:
                logger.error("Cannot find square root")
                return -1

            # 更新参数
            b = pow(c, 1 << (M - i - 1), p)
            M = i
            c = pow(b, 2, p)
            t = (t * c) % p
            R = (R * b) % p

        return R

    @staticmethod
    def calc_y_coord(curve: 'Curve', x: int):
        """
        根据给定的 x 坐标计算椭圆曲线上点的 y 坐标
        :param curve: 椭圆曲线
        :param x: 给定的 x 坐标
        :return: 两个 y 坐标值（如果存在），或者 None
        https://oi-wiki.org/math/number-theory/quad-residue/
        """
        p = curve.p()
        a = curve.a()
        b = curve.b()
        # 计算 y^2 的值
        y_squared = (x ** 3 + a * x + b) % p

        y = Util.Tonelli_Shanks(y_squared, p)
        if y > 0:
            # 另一个 y 坐标是当前 y 坐标的相反数
            return y, p - y
        else:
            return None


# 定义无穷远点
INFINITY = Point(None, None, None)
