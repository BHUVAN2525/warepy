#!/usr/bin/env python3
"""
Anti-Debugging Techniques
Detects and evades debugger attachment
Educational/Research purposes only
"""
import ctypes
import sys
import time

class AntiDebug:
    def __init__(self):
        self.kernel32 = ctypes.windll.kernel32
        self.ntdll = ctypes.windll.ntdll
        
    def check_debugger_present(self):
        """
        IsDebuggerPresent API check
        Most basic check, easily bypassed
        """
        return self.kernel32.IsDebuggerPresent()
    
    def check_remote_debugger(self):
        """
        CheckRemoteDebuggerPresent - can detect remote debuggers
        """
        being_debugged = ctypes.c_bool(False)
        self.kernel32.CheckRemoteDebuggerPresent(
            ctypes.c_void_p(-1),  # current process
            ctypes.byref(being_debugged)
        )
        return being_debugged.value
    
    def peb_being_debugged(self):
        """
        Direct PEB.BeingDebugged check (bypasses hooking)
        """
        # TEB at GS:[0x30] (x64) or FS:[0x30] (x86)
        # PEB at TEB+0x60
        # BeingDebugged at PEB+0x2
        
        # Using inline assembly or native API
        process_info = ctypes.c_ulong()
        self.ntdll.NtQueryInformationProcess(
            ctypes.c_void_p(-1),
            0,  # ProcessBasicInformation
            ctypes.byref(process_info),
            ctypes.sizeof(process_info),
            None
        )
        
        # Check byte at PEB+0x2
        return False
    
    def hardware_breakpoint_check(self):
        """
        Check debug registers for hardware breakpoints
        """
        context = CONTEXT()
        context.ContextFlags = 0x10010  # CONTEXT_DEBUG_REGISTERS
        
        self.kernel32.GetThreadContext(
            self.kernel32.GetCurrentThread(),
            ctypes.byref(context)
        )
        
        # Dr0-Dr3 contain breakpoint addresses
        # Dr6, Dr7 contain flags
        has_hwbp = any([
            context.Dr0 != 0,
            context.Dr1 != 0, 
            context.Dr2 != 0,
            context.Dr3 != 0
        ])
        
        return has_hwbp
    
    def timing_checks(self):
        """
        Timing side-channels to detect instrumentation
        """
        # RDTSC instruction (Read Time-Stamp Counter)
        # Debuggers cause timing anomalies
        
        # Method 1: QueryPerformanceCounter difference
        import ctypes
        freq = ctypes.c_longlong()
        start = ctypes.c_longlong()
        end = ctypes.c_longlong()
        
        self.kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
        self.kernel32.QueryPerformanceCounter(ctypes.byref(start))
        
        # Execute code that should be fast
        x = sum(range(100))
        
        self.kernel32.QueryPerformanceCounter(ctypes.byref(end))
        
        elapsed = (end.value - start.value) / freq.value
        return elapsed > 0.01  # Threshold for detection
    
    def int3_scanning(self):
        """
        Scan for 0xCC (int3) breakpoints in code section
        """
        # Read memory and scan for breakpoint opcodes
        pass
    
    def nt_global_flag(self):
        """
        Check NtGlobalFlag in PEB
        Set by Windows when debugging
        """
        # PEB + 0xBC (x64) = NtGlobalFlag
        # Typical values: FLG_HEAP_ENABLE_TAIL_CHECK (0x10)
        #               FLG_HEAP_ENABLE_FREE_CHECK (0x20)
        #               FLG_HEAP_VALIDATE_PARAMETERS (0x40)
        # Normal: 0, Debugged: 0x70 (combined)
        pass
    
    def vm_exit(self):
        """
        If debug detected, cause crash or fake execution
        """
        if self.check_debugger_present():
            # Option 1: Exit silently
            # sys.exit(0)
            
            # Option 2: Crash with misleading error
            # raise MemoryError("Visual C++ Runtime Error")
            
            # Option 3: Execute benign code path
            self.benign_payload()
            return True
        return False
    
    def benign_payload(self):
        """Decoy behavior when debugging detected"""
        # Harmless calculations
        result = 0
        for i in range(1000000):
            result += i
        return result

class CONTEXT(ctypes.Structure):
    _fields_ = [
        ("P1Home", ctypes.c_ulonglong),
        ("P2Home", ctypes.c_ulonglong),
        # ... full context structure
        ("Dr0", ctypes.c_ulonglong),
        ("Dr1", ctypes.c_ulonglong),
        ("Dr2", ctypes.c_ulonglong),
        ("Dr3", ctypes.c_ulonglong),
        ("Dr6", ctypes.c_ulonglong),
        ("Dr7", ctypes.c_ulonglong),
    ]

if __name__ == "__main__":
    ad = AntiDebug()
    
    checks = [
        ("IsDebuggerPresent", ad.check_debugger_present()),
        ("RemoteDebugger", ad.check_remote_debugger()),
        ("Timing", ad.timing_checks())
    ]
    
    for name, result in checks:
        print(f"[{'!' if result else '+'}] {name}: {result}")