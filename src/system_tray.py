"""
시스템 트레이 UI - 최소 기능 구현
"""
import tkinter as tk
from tkinter import messagebox
import threading
from typing import Callable, Optional
from .logger import get_logger


class SystemTrayIcon:
    """시스템 트레이 아이콘 클래스 (간단한 GUI 창으로 대체)"""

    def __init__(self):
        self.logger = get_logger("SystemTrayIcon")
        self.root: Optional[tk.Tk] = None
        self.enabled = False
        self.toggle_callback: Optional[Callable] = None
        self.settings_callback: Optional[Callable] = None
        self.window_management_callback: Optional[Callable] = None
        self.exit_callback: Optional[Callable] = None
        self._running = False

    def set_callbacks(self, toggle_callback: Callable = None,
                     settings_callback: Callable = None,
                     window_management_callback: Callable = None,
                     exit_callback: Callable = None) -> None:
        """콜백 함수들 설정"""
        self.toggle_callback = toggle_callback
        self.settings_callback = settings_callback
        self.window_management_callback = window_management_callback
        self.exit_callback = exit_callback

    def start(self) -> bool:
        """트레이 아이콘 시작 (GUI 창으로 대체)"""
        try:
            self.root = tk.Tk()
            self.root.title("가상 데스크톱 모니터 제어")
            self.root.geometry("300x200")

            # 상태 표시
            self.status_label = tk.Label(self.root, text="상태: 비활성화", font=("Arial", 12))
            self.status_label.pack(pady=10)

            # 토글 버튼
            self.toggle_btn = tk.Button(self.root, text="활성화", command=self._on_toggle)
            self.toggle_btn.pack(pady=5)

            # 창 관리 버튼
            window_btn = tk.Button(self.root, text="창 관리", command=self._on_window_management)
            window_btn.pack(pady=5)

            # 설정 버튼
            settings_btn = tk.Button(self.root, text="설정", command=self._on_settings)
            settings_btn.pack(pady=5)

            # 종료 버튼
            exit_btn = tk.Button(self.root, text="종료", command=self._on_exit)
            exit_btn.pack(pady=5)

            # 창 닫기 이벤트 처리
            self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

            self._running = True
            self.logger.info("시스템 트레이 UI 시작")
            return True

        except Exception as e:
            self.logger.error(f"트레이 UI 시작 실패: {str(e)}")
            return False

    def run(self) -> None:
        """GUI 메인 루프 실행"""
        if self.root:
            self.root.mainloop()

    def stop(self) -> None:
        """트레이 아이콘 중지"""
        if self.root and self._running:
            self.root.quit()
            self._running = False
            self.logger.info("시스템 트레이 UI 중지")

    def update_status(self, enabled: bool) -> None:
        """상태 업데이트"""
        self.enabled = enabled
        if self.root:
            status_text = "상태: 활성화" if enabled else "상태: 비활성화"
            self.status_label.config(text=status_text)

            toggle_text = "비활성화" if enabled else "활성화"
            self.toggle_btn.config(text=toggle_text)

    def _on_toggle(self) -> None:
        """토글 버튼 클릭 처리"""
        if self.toggle_callback:
            try:
                self.toggle_callback()
            except Exception as e:
                self.logger.error(f"토글 콜백 실행 중 오류: {str(e)}")
                messagebox.showerror("오류", f"토글 실행 중 오류가 발생했습니다: {str(e)}")

    def _on_window_management(self) -> None:
        """창 관리 버튼 클릭 처리"""
        if self.window_management_callback:
            try:
                self.window_management_callback()
            except Exception as e:
                self.logger.error(f"창 관리 콜백 실행 중 오류: {str(e)}")
                messagebox.showerror("오류", f"창 관리 실행 중 오류가 발생했습니다: {str(e)}")
        else:
            messagebox.showinfo("창 관리", "창 관리 기능은 아직 구현되지 않았습니다.")

    def _on_settings(self) -> None:
        """설정 버튼 클릭 처리"""
        if self.settings_callback:
            try:
                self.settings_callback()
            except Exception as e:
                self.logger.error(f"설정 콜백 실행 중 오류: {str(e)}")
                messagebox.showerror("오류", f"설정 실행 중 오류가 발생했습니다: {str(e)}")
        else:
            messagebox.showinfo("설정", "설정 기능은 아직 구현되지 않았습니다.")

    def _on_exit(self) -> None:
        """종료 버튼 클릭 처리"""
        if messagebox.askquestion("종료", "정말로 종료하시겠습니까?") == "yes":
            if self.exit_callback:
                try:
                    self.exit_callback()
                except Exception as e:
                    self.logger.error(f"종료 콜백 실행 중 오류: {str(e)}")
            self.stop()

    def is_running(self) -> bool:
        """실행 상태 반환"""
        return self._running


