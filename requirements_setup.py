import importlib.util
import os
import subprocess
import sys


REQUIRED_MODULES = (
    "cv2",
    "psutil",
    "PIL",
    "mss",
    "win32gui",
    "win32ts",
    "win32con",
    "win32ui",
    "win32api",
)


def ensure_requirements():
    missing_modules = [
        module for module in REQUIRED_MODULES
        if importlib.util.find_spec(module) is None
    ]
    if not missing_modules:
        return

    requirements_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.isfile(requirements_file):
        raise FileNotFoundError(f"Requirements file not found: {requirements_file}")

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-r", requirements_file],
        creationflags=creation_flags,
    )
