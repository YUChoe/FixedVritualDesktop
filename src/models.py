"""
가상 데스크톱 모니터 제어 애플리케이션의 핵심 데이터 모델
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum


class WindowState(Enum):
    """창 상태 열거형"""
    NORMAL = "normal"
    MINIMIZED = "minimized"
    MAXIMIZED = "maximized"
    HIDDEN = "hidden"


@dataclass
class WindowInfo:
    """창 정보를 저장하는 데이터 클래스"""
    hwnd: int  # 창 핸들
    title: str  # 창 제목
    class_name: str  # 창 클래스명
    process_id: int  # 프로세스 ID
    x: int  # X 좌표
    y: int  # Y 좌표
    width: int  # 너비
    height: int  # 높이
    state: WindowState  # 창 상태
    monitor_handle: int  # 모니터 핸들
    is_visible: bool  # 가시성 여부

    def __post_init__(self):
        """초기화 후 검증"""
        if self.hwnd <= 0:
            raise ValueError("유효하지 않은 창 핸들")
        if self.width < 0 or self.height < 0:
            raise ValueError("창 크기는 음수일 수 없습니다")


@dataclass
class MonitorInfo:
    """모니터 정보를 저장하는 데이터 클래스"""
    handle: int  # 모니터 핸들
    device_name: str  # 디바이스 이름
    x: int  # X 좌표
    y: int  # Y 좌표
    width: int  # 너비
    height: int  # 높이
    is_primary: bool  # 주 모니터 여부

    def __post_init__(self):
        """초기화 후 검증"""
        if self.handle <= 0:
            raise ValueError("유효하지 않은 모니터 핸들")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("모니터 크기는 양수여야 합니다")

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """모니터 경계 반환 (x, y, right, bottom)"""
        return (self.x, self.y, self.x + self.width, self.y + self.height)


@dataclass
class AppConfig:
    """애플리케이션 설정을 저장하는 데이터 클래스"""
    enabled: bool = True  # 기능 활성화 여부
    target_monitor_index: int = 1  # 대상 모니터 인덱스 (0: 주모니터, 1: 서브모니터)
    hotkey_enabled: bool = True  # 핫키 활성화 여부
    log_level: str = "INFO"  # 로그 레벨
    auto_start: bool = False  # 자동 시작 여부
    window_filters: List[str] = None  # 창 필터 목록

    def __post_init__(self):
        """초기화 후 기본값 설정 및 검증"""
        if self.window_filters is None:
            self.window_filters = []

        if self.target_monitor_index < 0:
            raise ValueError("모니터 인덱스는 0 이상이어야 합니다")

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"로그 레벨은 {valid_log_levels} 중 하나여야 합니다")

    def to_dict(self) -> Dict:
        """딕셔너리로 변환"""
        return {
            "enabled": self.enabled,
            "target_monitor_index": self.target_monitor_index,
            "hotkey_enabled": self.hotkey_enabled,
            "log_level": self.log_level,
            "auto_start": self.auto_start,
            "window_filters": self.window_filters
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'AppConfig':
        """딕셔너리에서 생성"""
        return cls(
            enabled=data.get("enabled", True),
            target_monitor_index=data.get("target_monitor_index", 1),
            hotkey_enabled=data.get("hotkey_enabled", True),
            log_level=data.get("log_level", "INFO"),
            auto_start=data.get("auto_start", False),
            window_filters=data.get("window_filters", [])
        )