# plot_spherical.py
"""
球谐函数双视图：
- 左：球面着色图（Surface plot）
- 右：径向变形“等值面形状”（Shape plot）
- m = 0 且 component = "imag" 时：两边不绘制几何，只显示类型 + (Im = 0)
"""

import numpy as np
import pyvista as pv
from math_spherical import spherical_harmonic_real, spherical_harmonic_imag

class SphericalDualPlotter:
    def __init__(self, pv_left: pv.Plotter, pv_right: pv.Plotter):
        self.pv_left = pv_left
        self.pv_right = pv_right
        self.pv_right.camera = self.pv_left.camera

    # -----------------------------------------------------
    # 公用单位球网格
    # -----------------------------------------------------
    def _sphere_grid(self, nt: int = 200, np_: int = 200):
        theta = np.linspace(0.0, np.pi, nt)
        phi = np.linspace(0.0, 2.0 * np.pi, np_)
        TH, PH = np.meshgrid(theta, phi, indexing="ij")

        X = np.sin(TH) * np.cos(PH)
        Y = np.sin(TH) * np.sin(PH)
        Z = np.cos(TH)
        return TH, PH, X, Y, Z

    # -----------------------------------------------------
    # 左图：球面图（Surface plot）
    # -----------------------------------------------------
    def _plot_left(self, l: int, m: int, component: str):
        self.pv_left.clear()

        # 虚部且 m = 0 → 不画，只写类型
        if component == "imag" and m == 0:
            self.pv_left.add_text(
                "Surface plot (Im = 0)",
                position="upper_left",
                font_size=14,
            )
            self.pv_left.add_axes()
            self.pv_left.reset_camera()
            self.pv_left.render()
            return

        TH, PH, X, Y, Z = self._sphere_grid()

        # 计算球谐
        if component == "real":
            vals = spherical_harmonic_real(l, m, TH, PH)
        else:
            vals = spherical_harmonic_imag(l, m, TH, PH)

        vals = np.asarray(vals, float)

        grid = pv.StructuredGrid(X, Y, Z)
        grid["Ylm"] = vals.ravel(order="F")

        # 球面着色
        self.pv_left.add_mesh(
            grid,
            scalars="Ylm",
            cmap="coolwarm",
            show_scalar_bar=True,
            show_edges=False,
        )

        # 标明图类型
        self.pv_left.add_text(
            "Surface plot",
            position="upper_left",
            font_size=14,
        )

        self.pv_left.add_axes()
        self.pv_left.reset_camera()
        self.pv_left.render()

    # -----------------------------------------------------
    # 右图：等值面形状（径向变形）Shape plot
    # -----------------------------------------------------
    def _plot_right(self, l: int, m: int, component: str):
        self.pv_right.clear()

        # 虚部且 m = 0 → 不画，只写类型
        if component == "imag" and m == 0:
            self.pv_right.add_text(
                "Shape plot (Im = 0)",
                position="upper_left",
                font_size=14,
            )
            self.pv_right.add_axes()
            self.pv_right.reset_camera()
            self.pv_right.render()
            return

        TH, PH, X0, Y0, Z0 = self._sphere_grid()

        # 计算球谐
        if component == "real":
            vals = spherical_harmonic_real(l, m, TH, PH)
        else:
            vals = spherical_harmonic_imag(l, m, TH, PH)

        vals = np.asarray(vals, float)
        vals = vals - vals.mean()

        # 控制形变强度，避免过分“鼓”
        k = 0.3
        R = 1 + k * vals

        X = R * np.sin(TH) * np.cos(PH)
        Y = R * np.sin(TH) * np.sin(PH)
        Z = R * np.cos(TH)

        grid = pv.StructuredGrid(X, Y, Z)
        grid["Ylm"] = vals.ravel(order="F")

        self.pv_right.add_mesh(
            grid,
            scalars="Ylm",
            cmap="coolwarm",
            show_scalar_bar=True,
            show_edges=False,
        )

        # 标明图类型
        self.pv_right.add_text(
            "Shape plot",
            position="upper_left",
            font_size=14,
        )

        self.pv_right.add_axes()
        self.pv_right.reset_camera()
        self.pv_right.render()

    # -----------------------------------------------------
    # 外部入口
    # -----------------------------------------------------
    def plot(self, l: int, m: int, component: str = "real"):
        self._plot_left(l, m, component)
        self._plot_right(l, m, component)
