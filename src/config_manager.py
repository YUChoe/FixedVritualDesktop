"""
설정 관리 시스템 - 최소 기능 구현
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from .models import AppConfig
from .logger import get_logger


class ConfigManager:
    """설정 관리 클래스"""

    def __init__(self, config_dir: str = "config"):
        self.logger = get_logger("ConfigManager")
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "app_config.json"

        # 설정 디렉토리 생성
        self.config_dir.mkdir(exist_ok=True)

        self._config: Optional[AppConfig] = None
        self.load_config()

    def load_config(self) -> AppConfig:
        """설정 파일 로드"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._config = AppConfig.from_dict(data)
                self.logger.info("설정 파일 로드 완료")
            else:
                # 기본 설정 생성
                self._config = AppConfig()
                self.save_config()
                self.logger.info("기본 설정 생성 완료")

        except Exception as e:
            self.logger.error(f"설정 로드 실패: {str(e)}")
            self._config = AppConfig()

        return self._config

    def save_config(self) -> bool:
        """설정 파일 저장"""
        try:
            if self._config is None:
                return False

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)

            self.logger.info("설정 파일 저장 완료")
            return True

        except Exception as e:
            self.logger.error(f"설정 저장 실패: {str(e)}")
            return False

    def get_config(self) -> AppConfig:
        """현재 설정 반환"""
        if self._config is None:
            self.load_config()
        return self._config

    def update_config(self, **kwargs) -> bool:
        """설정 업데이트"""
        try:
            if self._config is None:
                self.load_config()

            # 유효한 필드만 업데이트
            valid_fields = ['enabled', 'target_monitor_index', 'hotkey_enabled',
                          'log_level', 'auto_start', 'window_filters']

            updated = False
            for key, value in kwargs.items():
                if key in valid_fields:
                    setattr(self._config, key, value)
                    updated = True
                    self.logger.debug(f"설정 업데이트: {key} = {value}")

            if updated:
                return self.save_config()

            return True

        except Exception as e:
            self.logger.error(f"설정 업데이트 실패: {str(e)}")
            return False

    def reset_to_default(self) -> bool:
        """기본 설정으로 초기화"""
        try:
            self._config = AppConfig()
            result = self.save_config()
            self.logger.info("설정을 기본값으로 초기화")
            return result
        except Exception as e:
            self.logger.error(f"설정 초기화 실패: {str(e)}")
            return False

    def get_config_summary(self) -> Dict[str, Any]:
        """설정 요약 정보 반환"""
        if self._config is None:
            self.load_config()

        return {
            'config_file': str(self.config_file),
            'file_exists': self.config_file.exists(),
            'settings': self._config.to_dict()
        }