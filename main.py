#!/usr/bin/env python3
"""
가상 데스크톱 모니터 제어 애플리케이션

Windows 11의 가상 데스크톱 전환 시 서브모니터의 창들을 고정시키는 기능을 제공합니다.
"""
import sys
import argparse
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.app import VirtualDesktopApp
from src.logger import get_logger
from src.error_handler import install_global_exception_handler, uninstall_global_exception_handler, get_resource_manager


def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="가상 데스크톱 모니터 제어 애플리케이션",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main.py              # 기본 실행
  python main.py --debug      # 디버그 모드로 실행
  python main.py --version    # 버전 정보 표시
        """
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드로 실행 (로그 레벨을 DEBUG로 설정)'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='가상 데스크톱 모니터 제어 v1.0.0'
    )

    parser.add_argument(
        '--config-dir',
        type=str,
        default='config',
        help='설정 파일 디렉토리 경로 (기본값: config)'
    )

    return parser.parse_args()


def main():
    """메인 함수"""
    app = None
    resource_manager = get_resource_manager()

    try:
        # 전역 예외 처리기 설치
        def crash_handler(exc_type, exc_value, exc_traceback):
            print(f"\n치명적 오류가 발생했습니다: {exc_type.__name__}: {exc_value}")
            print("로그 파일을 확인해주세요.")
            if app:
                app.stop()

        install_global_exception_handler(crash_handler)

        # 명령행 인수 파싱
        args = parse_arguments()

        # 애플리케이션 초기화
        app = VirtualDesktopApp()

        # 리소스 매니저에 앱 등록
        resource_manager.register_resource("app", app, lambda x: x.stop())

        # 디버그 모드 설정
        if args.debug:
            app.config_manager.update_config(log_level='DEBUG')
            print("디버그 모드로 실행됩니다.")

        logger = get_logger("main")
        logger.info("애플리케이션 시작")

        # 애플리케이션 시작
        if app.start():
            logger.info("애플리케이션이 성공적으로 시작되었습니다.")
            print("가상 데스크톱 모니터 제어가 시작되었습니다.")
            print("시스템 트레이에서 설정을 변경할 수 있습니다.")
            print("종료하려면 트레이 아이콘에서 '종료'를 클릭하세요.")

            # 메인 루프 실행
            app.run()

        else:
            logger.error("애플리케이션 시작 실패")
            print("애플리케이션을 시작할 수 없습니다. 로그를 확인해주세요.")
            return 1

    except KeyboardInterrupt:
        logger = get_logger("main")
        logger.info("사용자에 의해 중단됨 (Ctrl+C)")
        print("\n애플리케이션이 중단되었습니다.")

    except Exception as e:
        logger = get_logger("main")
        logger.error(f"예상치 못한 오류 발생: {str(e)}", exc_info=True)
        print(f"오류가 발생했습니다: {str(e)}")
        return 1

    finally:
        # 정리 작업
        try:
            resource_manager.cleanup_all()
            uninstall_global_exception_handler()
        except Exception as e:
            print(f"정리 작업 중 오류: {str(e)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())