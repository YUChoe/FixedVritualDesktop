"""
선택적 창 고정 시스템

사용자가 지정한 창만 가상 데스크톱을 따라다니도록 하는 시스템
"""
import json
import time
from typing import Set, Dict, List, Optional
from pathlib import Path
from .windows_api import WindowsAPIWrapper
from .logger import get_logger


class SelectiveWindowManager:
    """선택적 창 관리 클래스"""

    def __init__(self, config_dir: str = "config"):
        self.logger = get_logger("SelectiveWindowManager")
        self.api = WindowsAPIWrapper()

        # 설정 파일 경로
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "pinned_windows.json"

        # 고정된 창 목록 (hwnd -> 창 정보)
        self._pinned_windows: Dict[int, dict] = {}

        # 설정 로드
        self._load_pinned_windows()

    def _load_pinned_windows(self):
        """고정된 창 목록 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # hwnd는 문자열로 저장되므로 정수로 변환
                    self._pinned_windows = {int(k): v for k, v in data.items()}
                self.logger.info(f"고정된 창 {len(self._pinned_windows)}개 로드")
            else:
                self._pinned_windows = {}
                self.logger.info("고정된 창 설정 파일이 없어 빈 목록으로 시작")
        except Exception as e:
            self.logger.error(f"고정된 창 목록 로드 실패: {str(e)}")
            self._pinned_windows = {}

    def _save_pinned_windows(self):
        """고정된 창 목록 저장"""
        try:
            self.config_dir.mkdir(exist_ok=True)
            # hwnd를 문자열로 변환하여 저장
            data = {str(k): v for k, v in self._pinned_windows.items()}
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"고정된 창 {len(self._pinned_windows)}개 저장")
            return True
        except Exception as e:
            self.logger.error(f"고정된 창 목록 저장 실패: {str(e)}")
            return False

    def add_pinned_window(self, hwnd: int) -> bool:
        """창을 고정 목록에 추가"""
        try:
            window_info = self.api.get_window_info(hwnd)
            if not window_info:
                self.logger.warning(f"창 정보를 가져올 수 없음: {hwnd}")
                return False

            # 창 정보 저장
            self._pinned_windows[hwnd] = {
                'title': window_info.title,
                'class_name': window_info.class_name,
                'process_id': window_info.process_id,
                'added_time': time.time()
            }

            self._save_pinned_windows()
            self.logger.info(f"창 고정 추가: {hwnd} '{window_info.title}'")
            return True

        except Exception as e:
            self.logger.error(f"창 고정 추가 실패: {str(e)}")
            return False

    def remove_pinned_window(self, hwnd: int) -> bool:
        """창을 고정 목록에서 제거"""
        try:
            if hwnd in self._pinned_windows:
                window_info = self._pinned_windows[hwnd]
                del self._pinned_windows[hwnd]
                self._save_pinned_windows()
                self.logger.info(f"창 고정 제거: {hwnd} '{window_info.get('title', 'Unknown')}'")
                return True
            else:
                self.logger.warning(f"고정되지 않은 창: {hwnd}")
                return False
        except Exception as e:
            self.logger.error(f"창 고정 제거 실패: {str(e)}")
            return False

    def get_pinned_windows(self) -> List[dict]:
        """고정된 창 목록 반환 (유효한 창만)"""
        valid_windows = []
        invalid_hwnds = []

        for hwnd, info in self._pinned_windows.items():
            if self.api.is_window_valid(hwnd):
                current_info = self.api.get_window_info(hwnd)
                if current_info:
                    valid_windows.append({
                        'hwnd': hwnd,
                        'title': current_info.title,
                        'class_name': current_info.class_name,
                        'process_id': current_info.process_id,
                        'x': current_info.x,
                        'y': current_info.y,
                        'width': current_info.width,
                        'height': current_info.height,
                        'is_visible': current_info.is_visible,
                        'original_info': info
                    })
                else:
                    invalid_hwnds.append(hwnd)
            else:
                invalid_hwnds.append(hwnd)

        # 유효하지 않은 창들 제거
        if invalid_hwnds:
            for hwnd in invalid_hwnds:
                del self._pinned_windows[hwnd]
            self._save_pinned_windows()
            self.logger.info(f"유효하지 않은 창 {len(invalid_hwnds)}개 제거")

        return valid_windows

    def move_pinned_windows_to_current_desktop(self) -> int:
        """고정된 창들을 현재 가상 데스크톱으로 이동"""
        pinned_windows = self.get_pinned_windows()
        moved_count = 0

        if not pinned_windows:
            self.logger.debug("고정된 창이 없음")
            return 0

        self.logger.info(f"고정된 창 {len(pinned_windows)}개를 현재 데스크톱으로 이동 시도")

        for window in pinned_windows:
            hwnd = window['hwnd']
            if self._move_window_to_current_desktop(hwnd, window):
                moved_count += 1

        self.logger.info(f"고정된 창 {moved_count}개 이동 완료")
        return moved_count

    def _move_window_to_current_desktop(self, hwnd: int, window_info: dict) -> bool:
        """개별 창을 현재 가상 데스크톱으로 이동"""
        try:
            import win32gui
            import win32con

            title = window_info.get('title', 'Unknown')
            is_fullscreen = (window_info['x'] == -32000 and window_info['y'] == -32000)

            if is_fullscreen:
                self.logger.debug(f"전체화면 고정 창 이동: {hwnd} '{title}'")

                # 전체화면 창 처리
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.2)

                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.2)
                except:
                    pass

                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)

            else:
                self.logger.debug(f"일반 고정 창 이동: {hwnd} '{title}'")

                # 일반 창 처리
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                time.sleep(0.1)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)

                try:
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.1)
                except:
                    pass

            return True

        except Exception as e:
            self.logger.error(f"고정 창 이동 실패 (hwnd: {hwnd}): {str(e)}")
            return False

    def get_current_windows_for_selection(self) -> List[dict]:
        """현재 열린 창 목록 반환 (고정 설정용)"""
        windows = []

        try:
            handles = self.api.enum_windows()
            for hwnd in handles:
                window_info = self.api.get_window_info(hwnd)
                if (window_info and window_info.is_visible and
                    window_info.title.strip() and len(window_info.title.strip()) > 0):

                    # 시스템 창 제외
                    excluded_titles = ['Program Manager', 'Windows 입력 환경', 'Desktop Window Manager']
                    if window_info.title not in excluded_titles:
                        windows.append({
                            'hwnd': hwnd,
                            'title': window_info.title,
                            'class_name': window_info.class_name,
                            'process_id': window_info.process_id,
                            'x': window_info.x,
                            'y': window_info.y,
                            'is_pinned': hwnd in self._pinned_windows
                        })

            # 제목 순으로 정렬
            windows.sort(key=lambda w: w['title'].lower())

        except Exception as e:
            self.logger.error(f"창 목록 수집 실패: {str(e)}")

        return windows

    def get_status(self) -> dict:
        """현재 상태 반환"""
        pinned_windows = self.get_pinned_windows()

        return {
            'pinned_count': len(pinned_windows),
            'pinned_windows': [
                {
                    'hwnd': w['hwnd'],
                    'title': w['title'],
                    'is_visible': w['is_visible']
                }
                for w in pinned_windows
            ],
            'config_file': str(self.config_file)
        }