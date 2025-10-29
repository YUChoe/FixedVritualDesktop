"""
가상 데스크톱 제어 시스템 - 최소 기능 구현
"""
from typing import Callable, Optional
import time
from .monitor_manager import MonitorManager
from .window_manager import WindowManager
from .hotkey_listener import HotkeyListener
from .logger import get_logger


class VirtualDesktopController:
    """가상 데스크톱 제어 클래스"""

    def __init__(self, target_monitor_index: int = 1):
        """
        Args:
            target_monitor_index: 창을 고정할 대상 모니터 인덱스 (0: 주모니터, 1+: 보조모니터)
        """
        self.logger = get_logger("VirtualDesktopController")
        self.target_monitor_index = target_monitor_index

        # 매니저 초기화
        self.monitor_manager = MonitorManager()
        self.window_manager = WindowManager()
        self.hotkey_listener = HotkeyListener()

        # 핫키 콜백 설정
        self.hotkey_listener.set_callback(self._on_hotkey_pressed)

        self._enabled = False
        self._last_action_time = 0
        self._action_cooldown = 1.0  # 1초 쿨다운

    def start(self) -> bool:
        """가상 데스크톱 제어 시작"""
        try:
            if self.hotkey_listener.start():
                self._enabled = True
                self.logger.info(f"가상 데스크톱 제어 시작 (대상 모니터: {self.target_monitor_index})")
                return True
            return False
        except Exception as e:
            self.logger.error(f"가상 데스크톱 제어 시작 실패: {str(e)}")
            return False

    def stop(self) -> None:
        """가상 데스크톱 제어 중지"""
        self._enabled = False
        self.hotkey_listener.stop()
        self.logger.info("가상 데스크톱 제어 중지")

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
        """데스크톱 전환 처리"""
        # 대상 모니터 확인
        target_monitor = self.monitor_manager.get_monitor_by_index(self.target_monitor_index)
        if not target_monitor:
            self.logger.warning(f"대상 모니터 {self.target_monitor_index}를 찾을 수 없음")
            return

        # 대상 모니터의 창들 상태 저장
        saved_count = self.window_manager.save_monitor_windows(target_monitor.handle)

        if saved_count > 0:
            self.logger.info(f"모니터 {self.target_monitor_index}의 창 {saved_count}개 고정 처리")

            # 잠시 대기 후 복원 (가상 데스크톱 전환 완료 대기)
            time.sleep(0.5)

            # 창 상태 복원
            restored_count = self.window_manager.restore_monitor_windows(target_monitor.handle)
            self.logger.info(f"창 {restored_count}개 복원 완료")
        else:
            self.logger.debug("고정할 창이 없음")

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
        target_monitor = self.monitor_manager.get_monitor_by_index(self.target_monitor_index)

        return {
            'enabled': self._enabled,
            'target_monitor_index': self.target_monitor_index,
            'target_monitor_name': target_monitor.device_name if target_monitor else None,
            'hotkey_listener_running': self.hotkey_listener.is_running(),
            'monitor_count': len(self.monitor_manager.get_monitors())
        }