class WindowManagementDialog:
    """창 관리 대화상자 클래스"""

    def __init__(self, parent=None):
        self.logger = get_logger("WindowManagementDialog")
        self.parent = parent
        self.dialog = None
        self.window_manager = None
        self.window_listbox = None
        self.pinned_listbox = None

    def show(self, window_manager) -> None:
        """창 관리 대화상자 표시"""
        try:
            self.window_manager = window_manager
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("창 관리 - 가상 데스크톱 고정 설정")
            self.dialog.geometry("800x600")
            self.dialog.resizable(True, True)

            # 모달 설정
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

            # 메인 프레임
            main_frame = tk.Frame(self.dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # 설명 라벨
            desc_label = tk.Label(main_frame,
                                text="가상 데스크톱을 따라다닐 창을 선택하세요.\n"
                                     "고정된 창은 가상 데스크톱 전환 시 자동으로 현재 데스크톱으로 이동합니다.",
                                font=("Arial", 10), justify=tk.LEFT)
            desc_label.pack(pady=(0, 10))

            # 좌우 분할 프레임
            content_frame = tk.Frame(main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True)

            # 왼쪽: 전체 창 목록
            left_frame = tk.Frame(content_frame)
            left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

            tk.Label(left_frame, text="전체 창 목록", font=("Arial", 12, "bold")).pack()

            # 창 목록 리스트박스
            list_frame = tk.Frame(left_frame)
            list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            scrollbar1 = tk.Scrollbar(list_frame)
            scrollbar1.pack(side=tk.RIGHT, fill=tk.Y)

            self.window_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar1.set,
                                           selectmode=tk.SINGLE, font=("Arial", 9))
            self.window_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar1.config(command=self.window_listbox.yview)

            # 버튼 프레임
            btn_frame1 = tk.Frame(left_frame)
            btn_frame1.pack(pady=5)

            tk.Button(btn_frame1, text="→ 고정 추가", command=self._add_pinned).pack(side=tk.LEFT, padx=2)
            tk.Button(btn_frame1, text="새로고침", command=self._refresh_windows).pack(side=tk.LEFT, padx=2)

            # 오른쪽: 고정된 창 목록
            right_frame = tk.Frame(content_frame)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

            tk.Label(right_frame, text="고정된 창 목록", font=("Arial", 12, "bold")).pack()

            # 고정된 창 리스트박스
            pinned_frame = tk.Frame(right_frame)
            pinned_frame.pack(fill=tk.BOTH, expand=True, pady=5)

            scrollbar2 = tk.Scrollbar(pinned_frame)
            scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

            self.pinned_listbox = tk.Listbox(pinned_frame, yscrollcommand=scrollbar2.set,
                                           selectmode=tk.SINGLE, font=("Arial", 9))
            self.pinned_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar2.config(command=self.pinned_listbox.yview)

            # 버튼 프레임
            btn_frame2 = tk.Frame(right_frame)
            btn_frame2.pack(pady=5)

            tk.Button(btn_frame2, text="← 고정 해제", command=self._remove_pinned).pack(side=tk.LEFT, padx=2)

            # 하단 버튼
            bottom_frame = tk.Frame(main_frame)
            bottom_frame.pack(pady=10)

            tk.Button(bottom_frame, text="닫기", command=self._close_dialog).pack()

            # 창 중앙 배치
            self.dialog.update_idletasks()
            x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
            self.dialog.geometry(f"+{x}+{y}")

            # 초기 데이터 로드
            self._refresh_windows()
            self._refresh_pinned()

            self.logger.info("창 관리 대화상자 표시")

        except Exception as e:
            self.logger.error(f"창 관리 대화상자 표시 실패: {str(e)}")

    def _refresh_windows(self) -> None:
        """전체 창 목록 새로고침"""
        try:
            self.window_listbox.delete(0, tk.END)
            windows = self.window_manager.get_current_windows_for_selection()

            for window in windows:
                status = " [고정됨]" if window['is_pinned'] else ""
                display_text = f"{window['title']}{status}"
                self.window_listbox.insert(tk.END, display_text)

            self.logger.debug(f"전체 창 목록 새로고침: {len(windows)}개")

        except Exception as e:
            self.logger.error(f"창 목록 새로고침 실패: {str(e)}")

    def _refresh_pinned(self) -> None:
        """고정된 창 목록 새로고침"""
        try:
            self.pinned_listbox.delete(0, tk.END)
            pinned_windows = self.window_manager.get_pinned_windows()

            for window in pinned_windows:
                status = " [보임]" if window['is_visible'] else " [숨김]"
                display_text = f"{window['title']}{status}"
                self.pinned_listbox.insert(tk.END, display_text)

            self.logger.debug(f"고정된 창 목록 새로고침: {len(pinned_windows)}개")

        except Exception as e:
            self.logger.error(f"고정된 창 목록 새로고침 실패: {str(e)}")

    def _add_pinned(self) -> None:
        """선택된 창을 고정 목록에 추가"""
        try:
            selection = self.window_listbox.curselection()
            if not selection:
                messagebox.showwarning("선택 필요", "고정할 창을 선택해주세요.")
                return

            index = selection[0]
            windows = self.window_manager.get_current_windows_for_selection()

            if index < len(windows):
                window = windows[index]
                if window['is_pinned']:
                    messagebox.showinfo("이미 고정됨", "선택한 창은 이미 고정되어 있습니다.")
                    return

                if self.window_manager.add_pinned_window(window['hwnd']):
                    messagebox.showinfo("고정 완료", f"'{window['title']}' 창이 고정되었습니다.")
                    self._refresh_windows()
                    self._refresh_pinned()
                else:
                    messagebox.showerror("고정 실패", "창 고정에 실패했습니다.")

        except Exception as e:
            self.logger.error(f"창 고정 추가 실패: {str(e)}")
            messagebox.showerror("오류", f"창 고정 중 오류가 발생했습니다: {str(e)}")

    def _remove_pinned(self) -> None:
        """선택된 창을 고정 목록에서 제거"""
        try:
            selection = self.pinned_listbox.curselection()
            if not selection:
                messagebox.showwarning("선택 필요", "고정 해제할 창을 선택해주세요.")
                return

            index = selection[0]
            pinned_windows = self.window_manager.get_pinned_windows()

            if index < len(pinned_windows):
                window = pinned_windows[index]
                if self.window_manager.remove_pinned_window(window['hwnd']):
                    messagebox.showinfo("고정 해제", f"'{window['title']}' 창의 고정이 해제되었습니다.")
                    self._refresh_windows()
                    self._refresh_pinned()
                else:
                    messagebox.showerror("고정 해제 실패", "창 고정 해제에 실패했습니다.")

        except Exception as e:
            self.logger.error(f"창 고정 해제 실패: {str(e)}")
            messagebox.showerror("오류", f"창 고정 해제 중 오류가 발생했습니다: {str(e)}")

    def _close_dialog(self) -> None:
        """대화상자 닫기"""
        self.dialog.destroy()
        self.logger.info("창 관리 대화상자 닫기")


