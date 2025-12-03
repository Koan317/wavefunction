# sampling_controls.py
from PyQt5 import QtWidgets, QtCore

class SamplingControls(QtWidgets.QGroupBox):
    """采样点数 N 控件"""

    sampling_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("采样点数 N", parent)

        layout = QtWidgets.QVBoxLayout(self)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(10000, 2_000_000)
        self.slider.setValue(200_000)
        self.slider.setSingleStep(10000)
        self.slider.setPageStep(10000)

        self.label = QtWidgets.QLabel("N = 200000")

        layout.addWidget(self.slider)
        layout.addWidget(self.label)

        self.slider.valueChanged.connect(self.on_value_changed)

    def set_max_for_n(self, n: int):
        """根据主量子数 n 动态调整采样点数上限。

        规则：n=10 时上限 2,000,000，每改变 1，最大值变化 100,000。
        """

        max_value = max(10000, 2_000_000 + (n - 10) * 100_000)
        self.slider.setMaximum(max_value)

        if self.slider.value() > max_value:
            self.slider.setValue(max_value)
        else:
            # 确保标签与当前值同步
            self.on_value_changed(self.slider.value())

    def on_value_changed(self, v):
        # 自动拉回到最近的 10000 倍数
        snapped = (v // 10000) * 10000

        # 如果拉回后的值和 slider 显示不一致，则更新 slider 本身
        if snapped != v:
            self.slider.blockSignals(True)
            self.slider.setValue(snapped)
            self.slider.blockSignals(False)

        self.label.setText(f"N = {snapped}")
        self.sampling_changed.emit(snapped)

