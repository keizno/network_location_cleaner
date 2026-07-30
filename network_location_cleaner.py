"""
네트워크 위치(내 PC > 네트워크 위치) 정리 도구 - 이동/복원 버전
다크테마 / tkinter (표준 라이브러리만 사용, 별도 설치 불필요)

원본 경로:
    %APPDATA%\\Microsoft\\Windows\\Network Shortcuts\\
보관 경로:
    %APPDATA%\\Microsoft\\Windows\\Network Shortcuts_Backup\\

죽은 네트워크 위치를 삭제하지 않고 보관 폴더로 "이동"해두면
탐색기 목록에서는 사라지고(=죽은 서버 접속 시도 없음),
나중에 필요할 때 "복원" 버튼으로 원래 위치에 그대로 되돌릴 수 있습니다.
"""

import json
import os
import shutil
import stat
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

SETTINGS_PATH = os.path.join(os.path.expanduser("~"), "network_location_cleaner_settings.json")

# ---------- 다크 테마 색상 ----------
BG = "#1e1e1e"
BG_LIGHT = "#252526"
FG = "#e0e0e0"
FG_DIM = "#9a9a9a"
ACCENT = "#3a7bd5"
ACCENT_HOVER = "#4a8be5"
DANGER = "#d9534f"
DANGER_HOVER = "#e56b67"
SELECT_BG = "#094771"
BORDER = "#3c3c3c"


def get_active_dir() -> str:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA 환경변수를 찾을 수 없습니다.")
    return os.path.join(appdata, "Microsoft", "Windows", "Network Shortcuts")


def get_backup_dir() -> str:
    appdata = os.environ.get("APPDATA")
    return os.path.join(appdata, "Microsoft", "Windows", "Network Shortcuts_Backup")


def load_settings() -> dict:
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data: dict):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _force_remove_readonly(func, path, exc_info):
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass


def _unique_dest(dest_dir: str, name: str) -> str:
    """대상 폴더에 동일 이름이 있으면 (1), (2)... 붙여서 충돌 방지"""
    candidate = os.path.join(dest_dir, name)
    if not os.path.exists(candidate):
        return candidate
    base, ext = os.path.splitext(name)
    i = 1
    while True:
        new_name = f"{base} ({i}){ext}"
        candidate = os.path.join(dest_dir, new_name)
        if not os.path.exists(candidate):
            return candidate
        i += 1


def move_item(src_dir: str, dst_dir: str, name: str):
    src = os.path.join(src_dir, name)
    if not os.path.exists(src):
        return False, "존재하지 않는 항목입니다."
    try:
        os.makedirs(dst_dir, exist_ok=True)
        dest = _unique_dest(dst_dir, name)
        shutil.move(src, dest)
        return True, "이동 완료"
    except Exception as e:
        return False, str(e)


