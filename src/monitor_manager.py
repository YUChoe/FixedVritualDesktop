"""
모니터 관리 시스템 - 최소 기능 구현
"""
from typing import List, Optional
from .models import MonitorInfo
from .windows_api import WindowsAPIWrapper
from .logger import get_logger


class MonitorManager:
    """모니터 관리 클래스"""

    def __init__(self):
        self.logger = get_logger("MonitorManager")
        self.api = WindowsAPIWrapper()
        self._monitors: List[MonitorInfo] = []
        self.refresh_monitors()

    def refresh_monitors(self) -> bool:
        """모니터 정보를 새로고침"""
        try:
            self._monitors = self.api.enum_display_monitors()
            self.logger.info(f"모니터 {len(self._monitors)}개 감지")
            return True
        except Exception as e:
            self.logger.error(f"모니터 새로고침 실패: {str(e)}")
            return False

    def get_monitors(self) -> List[MonitorInfo]:
        """모든 모니터 정보 반환"""
        return self._monitors.copy()

    def get_primary_monitor(self) -> Optional[MonitorInfo]:
        """주 모니터 반환"""
        for monitor in self._monitors:
            if monitor.is_primary:
                return monitor
        return None

    def get_monitor_by_index(self, index: int) -> Optional[MonitorInfo]:
        """인덱스로 모니터 조회 (0: 주모니터, 1+: 보조모니터)"""
        if index == 0:
            return self.get_primary_monitor()

        secondary = [m for m in self._monitors if not m.is_primary]
        if 1 <= index <= len(secondary):
            return secondary[index - 1]
        return None