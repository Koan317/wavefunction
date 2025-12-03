# ui.py
import sys
import multiprocessing
import queue as _queue  # 标准库 Queue 的 Empty 用
from math_radial import laguerre_precompute_worker, apply_laguerre_table
from PyQt5 import QtWidgets, QtCore
import pyvista as pv
from pyvistaqt import QtInteractor
from config import (
    MAX_N,
    DEFAULT_N,
    DEFAULT_L,
    DEFAULT_M,
)

# 拆分后的 UI 控件模块
from quantum_controls import QuantumControls
from mode_controls import ModeControls
from sampling_controls import SamplingControls

# 绘图器
from plot_radial import Radial2DCanvas
from plot_spherical import SphericalDualPlotter
from plot_wave3d import Wave3DPlotter

class WaveFunctionWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("氢原子波函数可视化")

        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        # ================= 顶部函数标题 =================
        self.func_label = QtWidgets.QLabel()
        font = self.func_label.font()
        font.setPointSize(14)
        font.setBold(True)
        self.func_label.setFont(font)
        main_layout.addWidget(self.func_label)

        # ================= 控件区域 =================
        controls_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(controls_layout)

        # 量子数组件（n,l,m）
        self.q_controls = QuantumControls()
        controls_layout.addWidget(self.q_controls, stretch=1)

        # 采样精度 N
        self.s_controls = SamplingControls()
        controls_layout.addWidget(self.s_controls, stretch=1)

        # 模式选择
        self.m_controls = ModeControls()
        controls_layout.addWidget(self.m_controls, stretch=2)

        # ================= 绘图区域（堆叠） =================
        self.stack = QtWidgets.QStackedLayout()
        main_layout.addLayout(self.stack, stretch=1)

        # 2D（径向）——主进程立即加载
        self.canvas_2d = Radial2DCanvas(self)
        self.stack.addWidget(self.canvas_2d)

        # 3D 单视图占位
        self._single_container = QtWidgets.QWidget(self)
        self.stack.addWidget(self._single_container)

        # 球谐双视图占位
        self.sph_container = QtWidgets.QWidget(self)
        self.stack.addWidget(self.sph_container)

        # 3D 对象延迟初始化
        self.pv_single = None
        self.pv_left = None
        self.pv_right = None
        self.sph_plotter = None
        self.wave3d_plotter = None
        self._3d_initialized = False

        # 初始化量子数组件
        self._init_quantum_controls()

        # ================= 信号连接 =================
        # 量子数变化 → 弹窗
        self.q_controls.n_combo.currentIndexChanged.connect(
            lambda _v: self._on_n_changed()
        )
        self.q_controls.l_combo.currentIndexChanged.connect(
            lambda _v: self._on_l_changed()
        )
        self.q_controls.m_combo.currentIndexChanged.connect(
            lambda _v: self.update_plot(show_dialog=True)
        )

        # 模式改变 → 弹窗
        self.m_controls.mode_changed.connect(
            lambda: self.update_plot(show_dialog=True)
        )
        self.m_controls.mode_changed.connect(self._update_sampling_enabled)

        # 采样精度变化 → 不弹窗
        self.s_controls.sampling_changed.connect(
            lambda _v: self.update_plot(show_dialog=False)
        )

        # 初始化采样控件是否启用
        self._update_sampling_enabled()

        # 初始绘图
        self.update_plot(show_dialog=False)

        # 异步（事件循环开始后）初始化 3D 控件：只创建组件，不画图
        QtCore.QTimer.singleShot(0, self._init_3d_views)

        # Laguerre 多项式后台预计算（多进程）
        self._laguerre_queue = multiprocessing.Queue()
        self._laguerre_proc = multiprocessing.Process(
            target=laguerre_precompute_worker,
            args=(self._laguerre_queue, )
        )
        self._laguerre_proc.daemon = True
        self._laguerre_proc.start()

        # 用 QTimer 轮询子进程结果，不阻塞 UI
        self._laguerre_timer = QtCore.QTimer(self)
        self._laguerre_timer.timeout.connect(self._poll_laguerre_result)
        self._laguerre_timer.start(100)

    def _poll_laguerre_result(self):
        if self._laguerre_queue is None:
            return
        try:
            rho_grid, cache = self._laguerre_queue.get_nowait()
        except _queue.Empty:
            return

        # 应用预计算表
        apply_laguerre_table(rho_grid, cache)

        # 清理定时器和队列
        self._laguerre_timer.stop()
        self._laguerre_queue = None
        # 子进程设成守护进程，会自动退出；保险一点可以尝试 terminate
        try:
            self._laguerre_proc.terminate()
        except Exception:
            pass
        self._laguerre_proc = None

    # ================================================================
    # 量子数逻辑
    # ================================================================
    def _init_quantum_controls(self):
        ns = [self.q_controls.n_combo.itemData(i)
              for i in range(self.q_controls.n_combo.count())]
        try:
            idx = ns.index(DEFAULT_N)
        except ValueError:
            idx = 0
        self.q_controls.n_combo.setCurrentIndex(idx)
        self.q_controls.update_l()
        self.q_controls.update_m()

    def _on_n_changed(self):
        self.q_controls.update_l()
        self.q_controls.update_m()
        self.update_plot(show_dialog=True)

    def _on_l_changed(self):
        self.q_controls.update_m()
        self.update_plot(show_dialog=True)

    # ================================================================
    # 读取当前参数
    # ================================================================
    def current_n(self): return self.q_controls.current_n()
    def current_l(self): return self.q_controls.current_l()
    def current_m(self): return self.q_controls.current_m()
    def current_N(self): return self.s_controls.slider.value()

    # ================================================================
    # 启用/禁用采样精度控件
    # ================================================================
    def _update_sampling_enabled(self):
        is_dense = (
            self.m_controls.radio_psire.isChecked() or
            self.m_controls.radio_psiim.isChecked() or
            self.m_controls.radio_prob.isChecked()
        )
        self.s_controls.slider.setEnabled(is_dense)
        self.s_controls.label.setEnabled(is_dense)

    # ================================================================
    # 顶部标题
    # ================================================================
    def _function_label(self):
        n, l, m = self.current_n(), self.current_l(), self.current_m()

        if self.m_controls.radio_radial.isChecked():
            return f"R{n}{l}(r)"
        if self.m_controls.radio_ylm_real.isChecked():
            return f"Y_{l}^{m}（实部）"
        if self.m_controls.radio_ylm_imag.isChecked():
            return f"Y_{l}^{m}（虚部）"
        if self.m_controls.radio_psire.isChecked():
            return f"R{n}{l}·Re(Y_{l}^{m})"
        if self.m_controls.radio_psiim.isChecked():
            return f"R{n}{l}·Im(Y_{l}^{m})"
        if self.m_controls.radio_prob.isChecked():
            return f"|ψ_{{{n}{l}{m}}}|²"

    # ================================================================
    # 核心：更新图像
    # ================================================================
    def update_plot(self, show_dialog=True):
        n, l, m = self.current_n(), self.current_l(), self.current_m()
        N = self.current_N()

        self.func_label.setText(self._function_label())

        # ---------------- 径向 ----------------
        if self.m_controls.radio_radial.isChecked():
            self.stack.setCurrentIndex(0)
            self.canvas_2d.plot_radial(n, l)
            return

        # ---------------- 球谐：双视图 ----------------
        if self.m_controls.radio_ylm_real.isChecked():
            self.stack.setCurrentIndex(2)
            self.sph_plotter.plot(l, m, component="real")
            return

        if self.m_controls.radio_ylm_imag.isChecked():
            self.stack.setCurrentIndex(2)
            self.sph_plotter.plot(l, m, component="imag")
            return

        # ---------------- RY/ψ²：3D 点密度 ----------------
        self.stack.setCurrentIndex(1)

        # 如果当前模式需要 3D，而 3D 还没初始化，则立即初始化一次
        need_3d = (
            self.m_controls.radio_ylm_real.isChecked() or
            self.m_controls.radio_ylm_imag.isChecked() or
            self.m_controls.radio_psire.isChecked() or
            self.m_controls.radio_psiim.isChecked() or
            self.m_controls.radio_prob.isChecked()
        )
        if need_3d and not self._3d_initialized:
            self._init_3d_views()

        dlg = None
        if show_dialog:
            dlg = QtWidgets.QProgressDialog(
                "Loading", None, 0, 0, self
            )
            dlg.setWindowFlags(
                QtCore.Qt.Dialog |
                QtCore.Qt.CustomizeWindowHint |
                QtCore.Qt.WindowTitleHint
            )
            dlg.setWindowModality(QtCore.Qt.WindowModal)
            dlg.setMinimumDuration(0)
            dlg.show()
            QtWidgets.QApplication.processEvents()

        # 绘制
        if self.m_controls.radio_psire.isChecked():
            self.wave3d_plotter.plot(n, l, m, mode="psi_real", N=N)

        elif self.m_controls.radio_psiim.isChecked():
            self.wave3d_plotter.plot(n, l, m, mode="psi_imag", N=N)

        elif self.m_controls.radio_prob.isChecked():
            self.wave3d_plotter.plot(n, l, m, mode="psi_prob", N=N)

        if dlg is not None:
            dlg.close()

    def _init_3d_views(self):
        if self._3d_initialized:
            return

        # 单视图 3D
        layout_single = QtWidgets.QVBoxLayout(self._single_container)
        layout_single.setContentsMargins(0, 0, 0, 0)

        self.pv_single = QtInteractor(self._single_container)
        self.pv_single.enable_depth_peeling()
        layout_single.addWidget(self.pv_single)

        # 球谐双视图
        hl = QtWidgets.QHBoxLayout(self.sph_container)
        hl.setContentsMargins(0, 0, 0, 0)

        self.pv_left = QtInteractor(self.sph_container)
        self.pv_left.enable_depth_peeling()
        self.pv_right = QtInteractor(self.sph_container)
        self.pv_right.enable_depth_peeling()

        hl.addWidget(self.pv_left)
        hl.addWidget(self.pv_right)

        # 绘图器对象
        self.sph_plotter = SphericalDualPlotter(self.pv_left, self.pv_right)
        self.wave3d_plotter = Wave3DPlotter(self.pv_single)

        self._3d_initialized = True


    # ================================================================
    # 关闭事件（防止 OpenGL 崩溃）
    # ================================================================
    def closeEvent(self, event):
        try:
            self.pv_left.close()
            self.pv_right.close()
            self.pv_single.close()
            self.canvas_2d.plotter.close()
        except:
            pass
        event.accept()

# ===================================================================
# 入口
# ===================================================================
def run_app():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    pv.set_plot_theme("dark")

    win = WaveFunctionWindow()
    win.resize(1400, 900)
    win.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
