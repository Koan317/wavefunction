# mode_controls.py
from PyQt5 import QtWidgets, QtCore

class ModeControls(QtWidgets.QGroupBox):
    """显示模式单选框"""
    mode_changed = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("显示模式", parent)
        layout = QtWidgets.QGridLayout(self)

        self.radio_radial = QtWidgets.QRadioButton("径向 Rₙₗ(r)")
        self.radio_ylm_real = QtWidgets.QRadioButton("球谐 Yₗᵐ（实）")
        self.radio_ylm_imag = QtWidgets.QRadioButton("球谐 Yₗᵐ（虚）")
        self.radio_psire = QtWidgets.QRadioButton("R·Y（实）")
        self.radio_psiim = QtWidgets.QRadioButton("R·Y（虚）")
        self.radio_prob = QtWidgets.QRadioButton("|ψ|²")

        radios = [
            self.radio_radial,
            self.radio_ylm_real,
            self.radio_ylm_imag,
            self.radio_psire,
            self.radio_psiim,
            self.radio_prob,
        ]

        self.radio_radial.setChecked(True)

        for btn in radios:
            btn.toggled.connect(lambda checked, b=btn: checked and self.mode_changed.emit())

        self.group = QtWidgets.QButtonGroup(self)

        half = (len(radios) + 1) // 2
        for i, btn in enumerate(radios):
            self.group.addButton(btn)
            col = 0 if i < half else 1
            row = i if i < half else i - half
            layout.addWidget(btn, row, col)
