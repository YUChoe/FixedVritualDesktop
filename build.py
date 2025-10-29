#!/usr/bin/env python3
"""
PyInstaller 빌드 스크립트
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_dirs():
    """빌드 디렉토리 정리"""
    dirs_to_clean = ['build', 'dist', '__pycache__']

    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"정리됨: {dir_name}")

    # .spec 파일 정리
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"정리됨: {spec_file}")


def install_pyinstaller():
    """PyInstaller 설치"""
    try:
        import PyInstaller
        print("PyInstaller가 이미 설치되어 있습니다.")
        return True
    except ImportError:
        print("PyInstaller를 설치합니다...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
            print("PyInstaller 설치 완료")
            return True
        except subprocess.CalledProcessError as e:
            print(f"PyInstaller 설치 실패: {e}")
            return False


def create_spec_file():
    """PyInstaller spec 파일 생성"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'win32api',
        'win32gui',
        'win32con',
        'win32process',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VirtualDesktopMonitorControl',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI 애플리케이션이므로 콘솔 숨김
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일이 있다면 여기에 경로 지정
)
'''

    with open('app.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("PyInstaller spec 파일 생성 완료: app.spec")


def build_executable():
    """실행 파일 빌드"""
    try:
        print("실행 파일 빌드를 시작합니다...")

        # PyInstaller 실행
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'app.spec']

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            print("빌드 성공!")
            print("실행 파일 위치: dist/VirtualDesktopMonitorControl.exe")
            return True
        else:
            print("빌드 실패:")
            print(result.stdout)
            print(result.stderr)
            return False

    except Exception as e:
        print(f"빌드 중 오류 발생: {e}")
        return False


def copy_resources():
    """필요한 리소스 파일 복사"""
    dist_dir = Path('dist')
    if not dist_dir.exists():
        print("dist 디렉토리가 없습니다.")
        return False

    # config 디렉토리가 있다면 복사
    if Path('config').exists():
        shutil.copytree('config', dist_dir / 'config', dirs_exist_ok=True)
        print("config 디렉토리 복사 완료")

    # README 파일 생성
    readme_content = """# 가상 데스크톱 모니터 제어

Windows 11의 가상 데스크톱 전환 시 서브모니터의 창들을 고정시키는 애플리케이션입니다.

## 사용법

1. VirtualDesktopMonitorControl.exe를 실행합니다.
2. 시스템 트레이에 아이콘이 나타납니다.
3. 트레이 아이콘을 우클릭하여 설정을 변경할 수 있습니다.
4. Win + Ctrl + 방향키로 가상 데스크톱을 전환하면 서브모니터의 창이 고정됩니다.

## 설정

- 대상 모니터: 창을 고정할 모니터 선택
- 로그 레벨: 로그 상세도 설정
- 핫키 활성화: 핫키 기능 on/off

## 로그 파일

logs/ 디렉토리에 로그 파일이 생성됩니다.
"""

    with open(dist_dir / 'README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print("README.txt 생성 완료")
    return True


def main():
    """메인 함수"""
    print("=== 가상 데스크톱 모니터 제어 빌드 스크립트 ===")

    # 1. 빌드 디렉토리 정리
    print("\n1. 빌드 디렉토리 정리...")
    clean_build_dirs()

    # 2. PyInstaller 설치 확인
    print("\n2. PyInstaller 설치 확인...")
    if not install_pyinstaller():
        return 1

    # 3. spec 파일 생성
    print("\n3. PyInstaller spec 파일 생성...")
    create_spec_file()

    # 4. 실행 파일 빌드
    print("\n4. 실행 파일 빌드...")
    if not build_executable():
        return 1

    # 5. 리소스 파일 복사
    print("\n5. 리소스 파일 복사...")
    copy_resources()

    print("\n=== 빌드 완료 ===")
    print("dist/ 디렉토리에서 실행 파일을 확인하세요.")

    return 0


if __name__ == "__main__":
    sys.exit(main())