# sampling_controls.py
from PyQt5 import QtWidgets, QtCore

class SamplingControls(QtWidgets.QGroupBox):
    """采样点数 N 控件"""

    sampling_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__("采样点数 N", parent)

        layout = QtWidgets.QVBoxLayout(self)

        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(5000, 1_000_000)
        self.slider.setValue(200_000)

        self.label = QtWidgets.QLabel("N = 200000")

        layout.addWidget(self.slider)
        layout.addWidget(self.label)

        self.slider.valueChanged.connect(self.on_value_changed)

    def on_value_changed(self, v):
        self.label.setText(f"N = {v}")
        self.sampling_changed.emit(v)
