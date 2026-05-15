"""
Research Modules — Advanced Offensive Security Techniques
=========================================================

This package contains standalone research implementations of advanced
offensive security techniques studied as part of the project's theoretical
analysis. Each module demonstrates a specific ATT&CK technique.

These modules are PROVIDED AS STANDALONE REFERENCES and are NOT integrated
into the main data collection pipeline. They exist for academic documentation
and analysis purposes.

Module Index:
    - uac_bypass.py              T1548.002 — UAC Bypass (6 techniques)
    - amsi_bypass.py             T1562.001 — AMSI Memory Patching
    - etw_patching.py            T1562.006 — ETW Telemetry Blocking
    - anti_debug.py              T1622    — Debugger Evasion (7 checks)
    - shellcode_loaders.py       T1055    — Process Injection (5 loaders)
    - defender_tamper.py         T1562.001 — Security Tool Tampering
    - kernel_rootkit.py          T1014    — Kernel Driver Rootkit
    - encryption_obfuscation.py  T1027    — Code Obfuscation
    - reflective_dll_loader.py   T1620    — Reflective Code Loading
    - privilege_escalation.py    T1068    — Privilege Escalation (7 methods)

See docs/proposed_stealth_modules_report.md for full analysis.
"""
