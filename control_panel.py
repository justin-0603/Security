# Required modules for Tkinter GUI control panel, process search, icon extraction, and logging utilities.
import json
import os
import shutil
import subprocess
import sys

from requirements_setup import ensure_requirements

ensure_requirements()

import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
import psutil
import win32gui
import win32ui
import win32con
import win32api

# Absolute directory paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "Logs")
SCREENSHOT_DIR = os.path.join(LOG_DIR, "Screenshots")
WEBCAM_DIR = os.path.join(LOG_DIR, "Webcams")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_TXT_FILE = os.path.join(LOG_DIR, "access_log.txt")

DEFAULT_CONFIG = {
    "target_apps": ["chrome.exe", "msedge.exe", "discord.exe", "javaw.exe"],
    "capture_interval_seconds": 5
}

# Ensure directories exist prior to GUI launch
def ensure_directories():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(WEBCAM_DIR, exist_ok=True)

# Extract icon from executable path or process name
def get_icon_from_file(file_path_or_name):
    try:
        path = file_path_or_name
        if not os.path.exists(path):
            for proc in psutil.process_iter(['name', 'exe']):
                if proc.info['name'] and proc.info['name'].lower() == file_path_or_name.lower():
                    if proc.info['exe'] and os.path.exists(proc.info['exe']):
                        path = proc.info['exe']
                        break

        if not os.path.exists(path):
            return None

        ico_x = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYSMICON)

        large, small = win32gui.ExtractIconEx(path, 0)
        hicon = small[0] if small else (large[0] if large else None)
        if not hicon:
            return None

        if large and small:
            win32gui.DestroyIcon(large[0])

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)

        win32gui.DrawIconEx(hdc_mem.GetSafeHdc(), 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        
        bmpinfo = hbmp.GetInfo()
        bmpbits = hbmp.GetBitmapBits(True)
        img = Image.frombuffer('RGBA', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpbits, 'raw', 'BGRA', 0, 1)

        win32gui.DestroyIcon(hicon)
        hdc.DeleteDC()
        hdc_mem.DeleteDC()
        win32gui.ReleaseDC(0, win32gui.GetDC(0))

        img = img.resize((16, 16), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

# Process Search and Selection Window
class ProcessSearchWindow(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.title("Search and Select Process")
        self.geometry("480x450")
        self.resizable(False, False)
        self.callback = callback
        self.icon_cache = {}

        self.create_widgets()
        self.load_running_processes()

    def create_widgets(self):
        lbl_search = ttk.Label(self, text="Search Process Name:")
        lbl_search.pack(anchor="w", padx=15, pady=(10, 2))

        self.entry_search = ttk.Entry(self)
        self.entry_search.pack(fill="x", padx=15, pady=5)
        self.entry_search.bind("<KeyRelease>", self.filter_processes)

        frame_list = ttk.Frame(self)
        frame_list.pack(fill="both", expand=True, padx=15, pady=5)

        self.tree = ttk.Treeview(frame_list, columns=("Name", "PID"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Icon", anchor="center")
        self.tree.column("#0", width=50, stretch=False, anchor="center")
        self.tree.heading("Name", text="Process Name", anchor="w")
        self.tree.column("Name", width=270, anchor="w")
        self.tree.heading("PID", text="PID", anchor="center")
        self.tree.column("PID", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_select = ttk.Button(self, text="Add Selected Process", command=self.select_process)
        btn_select.pack(pady=10)

    def load_running_processes(self):
        self.processes = []
        seen_names = set()

        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                name = proc.info['name']
                if name and name.lower() not in seen_names:
                    seen_names.add(name.lower())
                    exe_path = proc.info['exe'] if proc.info['exe'] else name
                    self.processes.append((name, proc.info['pid'], exe_path))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        self.processes.sort(key=lambda x: x[0].lower())
        self.display_processes(self.processes)

    def display_processes(self, proc_list):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for name, pid, exe_path in proc_list:
            if name not in self.icon_cache:
                icon = get_icon_from_file(exe_path)
                self.icon_cache[name] = icon
            else:
                icon = self.icon_cache[name]

            if icon:
                self.tree.insert("", "end", image=icon, values=(name, pid))
            else:
                self.tree.insert("", "end", values=(name, pid))

    def filter_processes(self, event):
        query = self.entry_search.get().lower()
        filtered = [p for p in self.processes if query in p[0].lower()]
        self.display_processes(filtered)

    def select_process(self):
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            proc_name = item['values'][0]
            self.callback(proc_name)
            self.destroy()

# Main Control Panel GUI
class ControlPanelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_directories()
        self.title("Surveillance Management Panel")
        self.geometry("520x660")
        self.resizable(False, False)
        self.icon_cache = {}

        self.create_widgets()
        self.load_settings()

    def create_widgets(self):
        header = ttk.Label(self, text="Security Surveillance Control Panel", font=("Segoe UI", 14, "bold"))
        header.pack(pady=10)

        # Target Apps Section
        frame_apps = ttk.LabelFrame(self, text=" Target Application List ")
        frame_apps.pack(fill="both", expand=True, padx=20, pady=5)

        frame_tree = ttk.Frame(frame_apps)
        frame_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_apps = ttk.Treeview(frame_tree, columns=("ProcessName"), show="tree headings", selectmode="browse")
        self.tree_apps.heading("#0", text="Icon", anchor="center")
        self.tree_apps.column("#0", width=60, stretch=False, anchor="center")
        self.tree_apps.heading("ProcessName", text="Executable File Name", anchor="w")
        self.tree_apps.column("ProcessName", width=380, anchor="w")

        scrollbar_apps = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_apps.yview)
        self.tree_apps.configure(yscrollcommand=scrollbar_apps.set)

        self.tree_apps.pack(side="left", fill="both", expand=True)
        scrollbar_apps.pack(side="right", fill="y")

        frame_app_buttons = ttk.Frame(frame_apps)
        frame_app_buttons.pack(fill="x", padx=10, pady=5)

        btn_add_search = ttk.Button(frame_app_buttons, text="Search & Add Process", command=self.open_search_window)
        btn_add_search.pack(side="left", padx=5)

        btn_remove_app = ttk.Button(frame_app_buttons, text="Remove Selected", command=self.remove_target_app)
        btn_remove_app.pack(side="left", padx=5)

        # Timing Settings Section
        frame_times = ttk.LabelFrame(self, text=" Timing Settings (Seconds) ")
        frame_times.pack(fill="x", padx=20, pady=5)

        lbl_interval = ttk.Label(frame_times, text="Capture Interval:")
        lbl_interval.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.entry_interval = ttk.Entry(frame_times, width=12)
        self.entry_interval.grid(row=0, column=1, padx=10, pady=8)

        btn_save = ttk.Button(self, text="Save Settings", command=self.save_settings)
        btn_save.pack(pady=8)

        # Storage & Cleanup Section
        frame_logs = ttk.LabelFrame(self, text=" Data & Folder Management ")
        frame_logs.pack(fill="x", padx=20, pady=5)

        btn_open_folder = ttk.Button(frame_logs, text="Open Logs Directory", command=self.open_logs_folder)
        btn_open_folder.pack(fill="x", padx=10, pady=3)

        btn_clear_text = ttk.Button(frame_logs, text="Delete Access Log Text File", command=self.clear_access_log_txt)
        btn_clear_text.pack(fill="x", padx=10, pady=3)

        btn_clear_screenshots = ttk.Button(frame_logs, text="Delete All Screenshots", command=self.clear_screenshots)
        btn_clear_screenshots.pack(fill="x", padx=10, pady=3)

        btn_clear_webcams = ttk.Button(frame_logs, text="Delete All Webcam Photos", command=self.clear_webcams)
        btn_clear_webcams.pack(fill="x", padx=10, pady=3)

        btn_clear_all = ttk.Button(frame_logs, text="Clear Entire Logs Folder", command=self.clear_all_logs)
        btn_clear_all.pack(fill="x", padx=10, pady=3)

    def load_settings(self):
        config = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config.update(json.load(f))
            except Exception:
                pass

        self.target_apps = config.get("target_apps", [])
        self.update_apps_treeview()

        self.entry_interval.delete(0, tk.END)
        self.entry_interval.insert(0, str(config.get("capture_interval_seconds", 5)))

    def update_apps_treeview(self):
        for item in self.tree_apps.get_children():
            self.tree_apps.delete(item)

        for app_name in self.target_apps:
            if app_name not in self.icon_cache:
                icon = get_icon_from_file(app_name)
                self.icon_cache[app_name] = icon
            else:
                icon = self.icon_cache[app_name]

            if icon:
                self.tree_apps.insert("", "end", image=icon, values=(app_name,))
            else:
                self.tree_apps.insert("", "end", values=(app_name,))

    def open_search_window(self):
        ProcessSearchWindow(self, self.add_target_app)

    def add_target_app(self, proc_name):
        if proc_name and proc_name.lower() not in [app.lower() for app in self.target_apps]:
            self.target_apps.append(proc_name)
            self.update_apps_treeview()

    def remove_target_app(self):
        selected = self.tree_apps.selection()
        if selected:
            item = self.tree_apps.item(selected[0])
            app_name = item['values'][0]
            self.target_apps = [app for app in self.target_apps if app.lower() != str(app_name).lower()]
            self.update_apps_treeview()

    def save_settings(self):
        try:
            interval = int(self.entry_interval.get())

            config = {
                "target_apps": self.target_apps,
                "capture_interval_seconds": interval
            }

            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)

            messagebox.showinfo("Success", "Settings successfully saved to config.json!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid integer for capture interval.")

    def open_logs_folder(self):
        ensure_directories()
        os.startfile(LOG_DIR)

    def _delete_files_in_dir(self, directory):
        if not os.path.exists(directory):
            return 0
        count = 0
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    count += 1
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    count += 1
            except Exception:
                pass
        return count

    def clear_access_log_txt(self):
        if os.path.exists(LOG_TXT_FILE):
            if messagebox.askyesno("Confirm", "Are you sure you want to delete access_log.txt?"):
                try:
                    os.remove(LOG_TXT_FILE)
                    messagebox.showinfo("Completed", "access_log.txt successfully removed.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete access_log.txt: {e}")
        else:
            messagebox.showinfo("Notice", "access_log.txt does not exist.")

    def clear_screenshots(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all screenshot files?"):
            removed = self._delete_files_in_dir(SCREENSHOT_DIR)
            messagebox.showinfo("Completed", f"Removed {removed} screenshot file(s).")

    def clear_webcams(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all webcam photo files?"):
            removed = self._delete_files_in_dir(WEBCAM_DIR)
            messagebox.showinfo("Completed", f"Removed {removed} webcam photo file(s).")

    def clear_all_logs(self):
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete ALL logs, screenshots, and webcam photos?"):
            removed = self._delete_files_in_dir(LOG_DIR)
            ensure_directories()
            messagebox.showinfo("Completed", f"Cleared entire Logs directory ({removed} items deleted).")

if __name__ == "__main__":
    app = ControlPanelApp()
    app.mainloop()