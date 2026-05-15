# Research Modules — Offensive Security Technique Analysis

> **⚠️ These modules are standalone research references. They are NOT integrated into the main tool.**

## Purpose

Each module in this directory demonstrates a specific MITRE ATT&CK technique commonly used by threat actors for defense evasion, privilege escalation, and persistence. They are documented here for academic analysis alongside their detection and mitigation strategies.

## Module Catalog

| Module | ATT&CK ID | Technique | Lines |
|--------|-----------|-----------|-------|
| `uac_bypass.py` | T1548.002 | UAC Bypass via Registry Hijack | 137 |
| `amsi_bypass.py` | T1562.001 | AMSI AmsiScanBuffer Patching | 68 |
| `etw_patching.py` | T1562.006 | ETW EtwEventWrite Patching | 62 |
| `anti_debug.py` | T1622 | Debugger Detection & Evasion | 168 |
| `shellcode_loaders.py` | T1055 | Memory Injection (5 methods) | 115 |
| `defender_tamper.py` | T1562.001 | Windows Defender Tampering | 136 |
| `kernel_rootkit.py` | T1014 | Kernel Driver Rootkit Operations | 136 |
| `encryption_obfuscation.py` | T1027 | Payload Encryption & Obfuscation | 143 |
| `reflective_dll_loader.py` | T1620 | Reflective PE Loading (fileless) | 109 |
| `privilege_escalation.py` | T1068 | Token/Pipe/Potato/Hijack PrivEsc | 186 |

## Full Analysis

See [`../docs/proposed_stealth_modules_report.md`](../docs/proposed_stealth_modules_report.md) for detailed technical analysis including:
- Implementation walkthroughs
- Real-world threat actor usage
- Detection methods for each technique
- Recommended mitigations