def delete_item(base_dir: str, name: str):
    target = os.path.join(base_dir, name)
    if not os.path.exists(target):
        return False, "존재하지 않는 항목입니다."
    try:
        if os.path.isdir(target):
            shutil.rmtree(target, onerror=_force_remove_readonly)
        else:
            os.chmod(target, stat.S_IWRITE)
            os.remove(target)
        if os.path.exists(target):
            return False, "삭제 실패 (여전히 존재)"
        return True, "삭제 완료"
    except Exception as e:
        return False, str(e)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("네트워크 위치 정리 도구")
        self.geometry("600x520")
        self.minsize(480, 420)
        self.configure(bg=BG)

        self.active_dir = None
        try:
            self.active_dir = get_active_dir()
        except Exception as e:
            messagebox.showerror("오류", str(e))
        settings = load_settings()
        saved_backup = settings.get("backup_dir")
        self.backup_dir = saved_backup if saved_backup else get_backup_dir()

        self._build_style()
        self._build_ui()
        self.refresh_all()

    # ---------- 스타일 ----------
    def _build_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 10))
        style.configure("Dim.TLabel", background=BG, foreground=FG_DIM, font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=BG, foreground=FG, font=("Segoe UI", 13, "bold"))

        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab", background=BG_LIGHT, foreground=FG_DIM,
            padding=(14, 8), font=("Segoe UI", 10),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", BG)],
            foreground=[("selected", FG)],
        )

        style.configure(
            "Accent.TButton",
            background=ACCENT, foreground="#ffffff",
            font=("Segoe UI", 10), borderwidth=0, focusthickness=0, padding=8,
        )
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])

        style.configure(
            "Danger.TButton",
            background=DANGER, foreground="#ffffff",
            font=("Segoe UI", 10), borderwidth=0, focusthickness=0, padding=8,
        )
        style.map("Danger.TButton", background=[("active", DANGER_HOVER)])

        style.configure(
            "Plain.TButton",
            background=BG_LIGHT, foreground=FG,
            font=("Segoe UI", 10), borderwidth=1, focusthickness=0, padding=8,
        )
        style.map("Plain.TButton", background=[("active", "#333333")])

        style.configure(
            "Vertical.TScrollbar",
            background=BG_LIGHT, troughcolor=BG, arrowcolor=FG, borderwidth=0,
        )

    # ---------- UI ----------
    def _build_ui(self):
        pad = 16

        header = ttk.Frame(self)
        header.pack(fill="x", padx=pad, pady=(pad, 4))
        ttk.Label(header, text="네트워크 위치 정리 도구", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="죽은 네트워크 위치를 삭제 대신 보관해두고, 필요하면 복원할 수 있습니다.",
            style="Dim.TLabel", wraplength=560,
        ).pack(anchor="w", pady=(2, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=pad, pady=8)

        # ---- 탭 1: 현재 등록된 네트워크 위치 ----
        active_tab = ttk.Frame(notebook)
        notebook.add(active_tab, text="현재 등록된 위치")
        self.active_listbox = self._make_listbox(active_tab)
        self.active_path_label = ttk.Label(active_tab, text=self.active_dir or "", style="Dim.TLabel", wraplength=540)
        self.active_path_label.pack(anchor="w", padx=4, pady=(4, 0))

        active_btns = ttk.Frame(active_tab)
        active_btns.pack(fill="x", pady=(8, 0))
        ttk.Button(active_btns, text="새로고침", style="Plain.TButton", command=self.refresh_all).pack(side="left")
        ttk.Button(
            active_btns, text="선택 항목 삭제", style="Danger.TButton", command=self.delete_selected
        ).pack(side="right")
        ttk.Button(
            active_btns, text="선택 항목 보관", style="Accent.TButton", command=self.archive_selected
        ).pack(side="right", padx=(0, 8))

        # ---- 탭 2: 보관함 ----
        backup_tab = ttk.Frame(notebook)
        notebook.add(backup_tab, text="보관함")
        self.backup_listbox = self._make_listbox(backup_tab)

        path_row = ttk.Frame(backup_tab)
        path_row.pack(fill="x", pady=(4, 0))
        self.backup_path_label = ttk.Label(path_row, text=self.backup_dir, style="Dim.TLabel", wraplength=440)
        self.backup_path_label.pack(side="left", anchor="w", padx=4, fill="x", expand=True)
        ttk.Button(
            path_row, text="폴더 변경", style="Plain.TButton", command=self.change_backup_dir
        ).pack(side="right")

        backup_btns = ttk.Frame(backup_tab)
        backup_btns.pack(fill="x", pady=(8, 0))
        ttk.Button(backup_btns, text="새로고침", style="Plain.TButton", command=self.refresh_all).pack(side="left")
        ttk.Button(
            backup_btns, text="선택 항목 완전삭제", style="Danger.TButton", command=self.delete_from_backup
        ).pack(side="right")
        ttk.Button(
            backup_btns, text="선택 항목 복원", style="Accent.TButton", command=self.restore_selected
        ).pack(side="right", padx=(0, 8))

        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, style="Dim.TLabel").pack(
            anchor="w", padx=pad, pady=(0, pad)
        )

    def _make_listbox(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        lb = tk.Listbox(
            frame,
            bg=BG_LIGHT, fg=FG,
            selectbackground=SELECT_BG, selectforeground="#ffffff",
            activestyle="none", borderwidth=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
            font=("Segoe UI", 10), selectmode="extended",
        )
        lb.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=lb.yview)
        sb.pack(side="right", fill="y")
        lb.config(yscrollcommand=sb.set)
        return lb

    # ---------- 보관 폴더 변경 ----------
    def change_backup_dir(self):
        chosen = filedialog.askdirectory(
            title="보관함으로 사용할 폴더 선택",
            initialdir=self.backup_dir if os.path.isdir(self.backup_dir) else os.path.expanduser("~"),
        )
        if not chosen:
            return
        self.backup_dir = os.path.normpath(chosen)
        save_settings({"backup_dir": self.backup_dir})
        self.backup_path_label.config(text=self.backup_dir)
        self.refresh_all()

    # ---------- 목록 갱신 ----------
    def refresh_all(self):
        self._fill_listbox(self.active_listbox, self.active_dir)
        self._fill_listbox(self.backup_listbox, self.backup_dir)
        self.backup_path_label.config(text=self.backup_dir)
        a = self.active_listbox.size()
        b = self.backup_listbox.size()
        self.status_var.set(f"현재 등록: {a}개  |  보관함: {b}개")

    def _fill_listbox(self, listbox, path):
        listbox.delete(0, "end")
        if not path or not os.path.isdir(path):
            return
        for name in sorted(os.listdir(path)):
            listbox.insert("end", name)

    def _selected(self, listbox):
        return [listbox.get(i) for i in listbox.curselection()]

    # ---------- 동작: 현재 등록된 위치 ----------
    def archive_selected(self):
        names = self._selected(self.active_listbox)
        if not names:
            messagebox.showinfo("알림", "보관할 항목을 목록에서 선택하세요.")
            return
        ok, fails = 0, []
        for name in names:
            success, msg = move_item(self.active_dir, self.backup_dir, name)
            if success:
                ok += 1
            else:
                fails.append(f"{name}: {msg}")
        self.refresh_all()
        self._report(ok, fails, "보관")

    def delete_selected(self):
        names = self._selected(self.active_listbox)
        if not names:
            messagebox.showinfo("알림", "삭제할 항목을 목록에서 선택하세요.")
            return
        if not messagebox.askyesno("삭제 확인", f"선택한 {len(names)}개 항목을 완전히 삭제할까요?\n(복원할 수 없습니다)"):
            return
        ok, fails = 0, []
        for name in names:
            success, msg = delete_item(self.active_dir, name)
            if success:
                ok += 1
            else:
                fails.append(f"{name}: {msg}")
        self.refresh_all()
        self._report(ok, fails, "삭제")

    # ---------- 동작: 보관함 ----------
    def restore_selected(self):
        names = self._selected(self.backup_listbox)
        if not names:
            messagebox.showinfo("알림", "복원할 항목을 목록에서 선택하세요.")
            return
        ok, fails = 0, []
        for name in names:
            success, msg = move_item(self.backup_dir, self.active_dir, name)
            if success:
                ok += 1
            else:
                fails.append(f"{name}: {msg}")
        self.refresh_all()
        self._report(ok, fails, "복원")

    def delete_from_backup(self):
        names = self._selected(self.backup_listbox)
        if not names:
            messagebox.showinfo("알림", "삭제할 항목을 목록에서 선택하세요.")
            return
        if not messagebox.askyesno("완전 삭제 확인", f"보관함에서 {len(names)}개 항목을 완전히 삭제할까요?\n(복원할 수 없습니다)"):
            return
        ok, fails = 0, []
        for name in names:
            success, msg = delete_item(self.backup_dir, name)
            if success:
                ok += 1
            else:
                fails.append(f"{name}: {msg}")
        self.refresh_all()
        self._report(ok, fails, "완전 삭제")

    def _report(self, ok, fails, action):
        if fails:
            self.status_var.set(f"{action} {ok}개 완료, {len(fails)}개 실패")
            messagebox.showwarning("일부 실패", "\n".join(fails))
        else:
            self.status_var.set(f"{action} {ok}개 완료")


if __name__ == "__main__":
    if os.name != "nt":
        print("이 프로그램은 윈도우에서 실행해야 합니다.")
        sys.exit(1)
    App().mainloop()
