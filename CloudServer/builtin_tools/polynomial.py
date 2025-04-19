# -*- coding: utf-8 -*-
# @Time    : 2024/11/19 21:47
# @Author  : DSTBP
# @File    : arithmetic.py
# @Description : 多项式类
from builtin_tools import arithmetic


class Polynomial:
    """
    多项式类: 用于支持多项式的加法、减法、乘法、幂运算、模运算等操作。
    """
    def __init__(self, coef=None, modulo: int=0):
        """
        初始化多项式对象。
        :param coef: 字典形式的多项式系数，例如 {2: 3, 0: -1} 表示 3X^2 - 1。也可以直接传入一个整数表示常数多项式。
        :param modulo: 模数，若为非零，则所有系数计算时会取模。
        """
        if coef is None:
            coef = {1: 1}
        if isinstance(coef, int):   # 如果系数是整数，则表示常数多项式
            self.coef = {0: coef} if coef else {}
        else:                       # 系数字典
            self.coef = coef
        self.degree = max(self.coef) if self.coef else -1   # 多项式的最高次幂
        self.modulo = modulo                                # 模数

    def __call__(self, x: int):
        """
        计算多项式在 x 点的值。
        :param x: 需要计算的点。
        :return: 多项式在 x 点的值，取模后返回。
        """
        if self.modulo:
            return sum((v * x**k) % self.modulo for k, v in self.coef.items()) % self.modulo
        else:
            return sum(v * (x ** k) for k, v in self.coef.items())

    def __add__(self, other):
        """
        实现多项式与整数或另一个多项式的加法。
        """
        if isinstance(other, int):  # 如果是整数
            res = self.coef.copy()
            res[0] = res.get(0, 0) + other                                          # 更新常数项
        elif isinstance(other, Polynomial):                                         # 如果是另一个多项式
            assert self.modulo == other.modulo, 'Modulo numbers are different.'     # 确保模数一致
            res = self.coef.copy()
            for k, v in other.coef.items():                                         # 将两个多项式的系数相加
                res[k] = res.get(k, 0) + v
        else:
            raise TypeError('Operated instances must be Integer or Polynomial.')    # 只支持与整数或多项式相加

        p = Polynomial(res, self.modulo)
        p.simplify()  # 化简结果
        return p

    def __radd__(self, a: int):
        """
        右加法，支持整数 + 多项式
        :param a: 加法整数
        :return: 返回加法后的多项式
        """
        return self + a

    def __neg__(self):
        """
        实现多项式的取反操作，即所有系数乘以 -1。
        """
        res = self.coef.copy()
        for k in res:
            res[k] = -res[k]
        return Polynomial(res, self.modulo)

    def __sub__(self, other):
        """
        实现多项式的减法。
        """
        return self + (-other)

    def __rsub__(self, other):
        """
        实现整数减去多项式。
        """
        return -self + other

    def __mul__(self, other):
        """
        实现多项式与整数或另一个多项式的乘法。
        """
        if isinstance(other, int):                                                  # 如果乘数是整数
            res = {k: v * other for k, v in self.coef.items()}                      # 使用字典推导式
        elif isinstance(other, Polynomial):                                         # 如果乘数是多项式
            assert self.modulo == other.modulo, 'Modulo numbers are different.'     # 确保模数一致
            res = {}                                # 累加同幂次项
            for k1, v1 in self.coef.items():
                for k2, v2 in other.coef.items():
                    key = k1 + k2                   # 计算幂次
                    if key in res:                  # 如果幂次已存在，累加
                        res[key] += v1 * v2
                    else:                           # 否则，初始化
                        res[key] = v1 * v2
        else:
            raise TypeError('Operated instances must be Integer or Polynomial.')  # 不支持其他类型

        p = Polynomial(res, self.modulo)
        p.simplify()  # 化简结果
        return p

    def __rmul__(self, a: int):
        """
        右乘法，支持整数 * 多项式
        :param a: 乘法整数
        :return: 返回乘法结果
        """
        return self * a

    def __pow__(self, n: int):
        """
        实现多项式的幂运算（快速幂算法）。
        """
        res = Polynomial(1, self.modulo)  # 初始值为常数 1
        p = self.copy()
        while n:        # 当 n 不为 0 时循环
            if n & 1:   # 如果当前幂次是奇数
                res *= p
            n >>= 1     # 幂次减半
            p *= p      # 底数平方
        return res

    def __mod__(self, other):
        """
        实现多项式对另一个多项式的模运算。
        """
        assert self.modulo == other.modulo, 'Modulo numbers are different.'
        assert other.coef, 'Modulo polynomial cannot be ZERO.'
        # 被除多项式为零直接返回
        if not self.coef:
            return self

        res = self.copy()
        while res.degree >= other.degree:
            # 计算当前最高阶系数的最大公约数 (gcd)，以及贝祖系数
            gcd, _, r2 = arithmetic.exgcd(res.coef[res.degree], other.coef[other.degree])
            # 计算缩放因子（用于消去当前最高阶的系数）
            factor = (res.coef[res.degree] // gcd) * (arithmetic.exgcd(other.coef[other.degree] // gcd, self.modulo)[1])
            # 用缩放后的除数多项式消去当前最高阶项
            res -= other * factor * Polynomial({res.degree - other.degree: 1}, modulo=self.modulo)
        return res

    def __str__(self):
        """
        将多项式转换为可读的字符串形式，例如 "4*X^3 - 2*X^2 + X - 7 % 23"。
        """
        if not self.coef:
            return '0'

        terms = []
        for k in sorted(self.coef, reverse=True):  # 按幂次从高到低排序
            c = self.coef[k]
            if not c:
                continue

            # 处理符号
            sign = ' + ' if c > 0 else ' - '
            abs_c = abs(c)

            # 处理系数
            coeff_part = str(abs_c) if abs_c != 1 or k == 0 else ''

            # 处理变量部分
            var_part = 'x' if k > 0 else ''
            pow_part = f'^{k}' if k > 1 else ''

            # 拼接每一项
            term = f"{sign}{coeff_part}{'*' if coeff_part and var_part else ''}{var_part}{pow_part}"
            terms.append(term)

        # 添加模数
        res = ''.join(terms).lstrip(' +')   # 拼接所有项并去掉首部多余的符号
        if self.modulo:
            res += f' (mod {self.modulo})'
        return res

    def simplify(self):
        """
        对多项式进行化简：移除系数为 0 的项，并对系数取模。
        """
        if self.modulo:
            self.coef = {
                k: v % self.modulo
                for k, v in self.coef.items()
                if v % self.modulo  # 仅保留系数不为 0 的项
            }
        else:
            self.coef = {k: v for k, v in self.coef.items() if v}  # 仅移除系数为 0 的项
        self.degree = max(self.coef, default=-1)  # 更新最高次幂

    def copy(self) -> 'Polynomial':
        """
        返回多项式的一个深拷贝。
        """
        return Polynomial(self.coef.copy(), self.modulo)

    @classmethod
    def poly_pow_mod(cls, p1: 'Polynomial', n: int, p2: 'Polynomial'):
        """
        计算 (p1(x)^n) mod p2(x)，即多项式的模数幂。
        :param p1: 多项式 p1，底数
        :param n: 指数 n，非负整数
        :param p2: 多项式 p2，模多项式，不能为零
        :return: 计算结果，多项式 res
        """
        # 检查模数是否一致，以及模多项式是否有效
        assert p1.modulo == p2.modulo, 'Modulo numbers are different.'
        assert p2.coef, 'Modulo polynomial cannot be ZERO.'

        res = Polynomial(1, p1.modulo)  # 初始化结果为常数 1
        p1 %= p2  # 先将 p1 对 p2 取模

        if isinstance(p1, dict):
            return p1

        # 多项式快速幂算法计算 (p1^n) % p2
        while n > 0:
            if n % 2 == 1:  # 如果 n 是奇数，累乘到结果上
                res = (res * p1) % p2
            n //= 2  # 指数折半
            if n > 0:
                p1 = (p1 * p1) % p2  # 底数平方取模
        return res

    @classmethod
    def gcd_poly(cls, p1: 'Polynomial', p2: 'Polynomial') -> 'Polynomial':
        """
        使用辗转相除法计算两个多项式的最大公因式。
        :param p1: 多项式 p1
        :param p2: 多项式 p2
        :return: p1 和 p2 的最大公因式
        """
        if not (p1.coef and p2.coef): return p1 + p2
        p1, p2 = p2, p1 % p2
        while p2.coef: p1, p2 = p2, p1 % p2
        return p1

    @classmethod
    def lagrange_poly_coeffs(cls, point_list: list, p: int) -> dict[int, int]:
        """
        使用拉格朗日插值法计算多项式的所有系数
        :param point_list: 已知点的坐标列表
        :param p: 模数
        :return: 多项式对象
        """
        x_s = [point[0] for point in point_list]
        y_s = [point[1] for point in point_list]
        k = len(x_s)
        assert k == len(set(x_s)), "points must be distinct"  # 确保点是唯一的

        final_poly = Polynomial(0, p)  # 初始化最终多项式为零多项式

        for i in range(k):
            # 计算拉格朗日基函数的分子多项式
            numerator_poly = Polynomial(1, p)
            for j in range(k):
                if j != i:
                    # 构建 (x - x_j) 多项式
                    poly = Polynomial({0: -x_s[j], 1: 1}, p)
                    numerator_poly *= poly

            # 计算拉格朗日基函数的分母
            denominator = 1
            for j in range(k):
                if j != i:
                    denominator *= (x_s[i] - x_s[j])

            # 计算拉格朗日基函数的分母的逆元
            denominator_inv = pow(denominator, -1, p)

            # 计算拉格朗日基函数
            lagrange_basis = numerator_poly * denominator_inv

            # 乘以对应的 y 值
            weighted_lagrange_basis = lagrange_basis * y_s[i]

            # 累加拉格朗日基函数
            final_poly += weighted_lagrange_basis

        return final_poly.coef