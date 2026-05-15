# sys-SPYWARE — Offensive Security Research Project

> **Author:** Bhuvan Kumar HM 

A comprehensive Windows post-exploitation research framework developed in Python, demonstrating real-world attack techniques mapped to the MITRE ATT&CK framework. This project covers the full adversary kill-chain: system reconnaissance, data collection, credential harvesting, exfiltration, and advanced defense evasion techniques.

---

## Project Structure

```
mycom/
├── docs/                              # Academic reports & documentation
│   ├── project_report.md              # Full technical report (main project)
│   └── proposed_stealth_modules_report.md  # Advanced evasion analysis
│
├── research_modules/                  # Standalone offensive technique research
│   ├── __init__.py                    # Module index with ATT&CK mapping
│   ├── README.md                      # Research modules catalog
│   ├── uac_bypass.py                  # T1548.002 — UAC Bypass
│   ├── amsi_bypass.py                 # T1562.001 — AMSI Bypass
│   ├── etw_patching.py                # T1562.006 — ETW Patching
│   ├── anti_debug.py                  # T1622   — Anti-Debugging
│   ├── shellcode_loaders.py           # T1055   — Process Injection
│   ├── defender_tamper.py             # T1562.001 — Defender Tampering
│   ├── kernel_rootkit.py              # T1014   — Kernel Rootkit
│   ├── encryption_obfuscation.py      # T1027   — Obfuscation
│   ├── reflective_dll_loader.py       # T1620   — Reflective DLL Loading
│   └── privilege_escalation.py        # T1068   — Privilege Escalation
│
├── sysinfo.py                         # Core orchestrator (2000+ lines)
├── browser.py                         # Browser history extraction
├── clip_screen.py                     # Clipboard & screenshot capture
├── location.py                        # Geolocation tracking
├── key.py                             # Keystroke logger
├── files.py                           # File system analysis
├── net.py                             # Network monitoring
├── process.py                         # Process enumeration
├── usb_mon.py                         # USB device monitoring
├── build_exe.py                       # PyInstaller build script
└── dist/                              # Compiled executable output
```

---

## MITRE ATT&CK Coverage

### Core Modules (Implemented & Functional)

| ATT&CK ID  | Technique                        | Module           |
|-------------|----------------------------------|------------------|
| T1005       | Data from Local System           | `files.py`       |
| T1049       | System Network Connections       | `process.py`     |
| T1056.001   | Keylogging                       | `key.py`         |
| T1057       | Process Discovery                | `process.py`     |
| T1082       | System Information Discovery     | `sysinfo.py`     |
| T1083       | File and Directory Discovery     | `files.py`       |
| T1113       | Screen Capture                   | `clip_screen.py` |
| T1115       | Clipboard Data                   | `clip_screen.py` |
| T1120       | Peripheral Device Discovery      | `usb_mon.py`     |
| T1217       | Browser Information Discovery    | `browser.py`     |
| T1547.001   | Registry Run Keys (Persistence)  | `sysinfo.py`     |
| T1567.002   | Exfiltration to Cloud Storage    | `sysinfo.py`     |
| T1614       | System Location Discovery        | `location.py`    |

### Research Modules (Documented & Analyzed)

| ATT&CK ID  | Technique                        | Module                        |
|-------------|----------------------------------|-------------------------------|
| T1014       | Rootkit                          | `kernel_rootkit.py`           |
| T1027       | Obfuscated Files                 | `encryption_obfuscation.py`   |
| T1055       | Process Injection                | `shellcode_loaders.py`        |
| T1068       | Exploitation for Privilege Esc.  | `privilege_escalation.py`     |
| T1548.002   | Bypass UAC                       | `uac_bypass.py`               |
| T1562.001   | Disable Security Tools           | `amsi_bypass.py`, `defender_tamper.py` |
| T1562.006   | Indicator Blocking               | `etw_patching.py`             |
| T1620       | Reflective Code Loading          | `reflective_dll_loader.py`    |
| T1622       | Debugger Evasion                 | `anti_debug.py`               |

**Total ATT&CK Coverage: 22 unique techniques across 7 tactics**

---

## Reports & Documentation

| Document | Description |
|----------|-------------|
| [`docs/project_report.md`](docs/project_report.md) | Full technical report covering architecture, module analysis, data flow, ATT&CK mapping, detection strategies |
| [`docs/proposed_stealth_modules_report.md`](docs/proposed_stealth_modules_report.md) | Detailed analysis of 10 advanced evasion & escalation techniques with defensive countermeasures |
| [`research_modules/README.md`](research_modules/README.md) | Research module catalog with ATT&CK technique index |

---

## Usage

```powershell
# Run in auto mode (collect + report)
python sysinfo.py

# Interactive menu
python sysinfo.py --menu

# Build standalone executable
python build_exe.py
```

## Configuration

```powershell
# Email reporting
set GMAIL_APP_PASSWORD=your_app_password

# Google Drive upload (optional)
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\service_account.json
set GOOGLE_DRIVE_FOLDER_ID=your_folder_id
```

---

## Security & Legal Notice

> ⚠️ **This project is developed exclusively for educational and authorized security research.**
> All testing was performed on systems owned by the author.
> Unauthorized deployment is illegal under CFAA, Computer Misuse Act, IT Act, and equivalent legislation.

---

## Requirements

- Python 3.x
- Windows 10/11 (x64)
- Dependencies: `psutil`, `wmi`, `pywin32`, `pynput`, `Pillow`, `watchdog`, `requests`, `cryptography`
