# config.py
"""
全局配置参数
"""

# 主量子数最大值
MAX_N = 7

# 径向坐标设置（原子单位）
R_MAX = 40.0
R_POINTS = 600

# 球坐标网格
THETA_POINTS = 80
PHI_POINTS = 160

# 球谐函数绘图的尺度
SPHERICAL_RADIUS_SCALE = 1.0  # 形状缩放
SPHERICAL_EPS = 1e-6          # 防止全 0 导致数值问题

# PyVista 绘图相关
BACKGROUND_COLOR = "black"
LINE_COLOR = "white"

# 颜色映射（正负不同颜色）
SPHERICAL_CMAP = "coolwarm"

# UI 默认数值
DEFAULT_N = 1
DEFAULT_L = 0
DEFAULT_M = 0
