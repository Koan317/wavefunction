# plot_wave3d.py
"""
严格物理版点云电子云可视化（红–透明–蓝版本）
- 点位置严格按 |ψ|² r² sinθ 抽样（概率密度）
- 实部 / 虚部：正红，负蓝，透明度按振幅逐渐过渡（节点自动透明）
- |ψ|²：纯白色点云
- 自动径向分壳（基于径向概率最大值）
"""

import numpy as np
import pyvista as pv

from math_wave_sample import HydrogenSampler
from math_wave import psi_real, psi_imag, psi_prob
from math_radial import radial_wavefunction, radial_with_grid

class Wave3DPlotter:
    def __init__(self, plotter: pv.Plotter):
        self.plotter = plotter

    # ---------------------------------------------------------
    # 自动分壳：使用径向概率分布 r^2 |R|^2
    # ---------------------------------------------------------
    def _radial_shell_peaks(self, n, l):
        r, R = radial_with_grid(n, l)
        P = (r * r) * (R * R)

        # 查找粗略峰值位置
        peaks = []
        for i in range(1, len(P) - 1):
            if P[i] > P[i - 1] and P[i] > P[i + 1]:
                peaks.append(r[i])

        if len(peaks) == 0:
            peaks = [r[np.argmax(P)]]

        return np.array(peaks)

    # ---------------------------------------------------------
    # 主绘图函数
    # ---------------------------------------------------------
    def plot(self, n, l, m, mode="psi_real", N=200000):
        self.plotter.clear()

        # ------- 连续抽样 -------
        sampler = HydrogenSampler(n, l, m, N)
        r, th, ph, x, y, z = sampler.sample(N)
        pts = np.column_stack((x, y, z))

        # ------- 计算波函数值 -------
        if mode == "psi_real":
            values = psi_real(n, l, m, r, th, ph)
            title = "Re(ψ)"
            signed_mode = True

        elif mode == "psi_imag":
            values = psi_imag(n, l, m, r, th, ph)
            title = "Im(ψ)"
            signed_mode = True

        elif mode == "psi_prob":
            values = psi_prob(n, l, m, r, th, ph)
            title = "|ψ|²"
            signed_mode = False

        else:
            raise ValueError(f"unknown mode: {mode}")

        values = np.asarray(values, float)

        # 若模式下理论上全为 0（如 m=0 的虚部）
        if np.allclose(values, 0, atol=1e-14):
            self.plotter.add_axes()
            self.plotter.add_text(f"{title} = 0", font_size=14)
            self.plotter.reset_camera()
            self.plotter.render()
            return

        # -----------------------------------------------------
        # 壳分层：根据 r 对抽样点按壳分类
        # -----------------------------------------------------
        r_peaks = self._radial_shell_peaks(n, l)
        n_shells = len(r_peaks)

        # 若只有一个壳，则所有点都归一组
        if n_shells == 1:
            shell_index = np.zeros(len(r), dtype=int)
        else:
            shell_index = np.zeros(len(r), dtype=int)
            """for i in range(len(r)):
                shell_index[i] = int(np.argmin(np.abs(r_peaks - r[i])))"""
            shell_index = np.argmin(np.abs(r[:,None] - r_peaks[None,:]), axis=1)

        # -----------------------------------------------------
        # 绘制每一壳
        # -----------------------------------------------------
        for k in range(n_shells):
            mask = (shell_index == k)
            if not np.any(mask):
                continue

            p = pts[mask]
            v = values[mask]

            if signed_mode:
                # ======== 红–透明–蓝 ========
                absv = np.abs(v)
                vmax = float(absv.max()) if absv.size > 0 else 1e-12

                # 透明度：|ψ| / max(|ψ|)
                alpha = (absv / vmax).clip(0.0, 1.0)

                # RGBA 数组
                colors = np.zeros((p.shape[0], 4))

                # 正值 → 红
                pos = v > 0
                colors[pos, 0] = 1.0
                colors[pos, 1] = 0.2
                colors[pos, 2] = 0.2
                colors[pos, 3] = alpha[pos]

                # 负值 → 蓝
                neg = v < 0
                colors[neg, 0] = 0.2
                colors[neg, 1] = 0.4
                colors[neg, 2] = 1.0
                colors[neg, 3] = alpha[neg]

                # 节点区（v=0）自动保持 alpha=0（完全透明）
                self.plotter.add_points(
                    p,
                    scalars=colors,
                    rgba=True,
                    render_points_as_spheres=True,
                    point_size=3,
                )
            else:
                # ======== |ψ|² 模式：白色 ========
                white = np.ones((p.shape[0], 3))
                self.plotter.add_points(
                    p,
                    scalars=white,
                    rgb=True,
                    render_points_as_spheres=True,
                    point_size=3,
                    opacity=0.9,
                )

        # -----------------------------------------------------
        # 坐标轴 + 文本
        # -----------------------------------------------------
        self.plotter.add_text(
            f"{title}  (n={n}, l={l}, m={m}, N={N})",
            font_size=16,
        )
        self.plotter.add_axes()
        self.plotter.reset_camera()
        self.plotter.render()
