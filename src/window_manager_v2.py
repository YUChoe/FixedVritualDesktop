"""
창 관리 시스템 - 가상 데스크톱 지원 버전
"""
import threading
import time
import ctypes
from ctypes import wintypes
from typing import List, Optional, Dict, Set
from .models import WindowInfo
from .windows_api import WindowsAPIWrapper
from .logger import get_logger


class VirtualDesktopWindowManager:
    """가상 데스크톱 지원 창 관리 클래스"""

    def __init__(self, monitor_manager=None, monitor_interval: float = 2.0):
        self.logger = get_logger("VirtualDesktopWindowManager")
        self.api = WindowsAPIWrapper()

        # 모니터 정보
        from .monitor_manager import MonitorManager
        self.monitor_manager = monitor_manager or MonitorManager()
        self._secondary_monitor_bounds = self._get_secondary_monitor_bounds()

        # 창 상태 추적
        self._secondary_monitor_windows: Set[int] = set()  # 서브모니터의 창들
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_interval = monitor_interval
        self._stop_event = threading.Event()

        # 가상 데스크톱 API 초기화
        self._init_virtual_desktop_api()

    def _init_virtual_desktop_api(self):
        """가상 데스크톱 API 초기화"""
        try:
            # Windows 10/11 가상 데스크톱 COM 인터페이스
            import comtypes.client
            self._vd_manager = None
            self.logger.info("가상 데스크톱 API 초기화 시도")
        except Exception as e:
            self.logger.warning(f"가상 데스크톱 API 초기화 실패: {str(e)}")
            self._vd_manager = None

    def _get_secondary_monitor_bounds(self):
        """서브모니터 경계 계산"""
        try:
            secondary = self.monitor_manager.get_monitor_by_index(1)  # 서브모니터
            if secondary:
                bounds = (secondary.x, secondary.y,
                         secondary.x + secondary.width, secondary.y + secondary.height)
                self.logger.info(f"서브모니터 경계: {bounds}")
                return bounds
            else:
                self.logger.warning("서브모니터를 찾을 수 없음")
                return None
        except Exception as e:
            self.logger.error(f"서브모니터 경계 계산 실패: {str(e)}")
            return None

    def _is_window_in_secondary_monitor(self, x: int, y: int) -> bool:
        """창이 서브모니터에 있는지 확인"""
        if not self._secondary_monitor_bounds:
            return False

        left, top, right, bottom = self._secondary_monitor_bounds
        return left <= x < right and top <= y < bottom

    def start_monitoring(self) -> bool:
        """창 모니터링 시작"""
        if self._monitoring:
            return True

        try:
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_worker, daemon=True)
            self._monitor_thread.start()
            self._monitoring = True
            self.logger.info(f"창 모니터링 시작 (간격: {self._monitor_interval}초)")
            return True
        except Exception as e:
            self.logger.error(f"창 모니터링 시작 실패: {str(e)}")
            return False

    def stop_monitoring(self):
        """창 모니터링 중지"""
        if self._monitoring:
            self._stop_event.set()
            if self._monitor_thread:
                self._monitor_thread.join(timeout=2.0)
            self._monitoring = False
            self.logger.info("창 모니터링 중지")

    def _monitor_worker(self):
        """창 모니터링 워커 스레드"""
        while not self._stop_event.is_set():
            try:
                self._update_secondary_monitor_windows()
            except Exception as e:
                self.logger.error(f"창 모니터링 중 오류: {str(e)}")

            # 인터럽트 가능한 대기
            self._stop_event.wait(self._monitor_interval)

    def _update_secondary_monitor_windows(self):
        """서브모니터의 창 목록 업데이트"""
        try:
            current_windows = set()
            total_windows = 0
            visible_windows = 0

            # 모든 보이는 창 확인
            windows = self.api.enum_windows()
            total_windows = len(windows)

            for hwnd in windows:
                window_info = self.api.get_window_info(hwnd)
                if window_info and window_info.is_visible and window_info.title.strip():
                    visible_windows += 1
                    self.logger.debug(f"창 감지: {hwnd} '{window_info.title}' 위치=({window_info.x},{window_info.y})")

                    # 서브모니터에 있는 창인지 확인
                    is_secondary = False

                    # 1. 실제 서브모니터 경계 확인 (여유를 두어 300 <= x < 2300, -1100 <= y < 100)
                    if (300 <= window_info.x < 2300 and -1100 <= window_info.y < 100):
                        is_secondary = True
                        self.logger.debug(f"서브모니터 창 (경계내): {hwnd} '{window_info.title}'")

                    # 2. 전체화면 창 감지 (-32000 좌표는 특별 처리)
                    elif window_info.x == -32000 and window_info.y == -32000:
                        # 창 상태 확인 - 최소화된 창은 제외
                        if window_info.state != window_info.state.MINIMIZED and window_info.title.strip():
                            # 시스템 창이나 숨겨진 창 제외
                            excluded_titles = ['', 'Program Manager', 'Windows 입력 환경', 'Desktop Window Manager']
                            excluded_keywords = ['notepad++']  # 최소화된 Notepad++ 제외

                            title_lower = window_info.title.lower()
                            if (window_info.title not in excluded_titles and
                                not any(keyword in title_lower for keyword in excluded_keywords)):
                                is_secondary = True
                                self.logger.debug(f"서브모니터 창 (전체화면): {hwnd} '{window_info.title}'")

                    if is_secondary:
                        current_windows.add(hwnd)

            self.logger.debug(f"창 스캔 결과: 전체={total_windows}, 보이는창={visible_windows}, 서브모니터={len(current_windows)}")

            # 새로 추가된 창들 로깅
            new_windows = current_windows - self._secondary_monitor_windows
            if new_windows:
                self.logger.info(f"서브모니터에 새 창 감지: {len(new_windows)}개")

            # 제거된 창들 로깅
            removed_windows = self._secondary_monitor_windows - current_windows
            if removed_windows:
                self.logger.info(f"서브모니터에서 창 제거: {len(removed_windows)}개")

            self._secondary_monitor_windows = current_windows

        except Exception as e:
            self.logger.error(f"서브모니터 창 업데이트 실패: {str(e)}")

    def get_secondary_monitor_windows(self) -> List[int]:
        """현재 서브모니터에 있는 창 목록 반환"""
        return list(self._secondary_monitor_windows)

    def move_windows_to_current_desktop(self) -> int:
        """서브모니터의 창들을 현재 가상 데스크톱으로 이동"""
        moved_count = 0

        try:
            secondary_windows = self.get_secondary_monitor_windows()
            self.logger.info(f"서브모니터 창 {len(secondary_windows)}개를 현재 데스크톱으로 이동 시도")

            for hwnd in secondary_windows:
                if self._move_window_to_current_desktop(hwnd):
                    moved_count += 1
                    self.logger.debug(f"창 이동 성공: {hwnd}")
                else:
                    self.logger.debug(f"창 이동 실패: {hwnd}")

            self.logger.info(f"총 {moved_count}개 창을 현재 데스크톱으로 이동")
            return moved_count

        except Exception as e:
            self.logger.error(f"창 이동 중 오류: {str(e)}")
            return moved_count

    def _move_window_to_current_desktop(self, hwnd: int) -> bool:
        """개별 창을 현재 가상 데스크톱으로 이동"""
        try:
            import win32gui
            import win32con

            # 창 정보 확인
            window_info = self.api.get_window_info(hwnd)
            if not window_info:
                return False

            is_fullscreen = (window_info.x == -32000 and window_info.y == -32000)

            if is_fullscreen:
                self.logger.debug(f"전체화면 창 이동 시도: {hwnd} '{window_info.title}'")

                # 전체화면 창 특별 처리
                # 1. 전체화면 해제
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)

                # 2. 강제 활성화
                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.2)
                except:
                    pass

                # 3. 다시 전체화면으로
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

            else:
                self.logger.debug(f"일반 창 이동 시도: {hwnd} '{window_info.title}'")

                # 일반 창 처리
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                time.sleep(0.1)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.1)
                except:
                    pass

                try:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    time.sleep(0.1)
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                except:
                    pass

            return True

        except Exception as e:
            self.logger.debug(f"창 이동 실패 (hwnd: {hwnd}): {str(e)}")
            return False

    def force_refresh_secondary_windows(self):
        """서브모니터 창 목록 강제 새로고침"""
        self._update_secondary_monitor_windows()
        count = len(self._secondary_monitor_windows)
        self.logger.info(f"서브모니터 창 새로고침 완료: {count}개")
        return count

    def get_status(self) -> dict:
        """현재 상태 반환"""
        return {
            'monitoring': self._monitoring,
            'secondary_windows_count': len(self._secondary_monitor_windows),
            'secondary_windows': list(self._secondary_monitor_windows),
            'monitor_interval': self._monitor_interval
        }