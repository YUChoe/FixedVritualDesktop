"""
가상 데스크톱 모니터 제어 애플리케이션

Windows 11의 가상 데스크톱 전환 시 서브모니터의 창들을 고정시키는 기능을 제공합니다.
"""

__version__ = "1.0.0"
__author__ = "Virtual Desktop Monitor Control"

from .models import WindowInfo, WindowState, MonitorInfo, AppConfig

__all__ = [
    "WindowInfo",
    "WindowState",
    "MonitorInfo",
    "AppConfig"
]