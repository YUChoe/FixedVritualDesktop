"""
전역 예외 처리 및 안정성 강화
"""
import sys
import traceback
import threading
from typing import Optional, Callable
from .logger import get_logger


class GlobalExceptionHandler:
    """전역 예외 처리 클래스"""

    def __init__(self):
        self.logger = get_logger("GlobalExceptionHandler")
        self._original_excepthook = sys.excepthook
        self._crash_callback: Optional[Callable] = None

    def install(self) -> None:
        """전역 예외 처리기 설치"""
        sys.excepthook = self._handle_exception
        threading.excepthook = self._handle_thread_exception
        self.logger.info("전역 예외 처리기 설치 완료")

    def uninstall(self) -> None:
        """전역 예외 처리기 제거"""
        sys.excepthook = self._original_excepthook
        self.logger.info("전역 예외 처리기 제거 완료")

    def set_crash_callback(self, callback: Callable) -> None:
        """크래시 발생 시 호출할 콜백 설정"""
        self._crash_callback = callback

    def _handle_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """메인 스레드 예외 처리"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Ctrl+C는 정상적인 종료로 처리
            self.logger.info("키보드 인터럽트로 종료")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 치명적 오류 로깅
        error_msg = f"치명적 오류 발생: {exc_type.__name__}: {exc_value}"
        self.logger.critical(error_msg, exc_info=True)

        # 트레이스백 정보 로깅
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in tb_lines:
            self.logger.critical(line.rstrip())

        # 크래시 콜백 호출
        if self._crash_callback:
            try:
                self._crash_callback(exc_type, exc_value, exc_traceback)
            except Exception as e:
                self.logger.error(f"크래시 콜백 실행 중 오류: {str(e)}")

        # 원래 예외 처리기 호출
        self._original_excepthook(exc_type, exc_value, exc_traceback)

    def _handle_thread_exception(self, args) -> None:
        """스레드 예외 처리"""
        exc_type, exc_value, exc_traceback, thread = args

        error_msg = f"스레드 '{thread.name}'에서 예외 발생: {exc_type.__name__}: {exc_value}"
        self.logger.error(error_msg, exc_info=(exc_type, exc_value, exc_traceback))


class SafeExecutor:
    """안전한 실행을 위한 유틸리티 클래스"""

    def __init__(self, logger_name: str = "SafeExecutor"):
        self.logger = get_logger(logger_name)

    def safe_call(self, func: Callable, *args, default=None, **kwargs):
        """안전한 함수 호출"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"함수 '{func.__name__}' 실행 중 오류: {str(e)}")
            return default

    def safe_thread_call(self, func: Callable, *args, **kwargs) -> Optional[threading.Thread]:
        """안전한 스레드 실행"""
        def wrapper():
            try:
                func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"스레드 함수 '{func.__name__}' 실행 중 오류: {str(e)}")

        try:
            thread = threading.Thread(target=wrapper, daemon=True)
            thread.start()
            return thread
        except Exception as e:
            self.logger.error(f"스레드 시작 실패: {str(e)}")
            return None


# 전역 인스턴스
_global_exception_handler: Optional[GlobalExceptionHandler] = None


def get_exception_handler() -> GlobalExceptionHandler:
    """전역 예외 처리기 인스턴스 반환"""
    global _global_exception_handler
    if _global_exception_handler is None:
        _global_exception_handler = GlobalExceptionHandler()
    return _global_exception_handler


def install_global_exception_handler(crash_callback: Callable = None) -> None:
    """전역 예외 처리기 설치 (편의 함수)"""
    handler = get_exception_handler()
    if crash_callback:
        handler.set_crash_callback(crash_callback)
    handler.install()


def uninstall_global_exception_handler() -> None:
    """전역 예외 처리기 제거 (편의 함수)"""
    handler = get_exception_handler()
    handler.uninstall()


class ResourceManager:
    """리소스 정리 및 메모리 관리 클래스"""

    def __init__(self):
        self.logger = get_logger("ResourceManager")
        self._cleanup_callbacks = []
        self._resources = {}

    def register_cleanup(self, callback: Callable, name: str = None) -> None:
        """정리 콜백 등록"""
        callback_name = name or callback.__name__
        self._cleanup_callbacks.append((callback_name, callback))
        self.logger.debug(f"정리 콜백 등록: {callback_name}")

    def register_resource(self, name: str, resource, cleanup_func: Callable = None) -> None:
        """리소스 등록"""
        self._resources[name] = {
            'resource': resource,
            'cleanup_func': cleanup_func
        }
        self.logger.debug(f"리소스 등록: {name}")

    def cleanup_all(self) -> None:
        """모든 리소스 정리"""
        self.logger.info("리소스 정리 시작")

        # 등록된 리소스 정리
        for name, resource_info in self._resources.items():
            try:
                resource = resource_info['resource']
                cleanup_func = resource_info['cleanup_func']

                if cleanup_func:
                    cleanup_func(resource)
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, 'cleanup'):
                    resource.cleanup()
                elif hasattr(resource, 'stop'):
                    resource.stop()

                self.logger.debug(f"리소스 정리 완료: {name}")

            except Exception as e:
                self.logger.error(f"리소스 '{name}' 정리 중 오류: {str(e)}")

        # 정리 콜백 실행
        for callback_name, callback in self._cleanup_callbacks:
            try:
                callback()
                self.logger.debug(f"정리 콜백 실행 완료: {callback_name}")
            except Exception as e:
                self.logger.error(f"정리 콜백 '{callback_name}' 실행 중 오류: {str(e)}")

        # 리소스 목록 초기화
        self._resources.clear()
        self._cleanup_callbacks.clear()

        self.logger.info("리소스 정리 완료")

    def get_memory_usage(self) -> dict:
        """메모리 사용량 정보 반환"""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()

            return {
                'rss': memory_info.rss,  # 물리 메모리 사용량
                'vms': memory_info.vms,  # 가상 메모리 사용량
                'percent': process.memory_percent(),  # 메모리 사용률
                'available': psutil.virtual_memory().available
            }
        except ImportError:
            # psutil이 없는 경우 기본 정보만 반환
            import gc
            return {
                'gc_objects': len(gc.get_objects()),
                'gc_collections': gc.get_count()
            }
        except Exception as e:
            self.logger.error(f"메모리 정보 수집 중 오류: {str(e)}")
            return {}


# 전역 리소스 매니저
_resource_manager: Optional[ResourceManager] = None


def get_resource_manager() -> ResourceManager:
    """전역 리소스 매니저 인스턴스 반환"""
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager()
    return _resource_manager