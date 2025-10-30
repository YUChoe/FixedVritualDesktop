"""
가상 데스크톱 제어 시스템 - 선택적 창 고정 기능
"""
from typing import Callable, Optional
import time
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
        self._action_cooldown = 1.0  # 1초 쿨다운

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

        # 쿨다운 체크
        current_time = time.time()
        if current_time - self._last_action_time < self._action_cooldown:
            return

        self._last_action_time = current_time

        try:
            self.logger.info(f"가상 데스크톱 전환 감지: {direction}")
            self._handle_desktop_switch(direction)
        except Exception as e:
            self.logger.error(f"데스크톱 전환 처리 중 오류: {str(e)}")

    def _handle_desktop_switch(self, direction: str) -> None:
        """데스크톱 전환 처리 - 고정된 창들만 이동"""
        try:
            self.logger.info(f"가상 데스크톱 전환 처리 시작: {direction}")

            # 고정된 창 목록 확인
            pinned_windows = self.window_manager.get_pinned_windows()

            if pinned_windows:
                self.logger.info(f"고정된 창 {len(pinned_windows)}개 감지")

                # 가상 데스크톱 전환 완료 대기
                time.sleep(0.8)

                # 고정된 창들을 현재 데스크톱으로 이동
                moved_count = self.window_manager.move_pinned_windows_to_current_desktop()

                if moved_count > 0:
                    self.logger.info(f"고정된 창 {moved_count}개를 현재 데스크톱으로 이동 완료")
                else:
                    self.logger.warning("고정된 창 이동에 실패했습니다")
            else:
                self.logger.debug("고정된 창이 없어 이동할 창이 없음")

        except Exception as e:
            self.logger.error(f"데스크톱 전환 처리 중 오류: {str(e)}")

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