class SettingsDialog:
    """설정 대화상자 클래스"""

    def __init__(self, parent=None):
        self.logger = get_logger("SettingsDialog")
        self.parent = parent
        self.dialog = None
        self.config_callback: Optional[Callable] = None

    def set_config_callback(self, callback: Callable) -> None:
        """설정 변경 콜백 설정"""
        self.config_callback = callback

    def show(self, current_config: dict) -> None:
        """설정 대화상자 표시"""
        try:
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("설정")
            self.dialog.geometry("400x300")
            self.dialog.resizable(False, False)

            # 모달 설정
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

            # 대상 모니터 설정
            tk.Label(self.dialog, text="대상 모니터:", font=("Arial", 10)).pack(pady=5)

            self.monitor_var = tk.StringVar(value=str(current_config.get('target_monitor_index', 1)))
            monitor_frame = tk.Frame(self.dialog)
            monitor_frame.pack(pady=5)

            tk.Radiobutton(monitor_frame, text="주 모니터 (0)", variable=self.monitor_var,
                          value="0").pack(side=tk.LEFT, padx=10)
            tk.Radiobutton(monitor_frame, text="보조 모니터 (1)", variable=self.monitor_var,
                          value="1").pack(side=tk.LEFT, padx=10)

            # 로그 레벨 설정
            tk.Label(self.dialog, text="로그 레벨:", font=("Arial", 10)).pack(pady=(20,5))

            self.log_var = tk.StringVar(value=current_config.get('log_level', 'INFO'))
            log_frame = tk.Frame(self.dialog)
            log_frame.pack(pady=5)

            for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                tk.Radiobutton(log_frame, text=level, variable=self.log_var,
                              value=level).pack(side=tk.LEFT, padx=5)

            # 핫키 활성화
            self.hotkey_var = tk.BooleanVar(value=current_config.get('hotkey_enabled', True))
            tk.Checkbutton(self.dialog, text="핫키 활성화 (Win+Ctrl+방향키)",
                          variable=self.hotkey_var, font=("Arial", 10)).pack(pady=10)

            # 버튼
            btn_frame = tk.Frame(self.dialog)
            btn_frame.pack(pady=20)

            tk.Button(btn_frame, text="확인", command=self._on_ok).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="취소", command=self._on_cancel).pack(side=tk.LEFT, padx=10)

            # 창 중앙 배치
            self.dialog.update_idletasks()
            x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
            self.dialog.geometry(f"+{x}+{y}")

            self.logger.info("설정 대화상자 표시")

        except Exception as e:
            self.logger.error(f"설정 대화상자 표시 실패: {str(e)}")

    def _on_ok(self) -> None:
        """확인 버튼 클릭 처리"""
        try:
            new_config = {
                'target_monitor_index': int(self.monitor_var.get()),
                'log_level': self.log_var.get(),
                'hotkey_enabled': self.hotkey_var.get()
            }

            if self.config_callback:
                self.config_callback(new_config)

            self.dialog.destroy()
            self.logger.info("설정 변경 완료")

        except Exception as e:
            self.logger.error(f"설정 저장 중 오류: {str(e)}")
            messagebox.showerror("오류", f"설정 저장 중 오류가 발생했습니다: {str(e)}")

    def _on_cancel(self) -> None:
        """취소 버튼 클릭 처리"""
        self.dialog.destroy()
        self.logger.info("설정 변경 취소")