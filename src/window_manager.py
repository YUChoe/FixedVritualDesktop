"""
창 관리 시스템 - 최소 기능 구현
"""
from typing import List, Optional, Dict
from .models import WindowInfo
from .windows_api import WindowsAPIWrapper
from .logger import get_logger


class WindowManager:
    """창 관리 클래스"""

    def __init__(self):
        self.logger = get_logger("WindowManager")
        self.api = WindowsAPIWrapper()
        self._window_states: Dict[int, tuple] = {}  # hwnd -> placement_data

    def get_visible_windows(self) -> List[WindowInfo]:
        """보이는 창 목록 반환"""
        windows = []
        try:
            handles = self.api.enum_windows()
            for hwnd in handles:
                window_info = self.api.get_window_info(hwnd)
                if window_info and window_info.is_visible and window_info.title.strip():
                    windows.append(window_info)

            self.logger.debug(f"보이는 창 {len(windows)}개 수집")
            return windows

        except Exception as e:
            self.logger.error(f"창 목록 수집 실패: {str(e)}")
            return []

    def get_windows_on_monitor(self, monitor_handle: int) -> List[WindowInfo]:
        """특정 모니터의 창 목록 반환"""
        windows = self.get_visible_windows()
        return [w for w in windows if w.monitor_handle == monitor_handle]

    def save_window_state(self, hwnd: int) -> bool:
        """창 상태 저장"""
        try:
            import win32gui
            placement = win32gui.GetWindowPlacement(hwnd)
            self._window_states[hwnd] = placement
            self.logger.debug(f"창 상태 저장: {hwnd}")
            return True
        except Exception as e:
            self.logger.error(f"창 상태 저장 실패 (hwnd: {hwnd}): {str(e)}")
            return False

    def restore_window_state(self, hwnd: int) -> bool:
        """창 상태 복원"""
        if hwnd not in self._window_states:
            return False

        try:
            placement = self._window_states[hwnd]
            return self.api.restore_window_placement(hwnd, placement)
        except Exception as e:
            self.logger.error(f"창 상태 복원 실패 (hwnd: {hwnd}): {str(e)}")
            return False

    def save_monitor_windows(self, monitor_handle: int) -> int:
        """모니터의 모든 창 상태 저장"""
        windows = self.get_windows_on_monitor(monitor_handle)
        saved_count = 0

        for window in windows:
            if self.save_window_state(window.hwnd):
                saved_count += 1

        self.logger.info(f"모니터 {monitor_handle}의 창 {saved_count}개 상태 저장")
        return saved_count

    def restore_monitor_windows(self, monitor_handle: int) -> int:
        """모니터의 모든 창 상태 복원"""
        restored_count = 0

        for hwnd in list(self._window_states.keys()):
            if self.api.is_window_valid(hwnd):
                current_monitor = self.api.get_monitor_from_window(hwnd)
                if current_monitor == monitor_handle:
                    if self.restore_window_state(hwnd):
                        restored_count += 1

        self.logger.info(f"모니터 {monitor_handle}의 창 {restored_count}개 상태 복원")
        return restored_count