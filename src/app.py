"""
메인 애플리케이션 클래스
"""
import threading
import time
from typing import Optional
from .config_manager import ConfigManager
from .virtual_desktop_controller import VirtualDesktopController
from .system_tray import SystemTrayIcon, SettingsDialog, WindowManagementDialog
from .logger import get_logger_manager, get_logger


class VirtualDesktopApp:
    """메인 애플리케이션 클래스"""

    def __init__(self):
        # 로거 초기화
        self.logger_manager = get_logger_manager()
        self.logger = get_logger("VirtualDesktopApp")

        # 컴포넌트 초기화
        self.config_manager = ConfigManager()
        self.controller: Optional[VirtualDesktopController] = None
        self.tray_icon: Optional[SystemTrayIcon] = None
        self.settings_dialog: Optional[SettingsDialog] = None
        self.window_dialog: Optional[WindowManagementDialog] = None

        self._running = False

        # 초기 설정 로드
        self._load_initial_config()

        self.logger.info("VirtualDesktopApp 초기화 완료")

    def _load_initial_config(self) -> None:
        """초기 설정 로드"""
        try:
            config = self.config_manager.get_config()

            # 로그 레벨 설정
            self.logger_manager.set_log_level(config.log_level)

            # 컨트롤러 초기화
            self.controller = VirtualDesktopController(
                target_monitor_index=config.target_monitor_index
            )

            self.logger.info(f"초기 설정 로드 완료 - 대상 모니터: {config.target_monitor_index}")

        except Exception as e:
            self.logger.error(f"초기 설정 로드 실패: {str(e)}")

    def start(self) -> bool:
        """애플리케이션 시작"""
        try:
            if self._running:
                return True

            # 시스템 정보 로깅
            self.logger_manager.log_system_info()

            # 트레이 아이콘 초기화
            self.tray_icon = SystemTrayIcon()
            self.tray_icon.set_callbacks(
                toggle_callback=self._on_toggle,
                settings_callback=self._on_settings,
                window_management_callback=self._on_window_management,
                exit_callback=self._on_exit
            )

            # 설정 대화상자 초기화
            if self.tray_icon.start():
                self.settings_dialog = SettingsDialog(self.tray_icon.root)
                self.settings_dialog.set_config_callback(self._on_config_changed)

                self.window_dialog = WindowManagementDialog(self.tray_icon.root)

                # 초기 상태 설정
                config = self.config_manager.get_config()
                if config.enabled:
                    self._start_controller()

                self._running = True
                self.logger.info("애플리케이션 시작 완료")
                return True
            else:
                self.logger.error("트레이 아이콘 시작 실패")
                return False

        except Exception as e:
            self.logger.error(f"애플리케이션 시작 실패: {str(e)}")
            return False

    def run(self) -> None:
        """애플리케이션 메인 루프 실행"""
        if self.tray_icon and self._running:
            self.logger.info("애플리케이션 메인 루프 시작")
            self.tray_icon.run()

    def stop(self) -> None:
        """애플리케이션 중지"""
        try:
            if not self._running:
                return

            self._running = False

            # 컨트롤러 중지
            if self.controller and self.controller.is_enabled():
                self.controller.stop()

            # 트레이 아이콘 중지
            if self.tray_icon:
                self.tray_icon.stop()

            self.logger.info("애플리케이션 중지 완료")

        except Exception as e:
            self.logger.error(f"애플리케이션 중지 중 오류: {str(e)}")

    def _start_controller(self) -> bool:
        """컨트롤러 시작"""
        if self.controller and not self.controller.is_enabled():
            if self.controller.start():
                if self.tray_icon:
                    self.tray_icon.update_status(True)
                self.logger.info("가상 데스크톱 제어 활성화")
                return True
        return False

    def _stop_controller(self) -> None:
        """컨트롤러 중지"""
        if self.controller and self.controller.is_enabled():
            self.controller.stop()
            if self.tray_icon:
                self.tray_icon.update_status(False)
            self.logger.info("가상 데스크톱 제어 비활성화")

    def _on_toggle(self) -> None:
        """토글 버튼 클릭 처리"""
        try:
            if self.controller and self.controller.is_enabled():
                self._stop_controller()
                # 설정에 상태 저장
                self.config_manager.update_config(enabled=False)
            else:
                if self._start_controller():
                    # 설정에 상태 저장
                    self.config_manager.update_config(enabled=True)

        except Exception as e:
            self.logger.error(f"토글 처리 중 오류: {str(e)}")

    def _on_window_management(self) -> None:
        """창 관리 버튼 클릭 처리"""
        try:
            if self.window_dialog and self.controller:
                window_manager = self.controller.get_window_manager()
                self.window_dialog.show(window_manager)
        except Exception as e:
            self.logger.error(f"창 관리 대화상자 표시 중 오류: {str(e)}")

    def _on_settings(self) -> None:
        """설정 버튼 클릭 처리"""
        try:
            if self.settings_dialog:
                current_config = self.config_manager.get_config().to_dict()
                self.settings_dialog.show(current_config)
        except Exception as e:
            self.logger.error(f"설정 대화상자 표시 중 오류: {str(e)}")

    def _on_config_changed(self, new_config: dict) -> None:
        """설정 변경 처리"""
        try:
            # 설정 업데이트
            self.config_manager.update_config(**new_config)

            # 로그 레벨 변경 적용
            if 'log_level' in new_config:
                self.logger_manager.set_log_level(new_config['log_level'])

            # 대상 모니터 변경 적용
            if 'target_monitor_index' in new_config and self.controller:
                self.controller.set_target_monitor(new_config['target_monitor_index'])

            self.logger.info("설정 변경 적용 완료")

        except Exception as e:
            self.logger.error(f"설정 변경 적용 중 오류: {str(e)}")

    def _on_exit(self) -> None:
        """종료 처리"""
        self.logger.info("애플리케이션 종료 요청")
        self.stop()

    def is_running(self) -> bool:
        """실행 상태 반환"""
        return self._running

    def get_status(self) -> dict:
        """애플리케이션 상태 반환"""
        controller_status = self.controller.get_status() if self.controller else {}

        return {
            'app_running': self._running,
            'controller_status': controller_status,
            'config': self.config_manager.get_config().to_dict()
        }