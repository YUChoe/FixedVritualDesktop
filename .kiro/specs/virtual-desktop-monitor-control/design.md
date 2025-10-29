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

**역할**: 가상 데스크톱 상태 관리

```python
class VirtualDesktopController:
    def get_current_desktop_id(self) -> str
    def detect_desktop_change(self) -> bool
    def handle_desktop_switch(self, direction: str) -> None
```

**주요 기능**:
- IVirtualDesktopManager 인터페이스 활용
- 가상 데스크톱 전환 감지
- 창 고정 로직 조율

### 5. SystemTrayIcon

**역할**: 시스템 트레이 UI

```python
class SystemTrayIcon:
    def create_tray_icon(self) -> None
    def show_context_menu(self) -> None
    def toggle_enabled_state(self) -> None
    def open_settings(self) -> None
```

**주요 기능**:
- 트레이 아이콘 표시 및 상태 표시
- 우클릭 컨텍스트 메뉴 제공
- 활성화/비활성화 토글
- 설정 창 열기

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
    fixed_monitors: List[int]
    enabled: bool
    log_level: str
    config_version: str
```

## 오류 처리

### 1. Windows API 오류

- **전략**: try-catch로 API 호출 감싸기
- **복구**: 기본값 반환 또는 기능 비활성화
- **로깅**: 상세한 오류 정보 기록

### 2. 모니터 연결 변화

- **감지**: WM_DISPLAYCHANGE 메시지 모니터링
- **대응**: 모니터 목록 재조회 및 설정 업데이트
- **알림**: 사용자에게 변경 사항 알림

### 3. 권한 부족

- **확인**: 관리자 권한 필요 여부 체크
- **안내**: 사용자에게 권한 상승 요청
- **대안**: 제한된 기능으로 동작

### 4. 가상 데스크톱 API 실패

- **대체**: 폴링 방식으로 데스크톱 변화 감지
- **제한**: 일부 기능 비활성화
- **복구**: 주기적 재시도

## 테스트 전략

### 1. 단위 테스트

- **WindowManager**: 창 정보 수집 및 복원 로직
- **MonitorManager**: 모니터 정보 관리
- **ConfigManager**: 설정 저장/로드
- **WindowsAPI**: API 래퍼 함수들

### 2. 통합 테스트

- **가상 데스크톱 전환 시나리오**: 실제 키 입력으로 전환 테스트
- **멀티 모니터 환경**: 다양한 모니터 구성에서 테스트
- **창 복원 정확성**: 창 위치가 정확히 복원되는지 확인

### 3. 시스템 테스트

- **장시간 실행**: 메모리 누수 및 안정성 테스트
- **다양한 애플리케이션**: 여러 종류의 창에서 동작 확인
- **시스템 리소스**: CPU 및 메모리 사용량 모니터링

### 4. 사용자 시나리오 테스트

- **일반적인 워크플로우**: 개발자의 실제 사용 패턴 시뮬레이션
- **설정 변경**: 모니터 설정 변경 시 동작 확인
- **오류 상황**: 예상치 못한 상황에서의 복구 능력 테스트

## 성능 고려사항

### 1. 메모리 사용량

- **창 정보 캐싱**: 필요한 정보만 메모리에 유지
- **주기적 정리**: 더 이상 존재하지 않는 창 정보 제거
- **효율적인 데이터 구조**: 빠른 검색을 위한 해시맵 활용

### 2. CPU 사용량

- **이벤트 기반 처리**: 폴링 대신 이벤트 기반 아키텍처
- **지연 로딩**: 필요할 때만 창 정보 수집
- **백그라운드 스레드**: UI 블로킹 방지

### 3. 응답 시간

- **빠른 키 감지**: 50ms 이내 키 입력 감지
- **즉시 창 복원**: 200ms 이내 창 위치 복원
- **비동기 처리**: 무거운 작업은 별도 스레드에서 처리

## 보안 고려사항

### 1. 권한 관리

- **최소 권한 원칙**: 필요한 최소한의 권한만 요청
- **권한 확인**: 실행 시 필요한 권한 보유 여부 확인
- **안전한 API 사용**: 검증된 Windows API만 사용

### 2. 데이터 보호

- **설정 파일 암호화**: 민감한 설정 정보 보호
- **로그 정보 제한**: 개인정보가 포함된 로그 방지
- **임시 파일 정리**: 사용 후 임시 파일 안전 삭제

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