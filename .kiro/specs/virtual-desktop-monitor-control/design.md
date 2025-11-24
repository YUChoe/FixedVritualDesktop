# 설계 문서

## 개요

Windows 11에서 가상 데스크톱 전환 시 서브모니터의 창만 고정하는 Python 애플리케이션의 설계입니다. 이 애플리케이션은 Windows API를 활용하여 실시간으로 가상 데스크톱 전환을 감지하고, 지정된 모니터의 창들을 원래 위치에 유지합니다.

## 아키텍처

### 전체 구조

```
VirtualDesktopApp
├── Core Services
│   ├── HotkeyListener (키보드 감지)
│   ├── WindowManager (창 관리)
│   ├── MonitorManager (모니터 관리)
│   └── VirtualDesktopController (가상 데스크톱 제어)
├── UI Components
│   ├── SystemTrayIcon (트레이 아이콘)
│   └── SettingsDialog (설정 창)
├── Configuration
│   └── ConfigManager (설정 관리)
└── Utilities
    ├── Logger (로깅)
    └── WindowsAPI (Windows API 래퍼)
```

### 주요 의존성

- **pywin32**: Windows API 접근 (win32api, win32gui, win32con)
- **pynput**: 글로벌 키보드 후킹
- **tkinter**: 설정 UI (Python 기본 포함)
- **json**: 설정 파일 관리
- **threading**: 비동기 처리
- **logging**: 로그 관리

## 컴포넌트 및 인터페이스

### 1. HotkeyListener

**역할**: Win + Ctrl + ←/→ 키 조합 감지

```python
class HotkeyListener:
    def start_listening(self) -> None
    def stop_listening(self) -> None
    def on_hotkey_pressed(self, direction: str) -> None
```

**주요 기능**:
- pynput.keyboard.GlobalHotKeys를 사용한 전역 키보드 후킹
- 가상 데스크톱 전환 키 조합 감지
- 이벤트 콜백을 통한 다른 컴포넌트 알림

### 2. WindowManager

**역할**: 창 위치 추적 및 복원

```python
class WindowManager:
    def get_all_windows(self) -> List[WindowInfo]
    def get_window_monitor(self, hwnd: int) -> int
    def save_window_states(self, monitor_id: int) -> Dict[int, WindowState]
    def restore_window_states(self, states: Dict[int, WindowState]) -> None
```

**주요 기능**:
- EnumWindows API를 통한 모든 창 열거
- MonitorFromWindow API로 창의 모니터 정보 확인
- GetWindowPlacement API로 창 위치/크기 정보 저장
- SetWindowPos API로 창 위치 복원

### 3. MonitorManager

**역할**: 모니터 정보 관리

```python
class MonitorManager:
    def get_monitor_list(self) -> List[MonitorInfo]
    def get_primary_monitor(self) -> MonitorInfo
    def is_monitor_connected(self, monitor_id: int) -> bool
```

**주요 기능**:
- EnumDisplayMonitors API를 통한 모니터 목록 조회
- 모니터 해상도, 위치 정보 관리
- 모니터 연결 상태 변화 감지

### 4. VirtualDesktopController

**역할**: 가상 데스크톱 상태 관리 및 선택적 창 고정

```python
class VirtualDesktopController:
    def get_current_desktop_id(self) -> str
    def handle_desktop_switch(self, direction: str) -> None
    def get_window_manager(self) -> SelectiveWindowManager
```

**주요 기능**:
- 보이는 창 목록 조합으로 데스크톱 상태 식별
- 가상 데스크톱 전환 감지 (핫키 기반)
- 고정된 창만 현재 데스크톱으로 이동

### 5. SystemTrayIcon

**역할**: 시스템 트레이 UI (tkinter GUI 창으로 구현)

```python
class SystemTrayIcon:
    def start(self) -> bool
    def run(self) -> None
    def update_status(self, enabled: bool) -> None
```

**주요 기능**:
- tkinter 기반 GUI 창 제공
- 활성화/비활성화 토글 버튼
- 창 관리 대화상자 열기
- 설정 대화상자 열기

