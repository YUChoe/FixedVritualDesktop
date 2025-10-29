"""
로깅 유틸리티

파일 기반 로깅 시스템과 로그 레벨별 메시지 분류 및 저장 기능을 제공합니다.
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class LoggerManager:
    """로깅 관리 클래스"""

    def __init__(self, log_dir: str = "logs", app_name: str = "VirtualDesktopApp"):
        self.log_dir = Path(log_dir)
        self.app_name = app_name
        self.logger = None

        # 로그 디렉토리 생성
        self.log_dir.mkdir(exist_ok=True)

        # 로거 초기화
        self._setup_logger()

    def _setup_logger(self) -> None:
        """로거 설정 및 초기화"""
        # 메인 로거 생성
        self.logger = logging.getLogger(self.app_name)
        self.logger.setLevel(logging.DEBUG)

        # 기존 핸들러 제거 (중복 방지)
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # 로그 포맷 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 파일 핸들러 설정 (일별 로테이션)
        log_file = self.log_dir / f"{self.app_name}.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when='midnight',
            interval=1,
            backupCount=30,  # 30일간 보관
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # 에러 전용 파일 핸들러
        error_log_file = self.log_dir / f"{self.app_name}_error.log"
        error_handler = logging.handlers.TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)

        # 콘솔 핸들러 설정 (개발 시에만)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # 핸들러 추가
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)

        # 로거 전파 방지 (중복 로그 방지)
        self.logger.propagate = False

    def set_log_level(self, level: str) -> None:
        """로그 레벨 설정"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        if level.upper() in level_map:
            self.logger.setLevel(level_map[level.upper()])
            # 콘솔 핸들러의 레벨도 조정
            for handler in self.logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setLevel(level_map[level.upper()])
        else:
            self.logger.warning(f"알 수 없는 로그 레벨: {level}")

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """로거 인스턴스 반환"""
        if name:
            return logging.getLogger(f"{self.app_name}.{name}")
        return self.logger

    def debug(self, message: str) -> None:
        """디버그 메시지 로깅"""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """정보 메시지 로깅"""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """경고 메시지 로깅"""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False) -> None:
        """오류 메시지 로깅"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False) -> None:
        """치명적 오류 메시지 로깅"""
        self.logger.critical(message, exc_info=exc_info)

    def log_exception(self, message: str, exception: Exception) -> None:
        """예외 정보와 함께 오류 로깅"""
        self.logger.error(f"{message}: {str(exception)}", exc_info=True)

    def log_system_info(self) -> None:
        """시스템 정보 로깅"""
        import platform
        import sys

        self.info("=== 시스템 정보 ===")
        self.info(f"운영체제: {platform.system()} {platform.release()}")
        self.info(f"Python 버전: {sys.version}")
        self.info(f"애플리케이션: {self.app_name}")
        self.info(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info("==================")

    def cleanup_old_logs(self, days: int = 30) -> None:
        """오래된 로그 파일 정리"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            for log_file in self.log_dir.glob("*.log*"):
                if log_file.is_file():
                    file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        log_file.unlink()
                        self.info(f"오래된 로그 파일 삭제: {log_file.name}")
        except Exception as e:
            self.error(f"로그 파일 정리 중 오류: {str(e)}")

    def get_log_stats(self) -> dict:
        """로그 파일 통계 정보 반환"""
        stats = {
            'log_dir': str(self.log_dir),
            'files': [],
            'total_size': 0
        }

        try:
            for log_file in self.log_dir.glob("*.log*"):
                if log_file.is_file():
                    size = log_file.stat().st_size
                    stats['files'].append({
                        'name': log_file.name,
                        'size': size,
                        'modified': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                    })
                    stats['total_size'] += size
        except Exception as e:
            self.error(f"로그 통계 수집 중 오류: {str(e)}")

        return stats


# 전역 로거 인스턴스
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """전역 로거 매니저 인스턴스 반환"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """로거 인스턴스 반환 (편의 함수)"""
    return get_logger_manager().get_logger(name)