# Demonstration Guide — sys-SPYWARE Research Project

## How to Present This Project

This guide walks through demonstrating the project for your university panel and OSCP+ submission.

---

## Demo Flow (Recommended 15–20 minutes)

### Part 1: Project Overview (3 min)

**Show:** `README.md` on screen

**Talk through:**
- "This is a modular offensive security research framework that demonstrates post-exploitation techniques"
- "It covers 22 MITRE ATT&CK techniques across 7 tactics"
- "The project has two components: a working data collection tool and a set of analyzed evasion techniques"
- Point to the project structure diagram showing core modules + research modules

---

### Part 2: Core Tool Demo (5 min)

**Run the tool in interactive mode:**

```powershell
cd t:\mycom
python sysinfo.py --menu
```

**Demonstrate these features live:**

1. **System Info Collection** — Show the tool gathering CPU, memory, disk, GPU, motherboard data
2. **Browser History** — Show it extracting Chrome/Edge history from SQLite
3. **Network Discovery** — Show active connections, WiFi profiles, public IP lookup
4. **Process Enumeration** — Show running processes with CPU/memory usage
5. **File Discovery** — Show file scanning across user directories
6. **Report Generation** — Show the HTML email report output

**Key talking points:**
- "Each module maps to a specific ATT&CK technique — for example, browser history extraction is T1217"
- "The tool generates both human-readable HTML reports and machine-readable JSON"
- "Data can be exfiltrated via Gmail SMTP or Google Drive API"

---

### Part 3: Research Modules Walkthrough (5 min)

**Open and walk through 3-4 key research modules:**

#### 3a. UAC Bypass (`research_modules/uac_bypass.py`)
```
"This demonstrates T1548.002 — 6 different UAC bypass techniques.
The Fodhelper method works by hijacking a registry key that auto-elevating
Windows binaries read. When fodhelper.exe launches, it executes our payload
at high integrity instead of the intended settings page."
```

#### 3b. AMSI Bypass (`research_modules/amsi_bypass.py`)
```
"This patches the AmsiScanBuffer function in memory to always return CLEAN.
It changes memory protection, overwrites the function prologue with
'mov eax, 0; ret', then restores protection. This blinds Windows'
content scanning for the entire process lifetime."
```

#### 3c. Anti-Debugging (`research_modules/anti_debug.py`)
```
"This implements 7 different debugger detection checks — from the basic
IsDebuggerPresent API to timing side-channels using QueryPerformanceCounter.
When debugging is detected, the tool can exit silently, show a fake error,
or execute benign decoy code."
```

#### 3d. ETW Patching (`research_modules/etw_patching.py`)
```
"ETW is how Windows Defender ATP and EDR tools receive telemetry.
By patching EtwEventWrite in ntdll.dll with 'xor rax, rax; ret',
all ETW events return SUCCESS without actually being logged.
This blinds security tools to everything happening in the process."
```

---

### Part 4: Detection & Mitigation Analysis (4 min)

**Show:** `docs/proposed_stealth_modules_report.md` — Section 6 (Defensive Recommendations)

**Walk through the detection table:**

```
"For each offensive technique, I've documented corresponding defensive measures:
- UAC Bypass → Sysmon registry monitoring + UAC Always Notify
- AMSI Bypass → AMSI provider integrity checks + Constrained Language Mode
- ETW Patching → Kernel-mode ETW consumers that can't be patched from user-mode
- Shellcode Injection → RWX memory detection + Control Flow Guard
- Rootkits → HVCI + Secure Boot + Microsoft's Driver Blocklist"
```

**Key talking point:**
```
"The dual offensive/defensive analysis is what makes this a research project
rather than just a tool. Understanding both sides is essential for
effective penetration testing and security assessment."
```

---

### Part 5: ATT&CK Mapping (2 min)

**Show:** The ATT&CK coverage table from `README.md`

```
"The complete project maps to 22 unique ATT&CK techniques:
- 13 implemented in the core tool (reconnaissance, collection, exfiltration)
- 9 additional techniques analyzed in the research modules (evasion, escalation)
- Coverage spans Reconnaissance, Collection, Credential Access, Exfiltration,
  Defense Evasion, Privilege Escalation, and Persistence tactics"
```

---

## Q&A Preparation

**Expected questions and answers:**

| Question | Answer |
|----------|--------|
| "How does the keylogger avoid detection?" | "The current implementation uses pynput which is detectable by AV. The research modules document how real threats use ETW patching and AMSI bypass to evade detection — and how defenders can counter with kernel-mode ETW and Constrained Language Mode." |
| "Did you test this on real targets?" | "All testing was on my own systems. The tool uses my own Gmail and Drive credentials. No unauthorized access was performed." |
| "How would you detect your own tool?" | "Sysmon rules for registry persistence, network monitoring for SMTP from non-email processes, file access auditing on browser databases, and behavioral analysis of the keylogger's write patterns." |
| "What would make this harder to detect?" | "The research modules document exactly that — ETW patching, AMSI bypass, and encryption would significantly increase evasion. The report also documents how defenders counter each technique." |
| "Why Python instead of C/C++?" | "Python allowed rapid prototyping of 10+ modules with ctypes for Win32 API access. A production red team tool would use C/C++ for smaller binary size and harder reverse engineering." |

---

## Files to Have Open During Demo

1. `README.md` — Project overview
2. `sysinfo.py` — Core orchestrator (show the `get_all_system_info()` method)
3. `research_modules/uac_bypass.py` — Walk through Fodhelper technique
4. `research_modules/anti_debug.py` — Show detection checks
5. `docs/proposed_stealth_modules_report.md` — Detection/mitigation table
