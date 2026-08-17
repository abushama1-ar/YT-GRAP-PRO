import customtkinter as ctk
import yt_dlp
import threading
import os
import subprocess
import sys
import webbrowser
import glob
import datetime
import json
import ctypes
import shutil
import tempfile
import zipfile
import urllib.request
from pathlib import Path
from tkinter import messagebox, filedialog
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── لوحة ألوان عصرية (Nova System Theme) ──────────────────────────────────
C = {
    "bg":        "#121212",
    "card":      "#1E1E1E",
    "card_hov":  "#EBF1E5",
    "input":     "#252525",
    "accent":    "#3B82F6",
    "acc_hov":   "#2563EB",
    "gold":      "#F59E0B",
    "ok":        "#10B981",
    "txt":       "#CFBCBC",
    "dim":       "#9CA3AF",
    "border":    "#2D2D2D",
}

EXTS = (".mp4", ".mkv", ".webm", ".avi", ".mov", ".mp3", ".m4a", ".flac", ".wav")

# ─── معلومات التطبيق والإصدار ─────────────────────────────────────────────
APP_NAME = "YT-GRAP-PRO"
CURRENT_VERSION = "v1.0.0"
GITHUB_REPO = "abushama1-ar/YT-GRAP-PRO"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


# ─── دالة الحصول على المسار الأساسي (تدعم Nuitka) ──────────────────────────
def get_base_dir():
    """الحصول على المجلد الأساسي للتطبيق (يدعم التشغيل المباشر و Nuitka)"""
    if getattr(sys, 'frozen', False):
        # Nuitka --onefile يستخدم sys._MEIPASS
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        # PyInstaller
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))


def get_ffmpeg_path():
    """الحصول على مسار ffmpeg من مجلد bin"""
    base_dir = get_base_dir()
    ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    
    # البحث في مجلد bin
    ffmpeg_path = os.path.join(base_dir, "bin", ffmpeg_name)
    if os.path.exists(ffmpeg_path):
        return ffmpeg_path
    
    # محاولة البحث في مجلد التطبيق نفسه
    ffmpeg_path = os.path.join(base_dir, ffmpeg_name)
    if os.path.exists(ffmpeg_path):
        return ffmpeg_path
    
    # محاولة البحث في PATH
    for path in os.environ.get("PATH", "").split(os.pathsep):
        full_path = os.path.join(path, ffmpeg_name)
        if os.path.exists(full_path):
            return full_path
    
    return None


# ─── دوال التحديث من GitHub (بدون requests) ──────────────────────────────
def fetch_github_release():
    """جلب بيانات الإصدار الأخير من GitHub باستخدام urllib"""
    try:
        req = urllib.request.Request(GITHUB_API_URL)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.getcode() == 200:
                return json.loads(response.read().decode('utf-8'))
    except Exception:
        pass
    return None


def download_file(url, dest_path, progress_callback=None):
    """تحميل ملف مع عرض التقدم باستخدام urllib"""
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and progress_callback:
                        progress_callback(int((downloaded / total_size) * 100))
            return True
    except Exception as e:
        raise e


