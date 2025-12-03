# math_wave_sample.py
"""
严格物理连续采样（按 |ψ|² r² sinθ），
但径向范围根据 R_{nl}(r) 自动裁剪到“最后一层壳附近”，
避免把一大段几乎没有结构的 tail 也纳入归一化，导致外层壳被稀释得看不见。
"""

import numpy as np
from math_radial import radial_wavefunction
from math_spherical import spherical_harmonic_real, spherical_harmonic_imag

class HydrogenSampler:
    def __init__(self, n, l, m, N=80000):
        self.n = n
        self.l = l
        self.m = m
        self.N = N

        # 先给一个理论上的最大范围，后面会自动裁剪
        self.rmax_theory = 8.0 * n * n

        self._prepare_radial()
        self._prepare_angular()

    # ---------------------------------------------------------
    # 1) 径向：自动找到“最后一层壳”的位置，再在那之前做严格物理采样
    # ---------------------------------------------------------
    def _prepare_radial(self):
        # 单次高分辨率扫描，同时用于峰值定位与最终抽样
        r_full = np.linspace(0.0, self.rmax_theory, 30000)
        R_full = radial_wavefunction(self.n, self.l, r_full)
        P_full = (r_full**2) * (R_full**2)

        # 找所有局部峰值（壳中心）
        peaks_mask = (P_full[1:-1] > P_full[:-2]) & (P_full[1:-1] > P_full[2:])
        peak_indices = np.where(peaks_mask)[0] + 1  # 对应 r_full 的索引

        if len(peak_indices) == 0:
            # 极少数异常，兜底直接用理论 rmax
            r_cut = self.rmax_theory
        else:
            # 最后一个“真正的壳峰”
            last_peak_idx = peak_indices[-1]
            last_peak_r = r_full[last_peak_idx]

            # 在最后一层壳外面再留一点余量（防止裁太死）
            r_cut = min(self.rmax_theory, last_peak_r * 1.4)

        self.rmax = float(r_cut)

        # 现在在 [0, rmax] 内直接用已计算的高分辨率网格，严格按 r^2|R|^2 做 PDF
        r_mask = r_full <= self.rmax
        r_grid = r_full[r_mask]
        pdf = P_full[r_mask]
        pdf = np.maximum(pdf, 0.0)
        s = pdf.sum()
        if s <= 0:
            pdf[:] = 1.0
            s = pdf.sum()
        pdf /= s

        cdf = np.cumsum(pdf)
        cdf /= cdf[-1]

        self._r_grid = r_grid
        self._r_cdf = cdf

    def _sample_r(self, N=None):
        if N is None:
            N = self.N
        u = np.random.rand(N)
        r = np.interp(u, self._r_cdf, self._r_grid)
        return r

    # ---------------------------------------------------------
    # 2) 角分布：p(θ, φ) ∝ |Y|^2 sinθ
    # ---------------------------------------------------------
    def _prepare_angular(self):
        Nth = int(60 + 20 * (self.l + 1))
        Nph = int(120 + 40 * (self.l + 1))

        th_edges = np.linspace(0.0, np.pi, Nth + 1)
        ph_edges = np.linspace(0.0, 2*np.pi, Nph + 1)

        th_centers = 0.5 * (th_edges[:-1] + th_edges[1:])
        ph_centers = 0.5 * (ph_edges[:-1] + ph_edges[1:])

        TH, PH = np.meshgrid(th_centers, ph_centers, indexing="ij")

        Yr = spherical_harmonic_real(self.l, self.m, TH, PH)
        Yi = spherical_harmonic_imag(self.l, self.m, TH, PH)
        Y2 = Yr*Yr + Yi*Yi

        pdf = Y2 * np.sin(TH)
        pdf = np.maximum(pdf, 0.0)
        pdf_flat = pdf.ravel()
        s = pdf_flat.sum()
        if s <= 0:
            pdf_flat[:] = 1.0
            s = pdf_flat.sum()
        pdf_flat /= s

        cdf = np.cumsum(pdf_flat)
        cdf /= cdf[-1]

        self._Nth = Nth
        self._Nph = Nph
        self._th_edges = th_edges
        self._ph_edges = ph_edges
        self._th_centers = th_centers
        self._ph_centers = ph_centers
        self._ang_cdf = cdf

    def _sample_theta_phi(self, N=None):
        if N is None:
            N = self.N

        Nth, Nph = self._Nth, self._Nph
        th_edges = self._th_edges
        ph_edges = self._ph_edges
        th_centers = self._th_centers
        ph_centers = self._ph_centers
        cdf = self._ang_cdf

        u = np.random.rand(N)
        idx = np.searchsorted(cdf, u, side="right")
        idx = np.clip(idx, 0, len(cdf) - 1)

        idx_th = idx // Nph
        idx_ph = idx % Nph

        th0 = th_centers[idx_th]
        ph0 = ph_centers[idx_ph]

        dth = th_edges[1] - th_edges[0]
        dph = ph_edges[1] - ph_edges[0]

        th = th0 + (np.random.rand(N) - 0.5) * dth
        ph = ph0 + (np.random.rand(N) - 0.5) * dph

        th = np.clip(th, 0.0, np.pi)
        ph = np.mod(ph, 2*np.pi)

        return th, ph

    # ---------------------------------------------------------
    # 3) 对外接口：返回 (r, θ, φ, x, y, z)
    # ---------------------------------------------------------
    def sample(self, N=None):
        if N is None:
            N = self.N

        r = self._sample_r(N)
        th, ph = self._sample_theta_phi(N)

        sin_th = np.sin(th)
        x = r * sin_th * np.cos(ph)
        y = r * sin_th * np.sin(ph)
        z = r * np.cos(th)

        return r, th, ph, x, y, z
