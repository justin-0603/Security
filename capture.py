# Required modules for system operations, time tracking, image processing, process monitoring, and Windows API.
import cv2
import datetime
import json
import os
import sys
import time
import subprocess
import threading
import win32gui
import win32ts
import win32con
import ctypes

# Check for required libraries and install them if missing silently without spawning console windows.
def check_and_install_requirements():
    required_packages = ["cv2", "psutil", "pywin32", "PIL", "mss"]
    CREATE_NO_WINDOW = 0x08000000
    
    for package in required_packages:
        try:
            if package == "PIL":
                import PIL
            else:
                __import__(package)
        except ImportError:
            pkg_name = "opencv-python" if package == "cv2" else ("pywin32" if package == "pywin32" else ("Pillow" if package == "PIL" else package))
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg_name],
                creationflags=CREATE_NO_WINDOW
            )

check_and_install_requirements()

from PIL import ImageGrab
import mss
import psutil

# Absolute directory paths relative to this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "Logs")
SCREENSHOT_DIR = os.path.join(LOG_DIR, "Screenshots")
WEBCAM_DIR = os.path.join(LOG_DIR, "Webcams")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

# Default settings fallback
DEFAULT_CONFIG = {
    "target_apps": ["chrome.exe", "msedge.exe", "discord.exe", "javaw.exe"],
    "capture_interval_seconds": 5
}

# Dynamically load configuration from config.json
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_CONFIG

# Global state flags
is_authenticated = False
stop_event = threading.Event()

# Ensure logs directory and categorized subdirectories explicitly exist
def ensure_directories():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(WEBCAM_DIR, exist_ok=True)

ensure_directories()

# Trigger Windows native toast notification
def show_notification(title, message):
    try:
        ps_script = f'''
        [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
        $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
        $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
        $objNotifyIcon.BalloonTipTitle = "{title}"
        $objNotifyIcon.BalloonTipText = "{message}"
        $objNotifyIcon.Visible = $True
        $objNotifyIcon.ShowBalloonTip(3000)
        Start-Sleep -s 3
        $objNotifyIcon.Dispose()
        '''
        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(["powershell", "-Command", ps_script], creationflags=CREATE_NO_WINDOW)
    except Exception:
        pass

# Force file saving strictly inside SCREENSHOT_DIR
def save_desktop_screenshot(target_file_path):
    # Method 1: Pillow ImageGrab (Primary)
    try:
        img = ImageGrab.grab(all_screens=True)
        img.save(target_file_path, "PNG")
        if os.path.exists(target_file_path) and os.path.getsize(target_file_path) > 0:
            return True
    except Exception:
        pass

    # Method 2: mss with explicit file path output
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            mss.tools.to_png(sct_img.rgb, sct_img.size, output=target_file_path)
            if os.path.exists(target_file_path) and os.path.getsize(target_file_path) > 0:
                return True
    except Exception:
        pass

    return False

# Capture webcam photo, desktop screenshot, and write log timestamp into organized subfolders
def record_evidence(prefix="webcam"):
    ensure_directories()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(LOG_DIR, "access_log.txt")
    
    # Save screenshot strictly in Logs/Screenshots directory
    screenshot_path = os.path.join(SCREENSHOT_DIR, f"screen_{prefix}_{now_str}.png")
    success = save_desktop_screenshot(screenshot_path)

    try:
        with open(log_file_path, "a", encoding="utf-8") as f:
            if success:
                f.write(f"[{prefix.upper()} Captured] {now_str}\n")
            else:
                f.write(f"[{prefix.upper()} Failed] Screenshot capture error at {now_str}\n")
    except Exception:
        pass

    # Save webcam photo strictly in Logs/Webcams directory
    if prefix == "webcam":
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                cap.release()
                if ret and frame is not None:
                    webcam_path = os.path.join(WEBCAM_DIR, f"webcam_{now_str}.jpg")
                    cv2.imwrite(webcam_path, frame)
            else:
                cap.release()
        except Exception:
            pass

def is_target_app_running(target_apps):
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in [app.lower() for app in target_apps]:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def run_surveillance_sequence():
    global is_authenticated
    
    if is_authenticated:
        return

    stop_event.clear()

    if not is_authenticated and not stop_event.is_set():
        record_evidence(prefix="webcam")

    while not stop_event.is_set() and not is_authenticated:
        config = load_config()
        target_apps = config.get("target_apps", DEFAULT_CONFIG["target_apps"])
        interval_seconds = config.get("capture_interval_seconds", DEFAULT_CONFIG["capture_interval_seconds"])

        if is_target_app_running(target_apps):
            record_evidence(prefix="app_active")
            
        if stop_event.wait(timeout=interval_seconds):
            break

HOTKEY_ID = 1

def window_proc(hwnd, msg, wparam, lparam):
    global is_authenticated
    WM_WTSSESSION_CHANGE = 0x02B1
    WTS_SESSION_UNLOCK = 0x8
    WTS_SESSION_LOCK = 0x7

    if msg == win32con.WM_HOTKEY:
        if wparam == HOTKEY_ID:
            is_authenticated = True
            stop_event.set()
            show_notification("Security Surveillance", "Authentication verified. Surveillance stopped immediately.")

    elif msg == WM_WTSSESSION_CHANGE:
        if wparam == WTS_SESSION_LOCK:
            is_authenticated = False
            stop_event.set()
        elif wparam == WTS_SESSION_UNLOCK:
            threading.Thread(target=run_surveillance_sequence, daemon=True).start()

    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

def start_session_listener():
    threading.Thread(target=run_surveillance_sequence, daemon=True).start()

    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = window_proc
    wc.lpszClassName = "SessionLockMonitorClass"
    hinst = wc.hInstance = win32gui.GetModuleHandle(None)
    class_atom = win32gui.RegisterClass(wc)
    hwnd = win32gui.CreateWindow(class_atom, "SessionLockMonitorWindow", 0, 0, 0, 0, 0, 0, 0, hinst, None)
    
    MOD_ALT = 0x0001
    MOD_CONTROL = 0x0002
    VK_K = 0x4B
    
    user32 = ctypes.windll.user32
    user32.RegisterHotKey(hwnd, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_K)

    win32ts.WTSRegisterSessionNotification(hwnd, win32ts.NOTIFY_FOR_THIS_SESSION)
    win32gui.PumpMessages()

if __name__ == "__main__":
    start_session_listener()