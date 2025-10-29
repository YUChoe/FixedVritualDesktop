#!/usr/bin/env python3
"""
빌드된 실행 파일 테스트 및 최적화 스크립트
"""
import os
import sys
import time
import subprocess
from pathlib import Path


def check_build_exists():
    """빌드된 실행 파일 존재 확인"""
    exe_path = Path('dist/VirtualDesktopMonitorControl.exe')
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"실행 파일 발견: {exe_path}")
        print(f"파일 크기: {size_mb:.2f} MB")
        return exe_path
    else:
        print("실행 파일을 찾을 수 없습니다.")
        print("먼저 build.py를 실행하여 빌드를 완료하세요.")
        return None


def test_executable_startup(exe_path):
    """실행 파일 시작 테스트"""
    print("\n실행 파일 시작 테스트...")

    try:
        # 실행 파일을 백그라운드에서 시작
        process = subprocess.Popen([str(exe_path)],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        # 3초 대기
        time.sleep(3)

        # 프로세스가 여전히 실행 중인지 확인
        if process.poll() is None:
            print("✓ 실행 파일이 성공적으로 시작되었습니다.")

            # 프로세스 종료
            process.terminate()
            process.wait(timeout=5)
            print("✓ 실행 파일이 정상적으로 종료되었습니다.")
            return True
        else:
            stdout, stderr = process.communicate()
            print("✗ 실행 파일이 즉시 종료되었습니다.")
            if stderr:
                print(f"오류: {stderr.decode('utf-8', errors='ignore')}")
            return False

    except Exception as e:
        print(f"✗ 실행 파일 테스트 중 오류: {e}")
        return False


def analyze_dependencies(exe_path):
    """실행 파일 의존성 분석"""
    print("\n실행 파일 의존성 분석...")

    try:
        # PyInstaller의 pyi-archive_viewer 사용 (있다면)
        result = subprocess.run([sys.executable, '-c',
                               'import PyInstaller.utils.cliutils.archive_viewer; print("PyInstaller 도구 사용 가능")'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ PyInstaller 분석 도구 사용 가능")
        else:
            print("- PyInstaller 분석 도구 사용 불가")

        # 파일 크기 분석
        size_mb = exe_path.stat().st_size / (1024 * 1024)

        if size_mb > 100:
            print(f"⚠ 파일 크기가 큽니다: {size_mb:.2f} MB")
            print("최적화 권장사항:")
            print("  - 불필요한 모듈 제외")
            print("  - UPX 압축 사용")
            print("  - 별도 DLL로 분리")
        else:
            print(f"✓ 적절한 파일 크기: {size_mb:.2f} MB")

        return True

    except Exception as e:
        print(f"의존성 분석 중 오류: {e}")
        return False


def check_required_files():
    """필수 파일 존재 확인"""
    print("\n필수 파일 확인...")

    dist_dir = Path('dist')
    required_files = [
        'VirtualDesktopMonitorControl.exe',
        'README.txt'
    ]

    optional_dirs = [
        'config'
    ]

    all_good = True

    for file_name in required_files:
        file_path = dist_dir / file_name
        if file_path.exists():
            print(f"✓ {file_name}")
        else:
            print(f"✗ {file_name} - 누락")
            all_good = False

    for dir_name in optional_dirs:
        dir_path = dist_dir / dir_name
        if dir_path.exists():
            print(f"✓ {dir_name}/ (선택사항)")
        else:
            print(f"- {dir_name}/ (선택사항) - 없음")

    return all_good


def create_optimization_report():
    """최적화 보고서 생성"""
    print("\n최적화 보고서 생성...")

    exe_path = Path('dist/VirtualDesktopMonitorControl.exe')
    if not exe_path.exists():
        return False

    size_mb = exe_path.stat().st_size / (1024 * 1024)

    report = f"""# 빌드 최적화 보고서

## 실행 파일 정보
- 파일명: VirtualDesktopMonitorControl.exe
- 크기: {size_mb:.2f} MB
- 생성일: {time.strftime('%Y-%m-%d %H:%M:%S')}

## 최적화 권장사항

### 파일 크기 최적화
"""

    if size_mb > 50:
        report += """
- UPX 압축 활성화 (이미 적용됨)
- 불필요한 모듈 제외 검토
- 별도 DLL 분리 고려
"""
    else:
        report += """
- 현재 크기는 적절합니다
"""

    report += """
### 성능 최적화
- 시작 시간 최적화를 위한 지연 로딩 고려
- 메모리 사용량 모니터링
- 백그라운드 프로세스 최적화

### 배포 최적화
- 디지털 서명 추가 고려
- 설치 프로그램 생성 고려
- 자동 업데이트 시스템 고려

## 테스트 결과
- 실행 파일 시작: 테스트 필요
- 기본 기능: 수동 테스트 필요
- 메모리 누수: 장시간 실행 테스트 필요
"""

    report_path = Path('dist/optimization_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ 최적화 보고서 생성: {report_path}")
    return True


def main():
    """메인 함수"""
    print("=== 실행 파일 테스트 및 최적화 ===")

    # 1. 빌드 파일 존재 확인
    print("1. 빌드된 실행 파일 확인...")
    exe_path = check_build_exists()
    if not exe_path:
        return 1

    # 2. 필수 파일 확인
    print("\n2. 필수 파일 확인...")
    if not check_required_files():
        print("⚠ 일부 필수 파일이 누락되었습니다.")

    # 3. 실행 파일 시작 테스트
    print("\n3. 실행 파일 시작 테스트...")
    startup_ok = test_executable_startup(exe_path)

    # 4. 의존성 분석
    print("\n4. 의존성 분석...")
    analyze_dependencies(exe_path)

    # 5. 최적화 보고서 생성
    print("\n5. 최적화 보고서 생성...")
    create_optimization_report()

    print("\n=== 테스트 완료 ===")

    if startup_ok:
        print("✓ 모든 기본 테스트를 통과했습니다.")
        print("수동으로 전체 기능을 테스트해보세요.")
    else:
        print("⚠ 일부 테스트에서 문제가 발견되었습니다.")
        print("로그 파일을 확인하고 문제를 해결하세요.")

    return 0 if startup_ok else 1


if __name__ == "__main__":
    sys.exit(main())