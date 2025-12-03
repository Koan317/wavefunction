# quantum_controls.py
from PyQt5 import QtWidgets
from math_radial import (
    available_n_values,
    available_l_values,
    available_m_values,
)

class QuantumControls(QtWidgets.QGroupBox):
    """量子数组件（n, l, m）"""

    def __init__(self, parent=None):
        super().__init__("量子数", parent)

        layout = QtWidgets.QVBoxLayout(self)

        self.n_combo = QtWidgets.QComboBox()
        self.l_combo = QtWidgets.QComboBox()
        self.m_combo = QtWidgets.QComboBox()

        # ---- n ----
        for n in available_n_values():
            self.n_combo.addItem(str(n), n)

        row1 = QtWidgets.QHBoxLayout()
        row1.addWidget(QtWidgets.QLabel("n:"))
        row1.addWidget(self.n_combo)

        row2 = QtWidgets.QHBoxLayout()
        row2.addWidget(QtWidgets.QLabel("l:"))
        row2.addWidget(self.l_combo)

        row3 = QtWidgets.QHBoxLayout()
        row3.addWidget(QtWidgets.QLabel("m:"))
        row3.addWidget(self.m_combo)

        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(row3)

    # ---- 工具函数 ----
    def current_n(self): return self.n_combo.currentData()
    def current_l(self): return self.l_combo.currentData()
    def current_m(self): return self.m_combo.currentData()

    def update_l(self):
        n = self.current_n()
        ls = available_l_values(n)
        old = self.current_l()
        self.l_combo.blockSignals(True)
        self.l_combo.clear()
        for l in ls:
            self.l_combo.addItem(str(l), l)
        if old in ls:
            self.l_combo.setCurrentIndex(ls.index(old))
        else:
            self.l_combo.setCurrentIndex(0)
        self.l_combo.blockSignals(False)

    def update_m(self):
        l = self.current_l()
        ms = available_m_values(l)
        old = self.current_m()
        self.m_combo.blockSignals(True)
        self.m_combo.clear()
        for m in ms:
            self.m_combo.addItem(str(m), m)
        if old in ms:
            self.m_combo.setCurrentIndex(ms.index(old))
        elif 0 in ms:
            self.m_combo.setCurrentIndex(ms.index(0))
        else:
            self.m_combo.setCurrentIndex(0)
        self.m_combo.blockSignals(False)
