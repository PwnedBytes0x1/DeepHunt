# /tool-registry — Complete Security Tool Reference

> **Skill type:** Reference  
> **Source:** Krishcalin/Autonomous-Pen-Testing (60+ tools), superhackers TOOLCHAIN.md, skyvanguard/awesome-ai-pentesting  

---

## Complete Tool Registry by Category

| Category | Tools | Install |
|----------|-------|---------|
| **Reconnaissance** | nmap, masscan, rustscan, subfinder, amass, httpx, whatweb, wafw00f, dnsrecon, whois | apt/go |
| **OSINT** | theHarvester, sherlock, holehe, maigret, spiderfoot, recon-ng | pip/apt |
| **Content Discovery** | ffuf, gobuster, feroxbuster, dirsearch, katana, hakrawler | go/pip |
| **Web Scanning** | nikto, nuclei, wapiti, zaproxy, skipfish | apt/go |
| **SQLi** | sqlmap, ghauri | pip |
| **XSS** | dalfox, XSSStrike | go/pip |
| **SSRF/XXE** | SSRFmap, xxeinjector | pip |
| **Command Injection** | commix | pip |
| **Parameter Discovery** | arjun, paramspider, x8 | pip |
| **Web Crawling** | katana, waybackurls, gau, photon | go/pip |
| **Exploitation** | metasploit, searchsploit, exploitdb | apt |
| **Credential Attacks** | hydra, medusa, crackmapexec, netexec | apt |
| **Password Cracking** | hashcat, john | apt |
| **Post-Exploitation Linux** | linpeas, pspy, linux-exploit-suggester | git |
| **Post-Exploitation Windows** | winpeas, seatbelt, bloodhound | git |
| **AD** | BloodHound, Certipy, impacket (all tools), responder, kerbrute | pip/apt |
| **Pivoting** | chisel, ligolo-ng, socat, netcat | go/apt |
| **C2** | sliver, metasploit, covenant | go/dotnet |
| **Mobile** | frida, objection, apktool, jadx, adb | pip/apt |
| **Wireless** | aircrack-ng, hcxdumptool, hcxpcapngtool, kismet | apt |
| **Cloud** | awscli, gcloud, az, scout-suite, prowler, pacu | pip/apt |
| **Container** | kube-hunter, trivy, peirates, CDK, kubeletctl | go/pip |
| **Secrets** | trufflehog, gitleaks, semgrep, bandit | pip/go |
| **Proxy** | burpsuite, mitmproxy, caido | manual/pip |
| **Traffic Analysis** | tcpdump, wireshark, tshark | apt |
| **AI Security** | garak, PyRIT, promptfoo, FuzzyAI | pip/npm |
| **Forensics** | volatility3, autopsy, binwalk | pip/apt |
| **Reverse Engineering** | ghidra, radare2, cutter, binwalk, strings | apt/manual |
| **Binary Exploitation** | pwntools, peda, pwndbg, gef | pip/apt |
| **Evasion** | donut, pe2shellcode, shellter | go/wine |
| **Reporting** | dradis, serpico, faraday | ruby/pip |
| **Utilities** | jq, curl, wget, socat, proxychains, tmux | apt |

---

## Quick Install Script

```bash
#!/bin/bash
# install-pentest-tools.sh

# Core tools
apt-get update && apt-get install -y \
  nmap masscan hydra john hashcat nikto sqlmap \
  netcat-traditional socat tcpdump wireshark-common \
  git curl wget jq python3 python3-pip golang

# Go tools
go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install github.com/projectdiscovery/httpx/cmd/httpx@latest
go install github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install github.com/ffuf/ffuf/v2@latest
go install github.com/OJ/gobuster/v3@latest
go install github.com/jpillora/chisel@latest
go install github.com/nicocha30/ligolo-ng/cmd/agent@latest
go install github.com/nicocha30/ligolo-ng/cmd/proxy@latest
go install github.com/hahwul/dalfox/v2@latest
go install github.com/projectdiscovery/katana/cmd/katana@latest
go install github.com/tomnomnom/waybackurls@latest

# Python tools
pip3 install impacket certipy-ad bloodhound crackmapexec \
  garak pyrit trufflehog semgrep bandit frida-tools objection

# Nuclei templates
nuclei -update-templates

echo "Core tools installed!"
```

---

## Tool Selection Decision Tree

```
Task: Port scan a single IP
→ nmap -sV -sC -p- TARGET

Task: Fast port scan large network
→ masscan -p1-65535 NETWORK --rate=10000

Task: Web directory discovery
→ ffuf (fastest) or feroxbuster (recursive)

Task: SQL injection testing
→ sqlmap (automated) or manual testing via Burp

Task: XSS testing
→ dalfox (automated) or manual via Burp

Task: SSRF testing
→ Manual via Burp + interactsh callback

Task: Subdomain enumeration
→ subfinder + amass (combine results)

Task: Credential brute force (web)
→ hydra or ffuf

Task: Password cracking (NTLM)
→ hashcat -m 1000

Task: AD enumeration
→ BloodHound (comprehensive) + ldapsearch (targeted)

Task: Kerberoasting
→ GetUserSPNs.py (impacket) + hashcat -m 13100

Task: Cloud security (AWS)
→ pacu or manual aws cli enumeration

Task: Container security
→ kube-hunter + trivy

Task: AI/LLM testing
→ garak (automated) + manual prompts
```
