"""
Windows API 래퍼 클래스

Windows API 함수들을 Python에서 사용하기 위한 래퍼와 오류 처리 로직을 제공합니다.
"""
import win32api
import win32gui
import win32con
import win32process
from typing import List, Tuple, Optional, Callable
import ctypes
from ctypes import wintypes
import logging

from .models import WindowInfo, WindowState, MonitorInfo


class WindowsAPIError(Exception):
    """Windows API 관련 예외 클래스"""
    def __init__(self, message: str, error_code: int = None):
        super().__init__(message)
        self.error_code = error_code


class WindowsAPIWrapper:
    """Windows API 함수들을 래핑하는 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _handle_win32_error(self, operation: str) -> None:
        """Win32 API 오류를 처리하고 예외로 변환"""
        try:
            error_code = win32api.GetLastError()
            if error_code != 0:
                error_message = win32api.FormatMessage(error_code)
                raise WindowsAPIError(
                    f"{operation} 실패: {error_message.strip()}",
                    error_code
                )
        except Exception as e:
            raise WindowsAPIError(f"{operation} 중 오류 발생: {str(e)}")

    def enum_windows(self) -> List[int]:
        """모든 최상위 창의 핸들 목록을 반환"""
        window_handles = []

        def enum_windows_proc(hwnd: int, lparam: int) -> bool:
            window_handles.append(hwnd)
            return True

        try:
            win32gui.EnumWindows(enum_windows_proc, 0)
            return window_handles
        except Exception as e:
            self._handle_win32_error("창 목록 열거")
            return []

    def get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """창 핸들로부터 창 정보를 수집"""
        try:
            # 창이 유효한지 확인
            if not win32gui.IsWindow(hwnd):
                return None

            # 창 제목 가져오기
            title = win32gui.GetWindowText(hwnd)

            # 창 클래스명 가져오기
            class_name = win32gui.GetClassName(hwnd)

            # 프로세스 ID 가져오기
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)

            # 창 위치 및 크기 가져오기
            rect = win32gui.GetWindowRect(hwnd)
            x, y, right, bottom = rect
            width = right - x
            height = bottom - y

            # 창 상태 확인
            placement = win32gui.GetWindowPlacement(hwnd)
            show_cmd = placement[1]

            if show_cmd == win32con.SW_SHOWMINIMIZED:
                state = WindowState.MINIMIZED
            elif show_cmd == win32con.SW_SHOWMAXIMIZED:
                state = WindowState.MAXIMIZED
            else:
                state = WindowState.NORMAL

            # 창이 보이는지 확인
            is_visible = win32gui.IsWindowVisible(hwnd)

            # 모니터 핸들 가져오기
            monitor_handle = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)

            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                process_id=process_id,
                x=x,
                y=y,
                width=width,
                height=height,
                state=state,
                monitor_handle=monitor_handle,
                is_visible=is_visible
            )

        except Exception as e:
            self.logger.warning(f"창 정보 수집 실패 (hwnd: {hwnd}): {str(e)}")
            return None

    def set_window_pos(self, hwnd: int, x: int, y: int, width: int, height: int,
                      flags: int = 0) -> bool:
        """창 위치와 크기를 설정"""
        try:
            result = win32gui.SetWindowPos(
                hwnd, 0, x, y, width, height,
                flags or (win32con.SWP_NOZORDER | win32con.SWP_NOACTIVATE)
            )
            if not result:
                self._handle_win32_error("창 위치 설정")
            return result
        except Exception as e:
            self.logger.error(f"창 위치 설정 실패 (hwnd: {hwnd}): {str(e)}")
            return False

    def restore_window_placement(self, hwnd: int, placement_data: tuple) -> bool:
        """창 배치 정보를 복원"""
        try:
            result = win32gui.SetWindowPlacement(hwnd, placement_data)
            if not result:
                self._handle_win32_error("창 배치 복원")
            return result
        except Exception as e:
            self.logger.error(f"창 배치 복원 실패 (hwnd: {hwnd}): {str(e)}")
            return False

    def enum_display_monitors(self) -> List[MonitorInfo]:
        """모든 디스플레이 모니터 정보를 반환"""
        monitors = []

        try:
            # ctypes를 사용하여 EnumDisplayMonitors 직접 호출
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32

            # 콜백 함수 타입 정의
            MonitorEnumProc = ctypes.WINFUNCTYPE(
                wintypes.BOOL,
                wintypes.HMONITOR,
                wintypes.HDC,
                ctypes.POINTER(wintypes.RECT),
                wintypes.LPARAM
            )

            def monitor_enum_proc(hmonitor, hdc, rect_ptr, data):
                try:
                    # 모니터 정보 가져오기
                    monitor_info = win32api.GetMonitorInfo(hmonitor)

                    # 모니터 영역 정보
                    monitor_rect = monitor_info['Monitor']
                    x, y, right, bottom = monitor_rect
                    width = right - x
                    height = bottom - y

                    # 주 모니터 여부 확인
                    is_primary = monitor_info['Flags'] == win32con.MONITORINFOF_PRIMARY

                    # 디바이스 이름
                    device_name = monitor_info.get('Device', f'Monitor_{hmonitor}')

                    monitor = MonitorInfo(
                        handle=hmonitor,
                        device_name=device_name,
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        is_primary=is_primary
                    )

                    monitors.append(monitor)

                except Exception as e:
                    self.logger.warning(f"모니터 정보 수집 실패 (handle: {hmonitor}): {str(e)}")

                return True

            # EnumDisplayMonitors 호출
            user32.EnumDisplayMonitors(None, None, MonitorEnumProc(monitor_enum_proc), 0)

            return monitors

        except Exception as e:
            self.logger.error(f"모니터 목록 열거 실패: {str(e)}")
            return []

    def get_monitor_from_window(self, hwnd: int) -> int:
        """창이 위치한 모니터의 핸들을 반환"""
        try:
            return win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
        except Exception as e:
            self.logger.error(f"창의 모니터 정보 가져오기 실패 (hwnd: {hwnd}): {str(e)}")
            return 0

    def is_window_valid(self, hwnd: int) -> bool:
        """창 핸들이 유효한지 확인"""
        try:
            return win32gui.IsWindow(hwnd)
        except Exception:
            return False

    def show_window(self, hwnd: int, cmd_show: int) -> bool:
        """창 표시 상태를 변경"""
        try:
            result = win32gui.ShowWindow(hwnd, cmd_show)
            return True
        except Exception as e:
            self.logger.error(f"창 표시 상태 변경 실패 (hwnd: {hwnd}): {str(e)}")
            return False

    def get_foreground_window(self) -> int:
        """현재 포어그라운드 창의 핸들을 반환"""
        try:
            return win32gui.GetForegroundWindow()
        except Exception as e:
            self.logger.error(f"포어그라운드 창 가져오기 실패: {str(e)}")
            return 0