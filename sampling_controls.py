# sampling_controls.py
from PyQt5 import QtWidgets, QtCore


class JumpSlider(QtWidgets.QSlider):
    """点击直接跳转到点击位置的滑块"""

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)
            groove = self.style().subControlRect(
                QtWidgets.QStyle.CC_Slider,
                opt,
                QtWidgets.QStyle.SC_SliderGroove,
                self,
            )
            handle = self.style().subControlRect(
                QtWidgets.QStyle.CC_Slider,
                opt,
                QtWidgets.QStyle.SC_SliderHandle,
                self,
            )

            if self.orientation() == QtCore.Qt.Horizontal:
                slider_min = groove.x()
                slider_max = groove.right() - handle.width() + 1
                pos = event.pos().x()
            else:
                slider_min = groove.y()
                slider_max = groove.bottom() - handle.height() + 1
                pos = event.pos().y()

            new_val = QtWidgets.QStyle.sliderValueFromPosition(
                self.minimum(),
                self.maximum(),
                pos - slider_min,
                slider_max - slider_min,
                opt.upsideDown,
            )
            # 标记本次跳转，避免在按下时触发采样更新
            self._jump_in_progress = True
            try:
                self.setValue(new_val)
            finally:
                self._jump_in_progress = False
            event.accept()

        super().mousePressEvent(event)

class SamplingControls(QtWidgets.QGroupBox):
    """采样点数 N 控件"""

    sampling_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("采样点数 N", parent)

        layout = QtWidgets.QVBoxLayout(self)

        self.slider = JumpSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(10000, 2_000_000)
        self.slider.setValue(200_000)
        self.slider.setSingleStep(10000)
        self.slider.setPageStep(10000)

        self.label = QtWidgets.QLabel("N = 200000")

        layout.addWidget(self.slider)
        layout.addWidget(self.label)

        self.slider.sliderReleased.connect(self.on_slider_released)
        self.slider.valueChanged.connect(self.on_value_changed)

        # 初始标签同步
        self._apply_value(self.slider.value(), emit_signal=False)

    def set_max_for_n(self, n: int, emit_signal: bool = True):
        max_value = max(10000, 200_000 + n * 200_000)
        self.slider.setMaximum(max_value)

        if self.slider.value() > max_value:
            self.slider.blockSignals(True)
            self.slider.setValue(max_value)
            self.slider.blockSignals(False)

        # 确保标签与当前值同步
        self._apply_value(self.slider.value(), emit_signal=emit_signal)

    def on_value_changed(self, v):
        # 鼠标拖拽未松开前不更新标签/图像
        if self.slider.isSliderDown() or getattr(self.slider, "_jump_in_progress", False):
            return

        self._apply_value(v)

    def on_slider_released(self):
        self._apply_value(self.slider.value())

    def _apply_value(self, v: int, emit_signal: bool = True):
        """对齐到 10000 的倍数，并更新标签和信号。"""
        snapped = (v // 10000) * 10000

        # 如果拉回后的值和 slider 显示不一致，则更新 slider 本身
        if snapped != v:
            self.slider.blockSignals(True)
            self.slider.setValue(snapped)
            self.slider.blockSignals(False)

        self.label.setText(f"N = {snapped}")
        if emit_signal:
            self.sampling_changed.emit(snapped)

