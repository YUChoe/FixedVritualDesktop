"""
가상 데스크톱 제어 시스템 - 선택적 창 고정 기능
"""
from typing import Callable, Optional
import time
import threading
from .monitor_manager import MonitorManager
from .selective_window_manager import SelectiveWindowManager
from .hotkey_listener import HotkeyListener
from .logger import get_logger


class VirtualDesktopController:
    """가상 데스크톱 제어 클래스 - 선택된 창만 가상 데스크톱을 따라다님"""

    def __init__(self, target_monitor_index: int = 1):
        """
        Args:
            target_monitor_index: 사용하지 않음 (하위 호환성을 위해 유지)
        """
        self.logger = get_logger("VirtualDesktopController")
        self.target_monitor_index = target_monitor_index

        # 매니저 초기화
        self.monitor_manager = MonitorManager()
        self.window_manager = SelectiveWindowManager()
        self.hotkey_listener = HotkeyListener()

        # 핫키 콜백 설정
        self.hotkey_listener.set_callback(self._on_hotkey_pressed)

        self._enabled = False
        self._last_action_time = 0
        self._action_cooldown = 1.5  # 1.5초 쿨다운 (중복 방지)

        # 가상 데스크톱 추적
        self._current_desktop_id = None
        self._last_desktop_id = None
        self._processing_lock = threading.Lock()  # 동시 실행 방지

    def start(self) -> bool:
        """가상 데스크톱 제어 시작"""
        try:
            # 핫키 리스너 시작
            if self.hotkey_listener.start():
                self._enabled = True
                pinned_count = len(self.window_manager.get_pinned_windows())
                self.logger.info(f"선택적 창 고정 시스템 시작 (고정된 창: {pinned_count}개)")
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"가상 데스크톱 제어 시작 실패: {str(e)}")
            return False

    def stop(self) -> None:
        """가상 데스크톱 제어 중지"""
        self._enabled = False
        self.hotkey_listener.stop()
        self.logger.info("선택적 창 고정 시스템 중지")

    def _on_hotkey_pressed(self, direction: str) -> None:
        """핫키 눌림 이벤트 처리"""
        if not self._enabled:
            return

        # 동시 실행 방지
        if not self._processing_lock.acquire(blocking=False):
            self.logger.debug("이미 처리 중인 데스크톱 전환이 있어 무시")
            return

        try:
            # 쿨다운 체크
            current_time = time.time()
            if current_time - self._last_action_time < self._action_cooldown:
                self.logger.debug(f"쿨다운 중 ({self._action_cooldown}초) - 무시")
                return

            self._last_action_time = current_time

            self.logger.info(f"가상 데스크톱 전환 감지: {direction}")
            self._handle_desktop_switch(direction)

        except Exception as e:
            self.logger.error(f"데스크톱 전환 처리 중 오류: {str(e)}")
        finally:
            self._processing_lock.release()

    def _get_current_desktop_id(self) -> Optional[str]:
        """현재 가상 데스크톱 ID 가져오기"""
        try:
            import win32gui

            # 현재 보이는 창들의 조합으로 데스크톱 상태 식별
            visible_windows = []

            def enum_windows_proc(hwnd, lParam):
                if win32gui.IsWindowVisible(hwnd):
                    try:
                        title = win32gui.GetWindowText(hwnd)
                        if title.strip() and len(title.strip()) > 0:  # 제목이 있는 창만
                            # 시스템 창 제외
                            excluded_titles = ['Program Manager', 'Windows 입력 환경', 'Desktop Window Manager']
                            if title not in excluded_titles:
                                visible_windows.append(hwnd)
                    except:
                        pass
                return True

            win32gui.EnumWindows(enum_windows_proc, 0)

            # 보이는 창들의 핸들 조합으로 데스크톱 식별자 생성
            if visible_windows:
                # 상위 10개 창의 핸들을 정렬하여 고유 ID 생성
                sorted_windows = sorted(visible_windows[:10])
                desktop_id = "desktop_" + "_".join([str(hwnd % 10000) for hwnd in sorted_windows])
                return desktop_id

            return "desktop_empty"

        except Exception as e:
            self.logger.debug(f"데스크톱 ID 가져오기 실패: {str(e)}")
            return None

    def _handle_desktop_switch(self, direction: str) -> None:
        """데스크톱 전환 처리 - 고정된 창들만 이동"""
        try:
            self.logger.info(f"가상 데스크톱 전환 처리 시작: {direction}")

            # alt_down 키는 포커스 창을 메인 모니터 중앙으로 이동
            if direction == 'alt_down':
                self._handle_center_window()
                return

            # down 키는 즉시 창 이동 (데스크톱 전환 없음)
            if direction == 'down':
                self._handle_immediate_window_move()
                return

            # 현재 데스크톱 ID 확인
            current_desktop_id = self._get_current_desktop_id()

            # 같은 데스크톱에서 연속 실행 방지
            if (current_desktop_id and
                current_desktop_id == self._last_desktop_id and
                self._last_desktop_id is not None):
                self.logger.info(f"같은 데스크톱({current_desktop_id[:20]}...)에서 연속 실행 - 무시")
                return

            # 고정된 창 목록 확인
            pinned_windows = self.window_manager.get_pinned_windows()

            if pinned_windows:
                self.logger.info(f"고정된 창 {len(pinned_windows)}개 감지")

                # 가상 데스크톱 전환 완료 대기
                time.sleep(0.8)

                # 데스크톱 전환 후 ID 다시 확인
                new_desktop_id = self._get_current_desktop_id()

                # 실제로 데스크톱이 변경되었는지 확인
                if new_desktop_id and new_desktop_id != current_desktop_id:
                    self.logger.info(f"데스크톱 변경 확인: {current_desktop_id[:20]}... -> {new_desktop_id[:20]}...")

                    # 고정된 창들을 현재 데스크톱으로 이동
                    moved_count = self.window_manager.move_pinned_windows_to_current_desktop()

                    if moved_count > 0:
                        self.logger.info(f"고정된 창 {moved_count}개를 현재 데스크톱으로 이동 완료")
                        self._last_desktop_id = new_desktop_id
                        # 성공적으로 이동한 후 추가 쿨다운 적용
                        self._last_action_time = time.time()
                    else:
                        self.logger.warning("고정된 창 이동에 실패했습니다")
                else:
                    self.logger.info("데스크톱 변경이 감지되지 않음 - 창 이동 생략")
                    # 데스크톱 ID 업데이트
                    if new_desktop_id:
                        self._last_desktop_id = new_desktop_id

            else:
                self.logger.debug("고정된 창이 없어 이동할 창이 없음")
                # 데스크톱 ID는 업데이트
                if current_desktop_id:
                    self._last_desktop_id = current_desktop_id

        except Exception as e:
            self.logger.error(f"데스크톱 전환 처리 중 오류: {str(e)}")

    def _handle_immediate_window_move(self) -> None:
        """즉시 고정된 창들을 현재 데스크톱으로 이동 (Win+Ctrl+Down)"""
        try:
            self.logger.info("즉시 창 이동 요청 (Win+Ctrl+Down)")

            # 고정된 창 목록 확인
            pinned_windows = self.window_manager.get_pinned_windows()

            if not pinned_windows:
                self.logger.info("고정된 창이 없어 이동할 창이 없음")
                return

            self.logger.info(f"고정된 창 {len(pinned_windows)}개를 현재 데스크톱으로 즉시 이동")

            # 고정된 창들을 현재 데스크톱으로 이동
            moved_count = self.window_manager.move_pinned_windows_to_current_desktop()

            if moved_count > 0:
                self.logger.info(f"고정된 창 {moved_count}개를 현재 데스크톱으로 이동 완료")
            else:
                self.logger.warning("고정된 창 이동에 실패했습니다")

        except Exception as e:
            self.logger.error(f"즉시 창 이동 처리 중 오류: {str(e)}")

    def _handle_center_window(self) -> None:
        """포커스 창을 메인 모니터 중앙으로 이동 및 크기 조정 (Win+Ctrl+Alt+Down)"""
        try:
            import win32gui
            import win32con

            self.logger.info("포커스 창 중앙 이동 요청 (Win+Ctrl+Alt+Down)")

            # 현재 포커스 창 가져오기
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                self.logger.warning("포커스된 창이 없음")
                return

            # 창 정보 가져오기
            from .windows_api import WindowsAPIWrapper
            api = WindowsAPIWrapper()
            window_info = api.get_window_info(hwnd)

            if not window_info:
                self.logger.warning(f"창 정보를 가져올 수 없음 (hwnd: {hwnd})")
                return

            self.logger.info(f"포커스 창: {window_info.title} (hwnd: {hwnd})")

            # 메인 모니터 정보 가져오기
            primary_monitor = self.monitor_manager.get_primary_monitor()
            if not primary_monitor:
                self.logger.error("메인 모니터를 찾을 수 없음")
                return

            # 목표 크기
            target_width = 1500
            target_height = 1392

            # 메인 모니터 중앙 좌표 계산
            center_x = primary_monitor.x + (primary_monitor.width - target_width) // 2
            center_y = primary_monitor.y + (primary_monitor.height - target_height) // 2

            self.logger.info(f"메인 모니터: {primary_monitor.width}x{primary_monitor.height} at ({primary_monitor.x}, {primary_monitor.y})")
            self.logger.info(f"목표 위치: ({center_x}, {center_y}), 크기: {target_width}x{target_height}")

            # 창이 최소화되어 있으면 복원
            if window_info.state == window_info.state.MINIMIZED:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.1)

            # 창 위치 및 크기 설정
            result = win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOP,
                center_x,
                center_y,
                target_width,
                target_height,
                win32con.SWP_SHOWWINDOW
            )

            if result:
                self.logger.info(f"창을 메인 모니터 중앙으로 이동 완료: '{window_info.title}'")
            else:
                self.logger.warning(f"창 이동 실패: '{window_info.title}'")

        except Exception as e:
            self.logger.error(f"포커스 창 중앙 이동 처리 중 오류: {str(e)}")

    def set_target_monitor(self, monitor_index: int) -> bool:
        """대상 모니터 변경"""
        monitor = self.monitor_manager.get_monitor_by_index(monitor_index)
        if monitor:
            self.target_monitor_index = monitor_index
            self.logger.info(f"대상 모니터 변경: {monitor_index}")
            return True
        else:
            self.logger.warning(f"유효하지 않은 모니터 인덱스: {monitor_index}")
            return False

    def is_enabled(self) -> bool:
        """활성화 상태 반환"""
        return self._enabled

    def get_status(self) -> dict:
        """현재 상태 정보 반환"""
        window_status = self.window_manager.get_status()

        return {
            'enabled': self._enabled,
            'hotkey_listener_running': self.hotkey_listener.is_running(),
            'monitor_count': len(self.monitor_manager.get_monitors()),
            'pinned_windows': window_status
        }

    def get_window_manager(self) -> SelectiveWindowManager:
        """창 관리자 반환 (UI에서 사용)"""
        return self.window_manager