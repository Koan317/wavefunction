# math_radial.py
"""
氢原子径向波函数 R_{n l}(r)
"""
import numpy as np
import math
from config import MAX_N, R_MAX, R_POINTS

# 预计算 Laguerre 用的全局表
_LAGUERRE_RHO_GRID = None
_LAGUERRE_CACHE = {}      # key: (n, l) -> L_{n-l-1}^{2l+1}(rho_grid)
_LAGUERRE_READY = False

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

    global _LAGUERRE_RHO_GRID, _LAGUERRE_CACHE, _LAGUERRE_READY

    # 如果预计算表已经就绪，优先用插值
    if _LAGUERRE_READY and (n, l) in _LAGUERRE_CACHE:
        L_full = _LAGUERRE_CACHE[(n, l)]
        L = np.interp(rho, _LAGUERRE_RHO_GRID, L_full)
    else:
        # 还没准备好，就临时算一遍（只会在启动早期用到）
        L = assoc_laguerre(k, alpha, rho)

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

def laguerre_precompute_worker(queue, max_n: int = MAX_N, rho_points: int = 2000):
    """
    在子进程中预计算所有 (n,l) 的 Laguerre 多项式表，
    计算完后通过 queue 把 (rho_grid, cache) 传回主进程。
    """
    import numpy as _np

    Z = 1.0
    rho_max = 2.0 * Z * R_MAX  # r ∈ [0, R_MAX] 时，n>=1 对应的 rho 最大值

    rho_grid = _np.linspace(0.0, rho_max, rho_points)
    cache = {}

    for n in range(1, max_n + 1):
        for l in range(0, n):
            k = n - l - 1
            alpha = 2*l + 1
            L = assoc_laguerre(k, alpha, rho_grid)
            cache[(n, l)] = L.astype(float)

    # 通过队列返回
    queue.put((rho_grid, cache))

def apply_laguerre_table(rho_grid, cache):
    """
    在主进程中调用：接收子进程算好的 Laguerre 表，填充到全局缓存。
    """
    global _LAGUERRE_RHO_GRID, _LAGUERRE_CACHE, _LAGUERRE_READY

    _LAGUERRE_RHO_GRID = np.asarray(rho_grid, dtype=float)
    _LAGUERRE_CACHE = {tuple(k): np.asarray(v, dtype=float) for k, v in cache.items()}
    _LAGUERRE_READY = True