# ─── نافذة المشغّل الخارجي ────────────────────────────────────────────────
class PlayerWindow(ctk.CTkToplevel):
    """نافذة تشغيل الملفات المحفوظة"""
    def __init__(self, master, folder: str):
        super().__init__(master)
        self.title("🎵 Nova System — مُشغّل الوسائط")
        self.geometry("500x600")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        
        try:
            self.after(200, self._set_icon)
        except:
            pass
            
        self.folder = folder
        self.files: list[str] = []
        self.current_idx = -1

        self._build()
        self._load_library()
        self.lift()

    def _set_icon(self):
        try:
            base_dir = get_base_dir()
            icon_path = os.path.join(base_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=75)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="▶", font=("Segoe UI", 22, "bold"), text_color=C["accent"]).place(x=20, y=16)
        ctk.CTkLabel(hdr, text="مُشغّل الوسائط المدمج", font=("Segoe UI", 18, "bold"), text_color=C["txt"]).place(x=55, y=15)
        ctk.CTkLabel(hdr, text="تشغيل وتصفح الملفات المحفوظة بسرعة فائقة", font=("Segoe UI", 11), text_color=C["dim"]).place(x=56, y=42)

        now_card = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        now_card.pack(fill="x", padx=16, pady=(16, 0))

        ctk.CTkLabel(now_card, text="يُشغَّل الآن:", font=("Segoe UI", 10, "bold"), text_color=C["accent"]).pack(anchor="w", padx=14, pady=(10, 0))
        self.now_label = ctk.CTkLabel(now_card, text="—", font=("Segoe UI", 12, "bold"), text_color=C["txt"], wraplength=430, anchor="w")
        self.now_label.pack(fill="x", padx=14, pady=(2, 12))

        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(pady=12)

        btn_cfg = dict(font=("Segoe UI", 12, "bold"), corner_radius=8, width=105, height=40, border_width=1)

        ctk.CTkButton(ctrl, text="⏮ السابق", fg_color=C["input"], hover_color=C["card_hov"], text_color=C["dim"], border_color=C["border"], command=self._prev, **btn_cfg).pack(side="left", padx=6)
        self.play_btn = ctk.CTkButton(ctrl, text="▶ تشغيل", fg_color=C["accent"], hover_color=C["acc_hov"], text_color="white", border_color=C["accent"], command=self._play_current, **btn_cfg)
        self.play_btn.pack(side="left", padx=6)
        ctk.CTkButton(ctrl, text="التالي ⏭", fg_color=C["input"], hover_color=C["card_hov"], text_color=C["dim"], border_color=C["border"], command=self._next, **btn_cfg).pack(side="left", padx=6)

        lib_hdr = ctk.CTkFrame(self, fg_color="transparent")
        lib_hdr.pack(fill="x", padx=18, pady=(10, 4))
        ctk.CTkLabel(lib_hdr, text="📂 الملفات المتاحة", font=("Segoe UI", 12, "bold"), text_color=C["dim"]).pack(side="left")
        ctk.CTkButton(lib_hdr, text="↻ تحديث القائمة", fg_color=C["input"], hover_color=C["card_hov"], text_color=C["dim"], border_color=C["border"], border_width=1, corner_radius=6, width=95, height=28, font=("Segoe UI", 11), command=self._load_library).pack(side="right")

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"], scrollbar_button_color=C["border"])
        self.list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _load_library(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        self.files = []
        for ext in EXTS:
            self.files += glob.glob(os.path.join(self.folder, f"*{ext}"))
        self.files.sort(key=os.path.getmtime, reverse=True)

        if not self.files:
            ctk.CTkLabel(self.list_frame, text="لا توجد ملفات في مجلد التحميل حالياً", font=("Segoe UI", 12), text_color=C["dim"]).pack(pady=40)
            return

        for i, path in enumerate(self.files):
            name = os.path.basename(path)
            ctk.CTkButton(
                self.list_frame,
                text=f"  🎵  {name[:52]}{'…' if len(name) > 52 else ''}",
                font=("Segoe UI", 11),
                fg_color="transparent",
                hover_color=C["input"],
                text_color=C["txt"],
                anchor="w",
                height=38,
                corner_radius=6,
                command=lambda idx=i: self._select_and_play(idx)
            ).pack(fill="x", padx=4, pady=2)

        if self.current_idx == -1 and self.files:
            self.current_idx = 0

    def _select_and_play(self, idx):
        self.current_idx = idx
        self._play_current()

    def _play_current(self):
        if not self.files or self.current_idx < 0:
            return
        path = self.files[self.current_idx]
        self.now_label.configure(text=os.path.basename(path))
        try:
            if os.name == "nt":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذّر تشغيل الملف:\n{e}", parent=self)

    def _prev(self):
        if self.files:
            self.current_idx = (self.current_idx - 1) % len(self.files)
            self._play_current()

    def _next(self):
        if self.files:
            self.current_idx = (self.current_idx + 1) % len(self.files)
            self._play_current()


# ─── النافذة الرئيسية ────────────────────────────────────────────────────────
class YTGrabPro(ctk.CTk):
    """النافذة الرئيسية لتطبيق YT Grab Pro"""
    
    def __init__(self):
        super().__init__()
        self.title("🎬 Nova System — YT Grab Pro")
        self.geometry("1300x820")
        self.minsize(1050, 700)
        self.configure(fg_color=C["bg"])

        try:
            self.after(200, self._set_icon)
        except:
            pass

        self.download_path = os.path.join(Path.home(), "Downloads", "Nova System Pro")
        os.makedirs(self.download_path, exist_ok=True)

        self.is_downloading = False
        self._player_win: PlayerWindow | None = None
        self.is_updating = False

        self._build_ui()
        self.after(1000, self._check_for_updates)

    def _set_icon(self):
        try:
            base_dir = get_base_dir()
            icon_path = os.path.join(base_dir, "icon.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except:
            pass

    # ─── دوال التحديث ──────────────────────────────────────────────────────

    def _check_for_updates(self):
        """التحقق من وجود تحديث تلقائياً"""
        def check():
            data = fetch_github_release()
            if data:
                latest = data.get("tag_name", "")
                if latest and latest != CURRENT_VERSION:
                    self.after(0, lambda: self._show_update_available(latest, data))
        threading.Thread(target=check, daemon=True).start()

    def _manual_check_update(self):
        """التحقق اليدوي من التحديثات"""
        self._log("🔍 جاري التحقق من وجود تحديثات...")
        def check():
            data = fetch_github_release()
            if data:
                latest = data.get("tag_name", "")
                if latest and latest != CURRENT_VERSION:
                    self.after(0, lambda: self._show_update_available(latest, data))
                else:
                    self.after(0, lambda: messagebox.showinfo("لا توجد تحديثات", f"أنت تستخدم أحدث إصدار: {CURRENT_VERSION}"))
            else:
                self.after(0, lambda: messagebox.showerror("خطأ", "تعذر الاتصال بـ GitHub للتحقق من التحديثات."))
        threading.Thread(target=check, daemon=True).start()

    def _show_update_available(self, version, data):
        """عرض إشعار بوجود تحديث جديد"""
        result = messagebox.askyesno(
            "تحديث متاح 🚀",
            f"يتوفر إصدار جديد من البرنامج: {version}\n"
            f"الإصدار الحالي: {CURRENT_VERSION}\n\n"
            "هل تريد تحديث البرنامج الآن؟",
            icon="info"
        )
        if result:
            self._perform_update(version, data)

    def _perform_update(self, version, data):
        """تنفيذ عملية التحديث"""
        if self.is_updating:
            return

        self.is_updating = True
        self._log("🔄 جاري بدء عملية التحديث...")

        download_url = None
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.endswith(".exe") or name.endswith(".zip"):
                download_url = asset.get("browser_download_url")
                break

        if not download_url:
            messagebox.showerror("خطأ", "تعذر العثور على ملف التحديث.")
            self.is_updating = False
            return

        update_win = ctk.CTkToplevel(self)
        update_win.title("جاري التحديث...")
        update_win.geometry("400x150")
        update_win.resizable(False, False)
        update_win.grab_set()

        ctk.CTkLabel(update_win, text="جاري تحميل التحديث...", font=("Segoe UI", 14), text_color=C["txt"]).pack(pady=20)

        progress_bar = ctk.CTkProgressBar(update_win, width=300, height=10)
        progress_bar.pack(pady=10)
        progress_bar.set(0)

        status_label = ctk.CTkLabel(update_win, text="0%", font=("Segoe UI", 11), text_color=C["dim"])
        status_label.pack(pady=5)

        def update_progress(pct):
            progress_bar.set(pct / 100)
            status_label.configure(text=f"{pct}%")
            update_win.update_idletasks()

        def download_thread():
            try:
                self._log(f"📥 جاري تحميل التحديث...")
                
                tmp_dir = tempfile.mkdtemp()
                if download_url.endswith(".exe"):
                    tmp_path = os.path.join(tmp_dir, "update.exe")
                else:
                    tmp_path = os.path.join(tmp_dir, "update.zip")

                download_file(download_url, tmp_path, update_progress)
                self._log("✅ تم تحميل التحديث بنجاح.")
                
                self.after(0, lambda: self._install_update(tmp_path, version, update_win))

            except Exception as e:
                self._log(f"❌ فشل التحديث: {e}")
                self.after(0, lambda: messagebox.showerror("خطأ", f"فشل التحديث:\n{e}"))
                self.after(0, update_win.destroy)
                self.is_updating = False

        threading.Thread(target=download_thread, daemon=True).start()

    def _install_update(self, update_file, version, update_win):
        """تثبيت التحديث"""
        try:
            update_win.destroy()
            
            current_exe = sys.argv[0]
            
            if update_file.endswith(".zip"):
                extract_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(update_file, 'r') as z:
                    z.extractall(extract_dir)
                exe_files = glob.glob(os.path.join(extract_dir, "*.exe"))
                if not exe_files:
                    raise Exception("لم يتم العثور على ملف EXE")
                new_exe = exe_files[0]
            else:
                new_exe = update_file

            bat_path = os.path.join(tempfile.gettempdir(), "update.bat")
            with open(bat_path, 'w', encoding='utf-8') as f:
                f.write(f'''@echo off
timeout /t 2 /nobreak > nul
copy /Y "{new_exe}" "{current_exe}"
start "" "{current_exe}"
rmdir /S /Q "{os.path.dirname(update_file)}" 2>nul
del /Q "%~f0"
''')

            self._log("🔄 جاري إعادة التشغيل لتطبيق التحديث...")
            messagebox.showinfo("تحديث", "سيتم إعادة تشغيل التطبيق لتطبيق التحديث.")
            
            subprocess.Popen([bat_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            self.quit()
            sys.exit(0)

        except Exception as e:
            self._log(f"❌ فشل التثبيت: {e}")
            messagebox.showerror("خطأ", f"فشل تثبيت التحديث:\n{e}")
            self.is_updating = False
            if update_win.winfo_exists():
                update_win.destroy()

    # ─── واجهة المستخدم ────────────────────────────────────────────────────

    def _build_ui(self):
        """بناء واجهة المستخدم الرئيسية"""
        
        hdr = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=80, border_width=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        ctk.CTkLabel(hdr, text="🎬", font=("Segoe UI", 24), text_color=C["accent"]).place(x=20, y=24)
        ctk.CTkLabel(hdr, text="NOVA", font=("Segoe UI", 26, "bold"), text_color=C["txt"]).place(x=60, y=22)
        ctk.CTkLabel(hdr, text="GRAB PRO", font=("Segoe UI", 26, "bold"), text_color=C["accent"]).place(x=141, y=22)
        ctk.CTkLabel(hdr, text=f"الإصدار {CURRENT_VERSION} | منظومة التحميل الذكية", font=("Segoe UI", 11), text_color=C["dim"]).place(x=60, y=53)

        def _open_github():
            webbrowser.open("https://github.com/abushama1-ar/YT-GRAP-PRO")

        def _open_support():
            webbrowser.open("https://discord.gg/YUKXKBmnaT")

        btn_x = -20
        ctk.CTkButton(hdr, text="🔄 تحديث", font=("Segoe UI", 11, "bold"), fg_color=C["gold"], hover_color="#D97706", text_color="#121212", border_width=0, corner_radius=8, width=95, height=32, command=self._manual_check_update).place(relx=1.0, x=btn_x, y=24, anchor="ne")
        btn_x -= 110
        ctk.CTkButton(hdr, text="💬 الدعم", font=("Segoe UI", 11, "bold"), fg_color=C["input"], hover_color=C["card_hov"], text_color=C["txt"], border_color=C["border"], border_width=1, corner_radius=8, width=95, height=32, command=_open_support).place(relx=1.0, x=btn_x, y=24, anchor="ne")
        btn_x -= 110
        ctk.CTkButton(hdr, text="🔗 GitHub", font=("Segoe UI", 11, "bold"), fg_color=C["input"], hover_color=C["card_hov"], text_color=C["txt"], border_color=C["border"], border_width=1, corner_radius=8, width=95, height=32, command=_open_github).place(relx=1.0, x=btn_x, y=24, anchor="ne")

        body = ctk.CTkScrollableFrame(self, fg_color=C["bg"], scrollbar_fg_color=C["bg"], scrollbar_button_color=C["border"])
        body.pack(fill="both", expand=True)

        # ─── 1. رابط الفيديو ──────────────────────────────────────────────
        self._lbl(body, "🔗 رابط الفيديو المستهدف")
        url_row = ctk.CTkFrame(body, fg_color="transparent")
        url_row.pack(fill="x", padx=28, pady=(6, 0))

        self.url_entry = ctk.CTkEntry(
            url_row, placeholder_text="الصق رابط الفيديو هنا...",
            font=("Segoe UI", 12), fg_color=C["card"], border_color=C["border"],
            border_width=1, text_color=C["txt"], placeholder_text_color=C["dim"],
            corner_radius=10, height=48
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.url_entry.bind("<Control-v>", lambda e: self._paste_url())
        self.url_entry.bind("<Control-V>", lambda e: self._paste_url())

        ctk.CTkButton(
            url_row, text="📋 لصق الرابط", font=("Segoe UI", 12, "bold"),
            fg_color=C["input"], hover_color=C["card_hov"], border_color=C["border"],
            border_width=1, text_color=C["txt"], corner_radius=10, width=120, height=48,
            command=self._paste_url
        ).pack(side="left")

        # ─── 2. جودة التحميل ──────────────────────────────────────────────
        self._lbl(body, "🎬 دقة التحميل والصيغة المطلوبة")
        q_frame = ctk.CTkFrame(body, fg_color="transparent")
        q_frame.pack(fill="x", padx=28, pady=(6, 0))

        self.quality_var = ctk.StringVar(value="720p")
        self._q_btns: dict[str, ctk.CTkButton] = {}

        for lbl in ["360p", "720p", "1080p", "4K", "MP3"]:
            btn = ctk.CTkButton(
                q_frame, text=lbl, font=("Segoe UI", 11, "bold"),
                fg_color=C["card"], hover_color=C["card_hov"],
                border_color=C["border"], border_width=1,
                text_color=C["dim"], corner_radius=10, width=135, height=44,
                command=lambda l=lbl: self._pick_quality(l)
            )
            btn.pack(side="left", padx=(0, 10))
            self._q_btns[lbl] = btn
        self._pick_quality("720p")

        # ─── 3. مجلد الحفظ ─────────────────────────────────────────────────
        self._lbl(body, "📁 مجلد الحفظ الحالي")
        folder_row = ctk.CTkFrame(body, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        folder_row.pack(fill="x", padx=28, pady=(6, 0))

        self.folder_label = ctk.CTkLabel(folder_row, text=self.download_path, font=("Consolas", 11), text_color=C["dim"], anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True, padx=16, pady=14)

        ctk.CTkButton(folder_row, text="تغيير المجلد", font=("Segoe UI", 11, "bold"), fg_color=C["input"], hover_color=C["card_hov"], text_color=C["txt"], border_color=C["border"], border_width=1, corner_radius=8, width=105, height=34, command=self._change_folder).pack(side="right", padx=12, pady=12)

        # ─── 4. مؤشر التقدم ─────────────────────────────────────────────────
        self._lbl(body, "📊 مؤشر التقدم والحالة")
        prog = ctk.CTkFrame(body, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        prog.pack(fill="x", padx=28, pady=(6, 0))

        self.status_lbl = ctk.CTkLabel(prog, text="الأداة جاهزة واستعداد تام للتحميل...", font=("Segoe UI", 12, "bold"), text_color=C["dim"], anchor="w")
        self.status_lbl.pack(fill="x", padx=18, pady=(14, 6))

        self.prog_bar = ctk.CTkProgressBar(prog, fg_color=C["input"], progress_color=C["accent"], corner_radius=6, height=10)
        self.prog_bar.pack(fill="x", padx=18, pady=(0, 6))
        self.prog_bar.set(0)

        self.pct_lbl = ctk.CTkLabel(prog, text="0%", font=("Consolas", 12, "bold"), text_color=C["dim"])
        self.pct_lbl.pack(anchor="e", padx=18, pady=(0, 14))

        # ─── 5. سجل العمليات ───────────────────────────────────────────────
        self._lbl(body, "📝 سجل عمليات النظام المباشر")
        self.log_box = ctk.CTkTextbox(body, height=130, font=("Consolas", 11), fg_color=C["card"], text_color=C["dim"], border_color=C["border"], border_width=1, corner_radius=12, wrap="word")
        self.log_box.pack(fill="x", padx=28, pady=(6, 28))
        self._log("✔ Nova System Core — Ready.")

        # ─── شريط الأزرار السفلي ───────────────────────────────────────────
        bar = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=0, height=85)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        ctk.CTkFrame(bar, fg_color=C["border"], height=1, corner_radius=0).pack(fill="x")

        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(expand=True)

        btn_action_cfg = dict(font=("Segoe UI", 13, "bold"), corner_radius=10, height=44)

        self.dl_btn = ctk.CTkButton(inner, text="⬇ بدء التحميل الفوري", fg_color=C["accent"], hover_color=C["acc_hov"], text_color="white", width=170, command=self._start_download, **btn_action_cfg)
        self.dl_btn.pack(side="left", padx=8, pady=20)

        self.stop_btn = ctk.CTkButton(inner, text="⏹ إيقاف", fg_color=C["input"], hover_color=C["card_hov"], text_color=C["dim"], border_color=C["border"], border_width=1, width=110, state="disabled", command=self._stop_download, **btn_action_cfg)
        self.stop_btn.pack(side="left", padx=8, pady=20)

        ctk.CTkButton(inner, text="▶ المشغّل المدمج", fg_color=C["gold"], hover_color="#D97706", text_color="#121212", width=140, command=self._open_player, **btn_action_cfg).pack(side="left", padx=8, pady=20)

        ctk.CTkButton(inner, text="📁 المجلد", fg_color=C["input"], hover_color=C["card_hov"], text_color=C["dim"], border_color=C["border"], border_width=1, width=70, command=self._open_folder, **btn_action_cfg).pack(side="left", padx=8, pady=20)

    def _lbl(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=("Segoe UI", 11, "bold"), text_color=C["dim"], anchor="w").pack(fill="x", padx=28, pady=(16, 0))

    def _pick_quality(self, label):
        self.quality_var.set(label)
        for l, b in self._q_btns.items():
            active = l == label
            b.configure(
                fg_color=C["accent"] if active else C["card"],
                text_color="white" if active else C["dim"],
                border_color=C["accent"] if active else C["border"]
            )

    def _log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _paste_url(self):
        try:
            url = self.clipboard_get()
            if url:
                self.url_entry.delete(0, "end")
                self.url_entry.insert(0, url.strip())
                self._log("📋 تم لصق الرابط من الحافظة بنجاح.")
        except Exception:
            try:
                self.url_entry.event_generate("<<Paste>>")
                self._log("📋 تم اللصق عبر اختصار النظام.")
            except Exception:
                self._log("⚠ تعذّر اللصق تلقائياً، يرجى المحاولة يدوياً.")

    def _change_folder(self):
        f = filedialog.askdirectory(initialdir=self.download_path)
        if f:
            self.download_path = f
            self.folder_label.configure(text=f)
            self._log(f"📁 تم تحديث مجلد الحفظ إلى: {f}")
            if self._player_win and self._player_win.winfo_exists():
                self._player_win.folder = f
                self._player_win._load_library()

    def _open_folder(self):
        try:
            if os.name == "nt":
                os.startfile(self.download_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", self.download_path])
            else:
                subprocess.run(["xdg-open", self.download_path])
        except Exception as e:
            self._log(f"❌ {e}")

    def _open_player(self):
        if self._player_win and self._player_win.winfo_exists():
            self._player_win._load_library()
            self._player_win.lift()
            self._player_win.focus_force()
        else:
            self._player_win = PlayerWindow(self, self.download_path)

    def _start_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("تنبيه", "الرجاء إدخال رابط الفيديو أولاً!")
            return

        self.is_downloading = True
        self.dl_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.prog_bar.set(0)
        self.pct_lbl.configure(text="0%", text_color=C["dim"])
        self.status_lbl.configure(text="🔄 جاري الاتصال بالخادم وتحليل الرابط...", text_color=C["dim"])
        
        threading.Thread(target=self._dl_thread, args=(url,), daemon=True).start()

    def _stop_download(self):
        self.is_downloading = False
        self._log("⏹ تم إيقاف التحميل بواسطة المستخدم.")
        self._reset_ui()

    def _reset_ui(self):
        self.dl_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.status_lbl.configure(text="الأداة جاهزة واستعداد تام للتحميل...", text_color=C["dim"])

    def _dl_thread(self, url):
        quality = self.quality_var.get()

        fmt_map = {
            "360p":  "best[height<=360]/best",
            "720p":  "best[height<=720]/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best",
            "4K":    "bestvideo[height<=2160]+bestaudio/best",
            "MP3":   "bestaudio/best",
        }

        opts = {
            "outtmpl":        os.path.join(self.download_path, "%(title)s.%(ext)s"),
            "format":         fmt_map.get(quality, "best"),
            "progress_hooks": [self._hook],
            "noplaylist":     True,
            "quiet":          True,
            "no_warnings":    True,
        }

        try:
            opts["extractor_args"] = {"youtube": {"player_client": ["android", "web"]}}
        except Exception:
            pass

        # ─── البحث عن ffmpeg في المجلد المضمن ─────────────────────────────
        ffmpeg_path = get_ffmpeg_path()
        if ffmpeg_path:
            opts["ffmpeg_location"] = os.path.dirname(ffmpeg_path)
            self._log(f"✅ تم العثور على FFmpeg: {ffmpeg_path}")
        else:
            self._log("⚠ لم يتم العثور على FFmpeg، قد لا تعمل بعض الميزات.")

        if "MP3" in quality:
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "فيديو")[:55]
                self.after(0, lambda t=title: self._log(f"بدء التحميل: {t}"))
                
                if not self.is_downloading:
                    self.after(0, self._reset_ui)
                    return
                
                ydl.download([url])

            if self.is_downloading:
                self.after(0, lambda: self.prog_bar.set(1))
                self.after(0, lambda: self.pct_lbl.configure(text="100%", text_color=C["ok"]))
                self.after(0, lambda: self.status_lbl.configure(text="✅ اكتمل التحميل بنجاح!", text_color=C["ok"]))
                self.after(0, lambda: self._log(f"✅ تم حفظ الملف في: {self.download_path}"))
                self.after(400, self._refresh_player_if_open)
                
        except Exception as e:
            err = str(e)[:120]
            self.after(0, lambda: self._log(f"❌ خطأ: {err}"))
            self.after(0, lambda: self.status_lbl.configure(text="❌ فشلت عملية التحميل", text_color="#EF4444"))
        finally:
            self.is_downloading = False
            self.after(0, self._reset_ui)

    def _hook(self, d):
        if not self.is_downloading:
            raise Exception("تم الإيقاف")
            
        if d["status"] == "downloading":
            raw = d.get("_percent_str", "0%").strip().replace("%", "")
            try:
                pct = float(raw) / 100
                speed = d.get("_speed_str", "")
                eta = d.get("_eta_str", "")
                
                self.after(0, lambda p=pct: self.prog_bar.set(p))
                self.after(0, lambda p=pct: self.pct_lbl.configure(text=f"{p*100:.0f}%"))
                self.after(0, lambda s=speed, e=eta: self.status_lbl.configure(text=f"⬇ السرعة: {s}  |  المتبقي: {e}"))
            except Exception:
                pass

    def _refresh_player_if_open(self):
        if self._player_win and self._player_win.winfo_exists():
            self._player_win._load_library()


# ─── نقطة الدخول الرئيسية ────────────────────────────────────────────────────
if __name__ == "__main__":
    app = YTGrabPro()
    app.mainloop()