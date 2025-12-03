import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from math_radial import radial_wavefunction


class Radial2DCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('bottom', 'r')
        self.plot_widget.setLabel('left', 'R(r)')

        self.curve = self.plot_widget.plot([], [], pen=pg.mkPen(color='cyan', width=2))

        self.n = 1
        self.l = 0

        # 固定的初始绘制范围
        self.default_min = 0
        self.default_max = 40

        # 防止递归触发
        self._manual_update = False

        # 只在用户真的缩放/平移后自动更新
        self.plot_widget.sigRangeChanged.connect(self._on_range_changed)

    def _autoscale_radial(self):
        """自动调整坐标系：左端靠近 0，右端是最后峰值后一点，上下端包住最大最小值"""
        # 使用默认全范围计算一次
        r = np.linspace(self.default_min, self.default_max, 3000)
        R = radial_wavefunction(self.n, self.l, r)

        # 找出最后一个波峰
        # 简单方式：找局部最大值
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(R)

        if len(peaks) > 0:
            last_peak_r = r[peaks[-1]]
        else:
            last_peak_r = self.default_max * 0.8  # 无峰的情况（比如 n=1,l=0）

        # 右侧多给一点 buffer
        right = last_peak_r + (last_peak_r * 0.15)

        # 左侧固定，例如 0 或 -2
        left = -2  # 如果你想要 x=0，就改成 0

        # 上下限
        top = np.max(R)
        bottom = np.min(R)

        # 应用范围（防止递归触发重绘）
        self._manual_update = True
        self.plot_widget.setXRange(left, right, padding=0)
        self.plot_widget.setYRange(bottom, top, padding=0)
        self._manual_update = False

    # ---------------------
    # 外部调用
    # ---------------------
    def plot_radial(self, n, l):
        # 检查是否改变了 n 或 l
        is_changed = (self.n != n) or (self.l != l)

        self.n = n
        self.l = l

        # 如果 n/l 变了 → 自动调整开始
        if is_changed:
            self._manual_update = True
            # 用默认范围先画一次（避免空图 autoscale）
            self._draw_range(self.default_min, self.default_max)
            self._manual_update = False

            # 自动缩放到合理视图
            self._autoscale_radial()
        else:
            # m 改变，不触发 autoscale
            self._draw_range(self.default_min, self.default_max)

    # ---------------------
    # 主动绘制某个范围
    # ---------------------
    def _draw_range(self, xmin, xmax):
        if xmax <= xmin:
            return

        # r 必须 ≥ 0
        xmin = max(0, xmin)
        xmax = max(0, xmax)

        r = np.linspace(xmin, xmax, 2000)
        R = radial_wavefunction(self.n, self.l, r)

        self.curve.setData(r, R)


    # ---------------------
    # 仅在用户操作时自动更新
    # ---------------------
    def _on_range_changed(self, view, range):
        if self._manual_update:
            return    # 不处理程序内部设定的范围

        xmin, xmax = self.plot_widget.viewRange()[0]

        # 限制最大可绘制范围，防止坐标爆炸
        if xmax - xmin > 200:
            xmax = xmin + 200
            self._manual_update = True
            self.plot_widget.setXRange(xmin, xmax, padding=0)
            self._manual_update = False

        self._draw_range(xmin, xmax)