### 6. SelectiveWindowManager

**역할**: 선택적 창 고정 관리

```python
class SelectiveWindowManager:
    def add_pinned_window(self, hwnd: int) -> bool
    def remove_pinned_window(self, hwnd: int) -> bool
    def get_pinned_windows(self) -> List[dict]
    def move_pinned_windows_to_current_desktop(self) -> int
```

**주요 기능**:
- 사용자가 선택한 창만 고정 목록에 추가
- 고정된 창 목록 JSON 파일로 저장/로드
- 가상 데스크톱 전환 시 고정된 창만 이동

## 데이터 모델

### WindowInfo

```python
@dataclass
class WindowInfo:
    hwnd: int
    title: str
    class_name: str
    monitor_id: int
    rect: Tuple[int, int, int, int]
    is_visible: bool
    is_minimized: bool
```

### WindowState

```python
@dataclass
class WindowState:
    hwnd: int
    x: int
    y: int
    width: int
    height: int
    show_state: int
    monitor_id: int
```

### MonitorInfo

```python
@dataclass
class MonitorInfo:
    monitor_id: int
    name: str
    rect: Tuple[int, int, int, int]
    work_rect: Tuple[int, int, int, int]
    is_primary: bool
```

### AppConfig

```python
@dataclass
class AppConfig:
    enabled: bool
    target_monitor_index: int
    hotkey_enabled: bool
    log_level: str
    auto_start: bool
    window_filters: List[str]
```

## 오류 처리

### 1. Windows API 오류

- **전략**: try-catch로 API 호출 감싸기
- **복구**: 기본값 반환 또는 기능 비활성화
- **로깅**: 상세한 오류 정보 기록

### 2. 가상 데스크톱 전환 감지

- **방식**: 보이는 창 목록 조합으로 데스크톱 상태 식별
- **쿨다운**: 중복 실행 방지를 위한 1.5초 쿨다운
- **복구**: 예외 발생 시 로깅 후 다음 전환 대기

## 테스트 전략

현재 구현은 수동 테스트를 통해 검증되었습니다. 자동화된 테스트는 향후 추가 예정입니다.

## 성능 고려사항

### 1. 메모리 사용량

- **선택적 창 추적**: 고정된 창만 메모리에 유지
- **유효성 검증**: 더 이상 존재하지 않는 창 자동 제거

### 2. CPU 사용량

- **이벤트 기반 처리**: 핫키 감지 시에만 동작
- **쿨다운 메커니즘**: 중복 실행 방지로 CPU 사용 최소화
- **백그라운드 스레드**: UI 블로킹 방지

### 3. 응답 시간

- **빠른 키 감지**: pynput을 통한 즉각적인 키 입력 감지
- **비동기 처리**: 창 이동 작업은 별도 처리

## 보안 고려사항

### 1. 권한 관리

- **최소 권한 원칙**: 필요한 최소한의 권한만 사용
- **안전한 API 사용**: 검증된 Windows API만 사용

### 2. 데이터 보호

- **로컬 설정 파일**: JSON 형식으로 로컬에 저장
- **로그 정보 제한**: 개인정보가 포함된 로그 방지

## 배포 및 설치

### 1. 패키징

- **PyInstaller**: 단일 실행 파일로 패키징
- **의존성 포함**: 필요한 모든 라이브러리 포함
- **크기 최적화**: 불필요한 모듈 제외
- **포터블 실행**: 별도 설치 없이 실행 가능

### 2. 실행 프로세스

- **수동 실행**: 사용자가 필요할 때 직접 실행
- **설정 디렉토리 생성**: 첫 실행 시 사용자 설정 폴더 생성
- **초기 설정**: 기본 모니터 구성 감지 및 설정

### 3. 설정 관리

- **로컬 설정 파일**: 실행 파일과 같은 디렉토리에 설정 저장
- **포터블 설정**: 설정 파일을 함께 이동하여 다른 PC에서도 사용 가능
- **설정 백업**: 사용자가 수동으로 설정 파일 백업 가능