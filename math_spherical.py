# math_spherical.py
"""
球谐函数 Y_{l}^{m}(theta, phi)
使用 scipy.special.sph_harm，约定：
theta: 极角 [0, pi] （colatitude）
phi: 方位角 [0, 2*pi]
"""

import numpy as np
from scipy.special import sph_harm
from config import THETA_POINTS, PHI_POINTS

def spherical_grid():
    """
    生成 (theta, phi) 网格。
    返回:
        theta, phi: 形状 (n_theta, n_phi)
    """
    theta = np.linspace(0.0, np.pi, THETA_POINTS)
    phi = np.linspace(0.0, 2.0 * np.pi, PHI_POINTS)
    theta_grid, phi_grid = np.meshgrid(theta, phi, indexing="ij")
    return theta_grid, phi_grid

def spherical_harmonic(l: int, m: int, theta: np.ndarray, phi: np.ndarray):
    """
    计算 Y_l^m(theta, phi)，返回 complex ndarray
    scipy 的 sph_harm(m, l, phi, theta) 参数顺序是 (m, l, phi, theta)
    """
    return sph_harm(m, l, phi, theta)

def spherical_harmonic_real(l: int, m: int, theta: np.ndarray, phi: np.ndarray):
    """
    返回 Re[Y_l^m]
    """
    return spherical_harmonic(l, m, theta, phi).real

def spherical_harmonic_imag(l: int, m: int, theta: np.ndarray, phi: np.ndarray):
    """
    返回 Im[Y_l^m]
    """
    return spherical_harmonic(l, m, theta, phi).imag

def has_nonzero_imag_part(l: int, m: int, atol: float = 1e-8):
    """
    粗略判断 Y_l^m 是否有非零虚部。
    用少量采样点判断，避免整网格计算。
    """
    theta_samples = np.linspace(0.1, np.pi - 0.1, 5)
    phi_samples = np.linspace(0.0, 2.0 * np.pi, 5)
    for theta in theta_samples:
        for phi in phi_samples:
            val = spherical_harmonic(l, m, theta, phi)
            if abs(val.imag) > atol:
                return True
    return False
