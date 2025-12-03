# math_radial.py
"""
氢原子径向波函数 R_{n l}(r)
"""
import numpy as np
import math
from config import MAX_N, R_MAX, R_POINTS

def available_n_values(max_n: int = MAX_N):
    return list(range(1, max_n + 1))

def available_l_values(n: int):
    return list(range(0, n))

def available_m_values(l: int):
    return list(range(-l, l + 1))

def radial_grid():
    return np.linspace(0.0, R_MAX, R_POINTS)

# -------------------------------------------------------------------
# 数值稳定版关联 Laguerre 多项式，通过递推构造
# -------------------------------------------------------------------
def assoc_laguerre(k, alpha, x):
    """
    计算 L_k^α(x)，采用稳定三项递推：
    L_0^α = 1
    L_1^α = -x + α + 1
    L_{n}^α = ((2n - 1 + α - x) * L_{n-1}^α - (n-1 + α) * L_{n-2}^α ) / n
    """

    if k == 0:
        return np.ones_like(x)
    if k == 1:
        return -x + alpha + 1

    L_prev = np.ones_like(x)   # L_0
    L_curr = -x + alpha + 1    # L_1

    for n in range(2, k + 1):
        L_next = ((2*n - 1 + alpha - x) * L_curr - (n - 1 + alpha) * L_prev) / n
        L_prev, L_curr = L_curr, L_next

    return L_curr
# ==========================
# 惰性加载 Laguerre 缓存系统
# ==========================
class LaguerreTable:
    """
    惰性加载 + 缓存：
    需要某个 (k, alpha) 的 Laguerre 时才计算一次并缓存。
    后续所有 radial_wavefunction 不再重新算。
    """
    def __init__(self, rho_max=80.0, rho_points=2000):
        self.rho_grid = np.linspace(0.0, rho_max, rho_points)
        self.cache = {}  # (k, alpha) -> array of shape (rho_points,)

    def get(self, k, alpha):
        """
        返回 L_k^alpha(rho_grid)
        如果第一次访问，自动计算并缓存。
        """
        key = (k, alpha)
        if key not in self.cache:
            # 只计算一次
            L = assoc_laguerre(k, alpha, self.rho_grid)
            self.cache[key] = L.astype(float)
        return self.cache[key]
# 单例
laguerre_table = LaguerreTable()

# -------------------------------------------------------------------
# 数值稳定的完整 R_{n l}(r)
# -------------------------------------------------------------------
def radial_wavefunction(n: int, l: int, r: np.ndarray, Z: float = 1.0):
    if n < 1:
        raise ValueError("n 必须 >= 1")
    if not (0 <= l <= n - 1):
        raise ValueError("l 必须满足 0 <= l <= n-1")

    # 转成数组
    r = np.asarray(r, dtype=float)

    # 物理上 r 只能 >= 0：负半轴直接裁到 0，避免 rho < 0 导致 exp 溢出
    r_phys = np.clip(r, 0.0, None)

    # a0 目前没用，但保留原意
    a0 = 1.0
    rho = 2.0 * Z * r_phys / n

    # 关联 Laguerre：L_{n-l-1}^{2l+1}(rho)
    k = n - l - 1
    alpha = 2*l + 1

    L_full = laguerre_table.get(k, alpha)
    L = np.interp(rho, laguerre_table.rho_grid, L_full)


    # 归一化因子（解析式）
    num = math.factorial(n - l - 1)
    den = 2*n*math.factorial(n + l)
    norm = (2*Z/n) * math.sqrt(num / den)

    # 数值安全区：关掉 exp / 乘法的溢出告警，把非有限值置 0
    with np.errstate(over="ignore", invalid="ignore"):
        R = norm * np.exp(-rho/2) * (rho**l) * L

    # 把 inf / nan 清掉，防止弄坏坐标轴范围
    R = np.where(np.isfinite(R), R, 0.0)
    return R


def radial_with_grid(n: int, l: int):
    r = radial_grid()
    return r, radial_wavefunction(n, l, r)
