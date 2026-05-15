#!/usr/bin/env python3
"""
Research Module Demonstrator
Runs safe, read-only checks from each research module to show they work.
No destructive actions — only detection/enumeration checks.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

def demo_separator(title):
    print(f"\n{'='*60}")
    print(f"  DEMO: {title}")
    print(f"{'='*60}\n")

def demo_anti_debug():
    """Demonstrate anti-debugging checks (read-only, safe)"""
    demo_separator("Anti-Debugging Checks (T1622)")
    from research_modules.anti_debug import AntiDebug
    ad = AntiDebug()
    
    checks = [
        ("IsDebuggerPresent", ad.check_debugger_present()),
        ("RemoteDebuggerPresent", ad.check_remote_debugger()),
        ("Timing Side-Channel", ad.timing_checks()),
    ]
    
    for name, result in checks:
        status = "DETECTED" if result else "CLEAN"
        icon = "!" if result else "+"
        print(f"  [{icon}] {name}: {status}")
    
    print(f"\n  >> Result: {'Debugger detected — would trigger evasion' if any(r for _,r in checks) else 'No debugger — normal execution proceeds'}")

def demo_uac_check():
    """Demonstrate UAC level check (read-only, safe)"""
    demo_separator("UAC Level Check (T1548.002)")
    from research_modules.uac_bypass import UACBypass
    bypass = UACBypass()
    
    uac_level = bypass.check_uac_level()
    levels = {
        0: "Always Notify (most secure)",
        2: "Default — notify on app changes",
        5: "Default — dimmed desktop",
        0x13: "Never Notify (least secure — bypassable)"
    }
    
    print(f"  UAC ConsentPromptBehaviorAdmin = {uac_level}")
    print(f"  Interpretation: {levels.get(uac_level, f'Custom value ({uac_level})')}")
    print(f"\n  >> Bypass feasibility: {'HIGH — UAC can be bypassed via Fodhelper/ComputerDefaults' if uac_level >= 2 else 'LOW — Always Notify blocks most bypasses'}")
    
    print(f"\n  Available bypass techniques:")
    print(f"    1. Fodhelper.exe registry hijack")
    print(f"    2. ComputerDefaults.exe registry hijack")
    print(f"    3. Slui.exe registry hijack")
    print(f"    4. EventViewer.exe registry hijack")
    print(f"    5. Sdclt.exe App Paths hijack")
    print(f"    6. CMSTPLUA COM elevation")

def demo_encryption():
    """Demonstrate encryption/obfuscation (safe — just encodes a test string)"""
    demo_separator("String Obfuscation (T1027)")
    from research_modules.encryption_obfuscation import Obfuscator
    obf = Obfuscator()
    
    test_strings = ["AmsiScanBuffer", "ntdll.dll", "VirtualAlloc"]
    
    for s in test_strings:
        result = obf.string_obfuscation(s)
        print(f"  Original : {s}")
        print(f"  Obfuscated: data={result['data'][:30]}...")
        print(f"              key ={result['key'][:30]}...")
        print(f"              mask={result['mask'][:30]}...")
        print()
    
    # AES demo
    print(f"  AES-256-CBC Encryption Demo:")
    plaintext = b"This is a secret payload that would be encrypted in transit"
    encrypted = obf.aes_encrypt(plaintext)
    print(f"    Plaintext : {plaintext[:40]}...")
    print(f"    Encrypted : {encrypted[:20].hex()}... ({len(encrypted)} bytes)")
    print(f"    IV        : {encrypted[:16].hex()}")

def demo_system_info():
    """Demonstrate the core data collection tool"""
    demo_separator("Core System Data Collection (T1082)")
    from sysinfo import SystemInfoGatherer
    gatherer = SystemInfoGatherer()
    
    # Only collect safe, non-invasive info
    basic = gatherer.get_basic_system_info()
    cpu = gatherer.get_cpu_info()
    mem = gatherer.get_memory_info()
    uptime = gatherer.get_system_uptime()
    
    sys_info = basic.get('system', {})
    print(f"  Hostname     : {sys_info.get('hostname', 'N/A')}")
    print(f"  Platform     : {sys_info.get('platform', 'N/A')} {sys_info.get('platform_release', '')}")
    print(f"  Architecture : {sys_info.get('architecture', 'N/A')}")
    print(f"  CPU          : {cpu.get('name', 'N/A')}")
    print(f"  Cores        : {cpu.get('physical_cores')} physical / {cpu.get('total_cores')} logical")
    print(f"  RAM          : {mem.get('total', 0) / (1024**3):.1f} GB ({mem.get('percentage')}% used)")
    print(f"  Uptime       : {uptime.get('uptime', 'N/A')}")
    print(f"  Local IP     : {sys_info.get('ip_address', 'N/A')}")

def demo_network():
    """Show network discovery"""
    demo_separator("Network Discovery (T1049)")
    import psutil, socket
    
    conns = [c for c in psutil.net_connections(kind='inet') if c.status == 'ESTABLISHED']
    print(f"  Active TCP connections: {len(conns)}")
    print(f"  {'Local':<25} {'Remote':<25} {'PID'}")
    print(f"  {'-'*25} {'-'*25} {'-'*6}")
    for c in conns[:10]:
        local = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "N/A"
        remote = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "N/A"
        print(f"  {local:<25} {remote:<25} {c.pid}")
    if len(conns) > 10:
        print(f"  ... and {len(conns)-10} more")

def main():
    print("=" * 60)
    print("  sys-SPYWARE — LIVE DEMONSTRATION")
    print("  Offensive Security Research Project")
    print("=" * 60)
    print(f"  Demonstrating ATT&CK techniques on LOCAL system")
    print(f"  All checks are READ-ONLY — no modifications made")
    
    demos = [
        ("1", "System Data Collection (T1082)", demo_system_info),
        ("2", "Network Discovery (T1049)", demo_network),
        ("3", "Anti-Debugging Checks (T1622)", demo_anti_debug),
        ("4", "UAC Level Assessment (T1548.002)", demo_uac_check),
        ("5", "Encryption & Obfuscation (T1027)", demo_encryption),
        ("A", "Run ALL demos", None),
        ("Q", "Quit", None),
    ]
    
    while True:
        print(f"\n{'-'*60}")
        print("  Select demonstration:")
        for key, name, _ in demos:
            print(f"    [{key}] {name}")
        
        choice = input("\n  Choice: ").strip().upper()
        
        if choice == 'Q':
            print("\n  Demo complete.")
            break
        elif choice == 'A':
            for key, name, func in demos:
                if func:
                    try:
                        func()
                    except Exception as e:
                        print(f"  [!] {name} error: {e}")
        else:
            for key, name, func in demos:
                if key == choice and func:
                    try:
                        func()
                    except Exception as e:
                        print(f"  [!] Error: {e}")
                    break
            else:
                print("  Invalid choice.")

if __name__ == "__main__":
    main()
