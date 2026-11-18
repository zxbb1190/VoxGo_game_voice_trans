"""
简化启动 - 测试核心功能
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.app_info import APP_NAME
from voxgo.ui.config_models import OverlayConfig
from voxgo.ui.overlay_window import GameOverlay

def test_overlay():
    """测试浮窗"""
    app = QApplication([])
    overlay = GameOverlay(OverlayConfig())
    overlay.show()
    
    # 添加测试翻译
    overlay.add_translation("Hello team, push A site", "队友，冲A点")
    overlay.add_translation("He's one shot", "他大残了")
    overlay.add_translation("Need backup", "需要支援")
    
    print("✅ 浮窗已启动，关闭窗口停止")
    app.exec_()

if __name__ == "__main__":
    print(f"{APP_NAME} - 简化测试")
    print("正在启动浮窗...")
    
    # QApplication and widgets belong to the main thread, as in the real app.
    test_overlay()
