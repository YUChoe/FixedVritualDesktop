"""
키보드 이벤트 감지 시스템 - 최소 기능 구현
"""
from pynput import keyboard
from typing import Callable, Optional
import threading
import time
from .logger import get_logger


class HotkeyListener:
    """핫키 리스너 클래스"""

    def __init__(self):
        self.logger = get_logger("HotkeyListener")
        self._listener: Optional[keyboard.Listener] = None
        self._callback: Optional[Callable] = None
        self._pressed_keys = set()
        self._running = False

        # 중복 감지 방지
        self._last_trigger_time = 0
        self._trigger_cooldown = 1.0  # 1초 쿨다운 (더 강력한 중복 방지)
        self._last_combination = None

        # 키 상태 추적 (키 반복 방지)
        self._key_states = {}  # 키별 마지막 이벤트 시간
        self._key_repeat_threshold = 0.1  # 100ms 내 같은 키 이벤트 무시

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
            self._key_states.clear()
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

            current_time = time.time()

            # 키 반복 방지 - 같은 키가 짧은 시간 내에 반복되면 무시
            if key_name in self._key_states:
                if current_time - self._key_states[key_name] < self._key_repeat_threshold:
                    return  # 키 반복 무시

            self._key_states[key_name] = current_time

            # 키가 이미 눌린 상태라면 무시 (키 반복 방지)
            if key_name in self._pressed_keys:
                return

            self._pressed_keys.add(key_name)

            # 방향키가 새로 눌렸을 때만 핫키 조합 확인
            if key_name in ['left', 'right', 'down']:
                self.logger.debug(f"방향키 눌림: {key_name}, 현재 키들: {sorted(self._pressed_keys)}")

                if self._is_target_combination():
                    # Alt 키 확인
                    has_alt = any(k in self._pressed_keys for k in ['alt', 'alt_l', 'alt_r'])

                    # Win+Ctrl+Alt+Down 조합인지 확인
                    if has_alt and key_name == 'down':
                        direction = 'alt_down'
                    else:
                        direction = key_name  # 방금 눌린 방향키 사용

                    current_combination = f"win_ctrl_{direction}"

                    # 중복 감지 방지
                    if (current_time - self._last_trigger_time > self._trigger_cooldown or
                        current_combination != self._last_combination):

                        if self._callback:
                            self._callback(direction)
                            if direction == 'alt_down':
                                self.logger.info(f"핫키 감지: Win+Ctrl+Alt+Down")
                            else:
                                self.logger.info(f"핫키 감지: Win+Ctrl+{direction}")

                        self._last_trigger_time = current_time
                        self._last_combination = current_combination
                    else:
                        self.logger.debug(f"핫키 중복 감지 방지: {direction} (쿨다운 {self._trigger_cooldown}초)")

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

            # 키 상태에서도 제거
            if key_name in self._key_states:
                del self._key_states[key_name]

        except Exception as e:
            self.logger.error(f"키 놓음 처리 중 오류: {str(e)}")

    def _is_target_combination(self) -> bool:
        """목표 키 조합인지 확인 (Win + Ctrl + Left/Right/Down 또는 Win + Ctrl + Alt + Down)"""
        # Windows 키 확인 (cmd 또는 cmd_l, cmd_r)
        has_win = any(k in self._pressed_keys for k in ['cmd', 'cmd_l', 'cmd_r'])

        # Ctrl 키 확인
        has_ctrl = any(k in self._pressed_keys for k in ['ctrl', 'ctrl_l', 'ctrl_r'])

        # Alt 키 확인
        has_alt = any(k in self._pressed_keys for k in ['alt', 'alt_l', 'alt_r'])

        # 방향키 확인 (정확히 하나의 방향키만)
        has_left = 'left' in self._pressed_keys
        has_right = 'right' in self._pressed_keys
        has_down = 'down' in self._pressed_keys

        # 방향키가 하나만 눌렸을 때만 유효
        arrow_count = sum([has_left, has_right, has_down])
        has_single_arrow = arrow_count == 1

        # Win + Ctrl + Alt + Down 조합 확인
        if has_win and has_ctrl and has_alt and has_down:
            self.logger.debug(f"키 조합 확인: Win+Ctrl+Alt+Down")
            return True

        # Win + Ctrl + Left/Right/Down 조합 확인 (Alt 없음)
        result = has_win and has_ctrl and not has_alt and has_single_arrow

        if result:
            if has_left:
                direction = 'left'
            elif has_right:
                direction = 'right'
            else:
                direction = 'down'
            self.logger.debug(f"키 조합 확인: Win={has_win}, Ctrl={has_ctrl}, Arrow={direction}")

        return result

    def is_running(self) -> bool:
        """리스너 실행 상태 반환"""
        return self._running