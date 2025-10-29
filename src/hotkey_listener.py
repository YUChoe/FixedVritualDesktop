"""
키보드 이벤트 감지 시스템 - 최소 기능 구현
"""
from pynput import keyboard
from typing import Callable, Optional
import threading
from .logger import get_logger


class HotkeyListener:
    """핫키 리스너 클래스"""

    def __init__(self):
        self.logger = get_logger("HotkeyListener")
        self._listener: Optional[keyboard.Listener] = None
        self._callback: Optional[Callable] = None
        self._pressed_keys = set()
        self._running = False

    def set_callback(self, callback: Callable[[str], None]) -> None:
        """핫키 감지 시 호출할 콜백 함수 설정"""
        self._callback = callback

    def start(self) -> bool:
        """핫키 리스닝 시작"""
        if self._running:
            return True

        try:
            self._listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._listener.start()
            self._running = True
            self.logger.info("핫키 리스너 시작됨")
            return True

        except Exception as e:
            self.logger.error(f"핫키 리스너 시작 실패: {str(e)}")
            return False

    def stop(self) -> None:
        """핫키 리스닝 중지"""
        if self._listener and self._running:
            self._listener.stop()
            self._running = False
            self._pressed_keys.clear()
            self.logger.info("핫키 리스너 중지됨")

    def _on_key_press(self, key) -> None:
        """키 눌림 이벤트 처리"""
        try:
            # 특수 키 처리
            if hasattr(key, 'name'):
                key_name = key.name
            elif hasattr(key, 'vk'):
                key_name = f'vk_{key.vk}'
            else:
                key_name = str(key).replace("'", "")

            self._pressed_keys.add(key_name)

            # Win + Ctrl + Left/Right 조합 감지
            if self._is_target_combination():
                direction = 'left' if 'left' in self._pressed_keys else 'right'
                if self._callback:
                    self._callback(direction)
                    self.logger.info(f"핫키 감지: Win+Ctrl+{direction}")

        except Exception as e:
            self.logger.error(f"키 눌림 처리 중 오류: {str(e)}")

    def _on_key_release(self, key) -> None:
        """키 놓음 이벤트 처리"""
        try:
            if hasattr(key, 'name'):
                key_name = key.name
            elif hasattr(key, 'vk'):
                key_name = f'vk_{key.vk}'
            else:
                key_name = str(key).replace("'", "")

            self._pressed_keys.discard(key_name)

        except Exception as e:
            self.logger.error(f"키 놓음 처리 중 오류: {str(e)}")

    def _is_target_combination(self) -> bool:
        """목표 키 조합인지 확인 (Win + Ctrl + Left/Right)"""
        # Windows 키 확인 (cmd 또는 cmd_l, cmd_r)
        has_win = any(k in self._pressed_keys for k in ['cmd', 'cmd_l', 'cmd_r'])

        # Ctrl 키 확인
        has_ctrl = any(k in self._pressed_keys for k in ['ctrl', 'ctrl_l', 'ctrl_r'])

        # 방향키 확인
        has_arrow = any(k in self._pressed_keys for k in ['left', 'right'])

        return has_win and has_ctrl and has_arrow

    def is_running(self) -> bool:
        """리스너 실행 상태 반환"""
        return self._running