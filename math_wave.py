# math_wave.py
"""
组合波函数 ψ(r,θ,φ) = R(r)·Y(θ,φ)
"""

import numpy as np
from math_radial import radial_wavefunction
from math_spherical import spherical_harmonic_real, spherical_harmonic_imag

def psi_real(n, l, m, r, theta, phi):
    """ψ 的实部 = R * Re(Y)"""
    R = radial_wavefunction(n, l, r)
    Y = spherical_harmonic_real(l, m, theta, phi)
    return R * Y

def psi_imag(n, l, m, r, theta, phi):
    """ψ 的虚部 = R * Im(Y)"""
    R = radial_wavefunction(n, l, r)
    Y = spherical_harmonic_imag(l, m, theta, phi)
    return R * Y

def psi_prob(n, l, m, r, theta, phi):
    """
    概率密度 |ψ|^2 = |R|^2 * |Y|^2
    """
    R = radial_wavefunction(n, l, r)
    Yr = spherical_harmonic_real(l, m, theta, phi)
    Yi = spherical_harmonic_imag(l, m, theta, phi)
    return (R * R) * (Yr * Yr + Yi * Yi)
