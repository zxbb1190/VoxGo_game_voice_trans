"""Manual mobile-server launcher using the same routes and assets as VoxGo."""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from voxgo.mobile.server import MobileWebSocketManager

manager = MobileWebSocketManager()
app = manager._app
broadcast = manager.broadcast_translation

if __name__ == "__main__":
    print("Mobile server: " + manager.get_mobile_url())
    asyncio.run(manager.start_server())
