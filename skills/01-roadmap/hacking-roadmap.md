# /roadmap — Hacker AI Agent Learning Roadmap

> **Skill type:** Meta / Orientation  
> **Chains into:** All other skills  
> **Chained from:** Nothing (starting point)

---

## Purpose

This skill orients an AI agent across the full offensive security lifecycle — from zero knowledge to domain expertise. Use it to plan a learning or engagement path, decide which skill to invoke next, and understand how capabilities compose.

---

## Phase 0 — Foundations (Know Before You Hack)

### Mental Model: What Is a Pentest?
A penetration test is a **structured simulation of an adversary**. The goal is to find and demonstrate impact — not just flag issues. Every finding needs:
1. **Evidence** — proof it exists (screenshot, request/response, scan output)
2. **Impact** — what a real attacker could do with it
3. **Reproduction** — steps another tester can follow
4. **Remediation** — how to fix it

### The Kill Chain (MITRE ATT&CK aligned)
```
Recon → Weaponize → Deliver → Exploit → Install → C2 → Actions on Objective
```

Mapped to pentester workflow:
```
OSINT/Recon → Vuln Finding → Exploitation → Post-Exploit → Lateral Movement → Exfiltration → Report
```

### Core Frameworks to Internalize
| Framework | What It Teaches |
|-----------|----------------|
| OWASP Top 10 (2025) | Web app vulnerability priority |
| OWASP API Top 10 (2023) | API-specific attack surface |
| OWASP LLM Top 10 (2025) | AI system attacks |
| OWASP ASVS 5.0 | 427-requirement security standard |
| MITRE ATT&CK | Adversary tactics, techniques, procedures |
| MITRE ATLAS | AI/ML adversarial tactics |
| PTES | Pentest Execution Standard |
| CVSS v3.1 | Vulnerability scoring |
| CWE Top 25 | Root-cause weakness classification |

---

## Phase 1 — Reconnaissance & Surface Mapping

**Goal:** Know more about the target than the target knows about itself.

### Passive Recon (No direct target contact)
- Certificate transparency logs (crt.sh)
- Shodan / Censys / FOFA for exposed services
- GitHub / GitLab secret hunting (trufflehog, gitleaks)
- Wayback Machine for historical endpoints
- LinkedIn / social media for employee info → phishing targets
- DNS records: A, MX, TXT, SPF, DKIM, DMARC

### Active Recon (Direct target contact)
- Port scanning: nmap, masscan, rustscan
- Service fingerprinting: whatweb, wappalyzer, httpx
- Directory/content discovery: ffuf, gobuster, feroxbuster
- Subdomain brute force: subfinder, amass
- WAF detection: wafw00f

### Skills to invoke:
→ `/osint` — passive intelligence  
→ `/recon` — active enumeration  
→ `/threat-modeling` — map the attack surface  

---

## Phase 2 — Vulnerability Finding

**Goal:** Find exploitable conditions, not just scanner noise.

### Scanning approaches
- **DAST** (Dynamic): nuclei, nikto, OWASP ZAP, Burp Scanner
- **SAST** (Static): semgrep, bandit, CodeQL, snyk
- **SCA** (Dependency): trivy, grype, snyk
- **Secret scanning**: trufflehog (700+ detectors), gitleaks

### CVE research workflow
1. Identify service + version from recon
2. Search CVE databases: NIST NVD, CVEmap, Vulhub
3. Find public exploits: ExploitDB, GitHub, Packet Storm
4. Score by exploitability: CVSS v3.1 + contextual modifiers
5. Prioritize: P1 (CVSS≥9 + public exploit) → P4 (CVSS<4)

### Finding validation (6-stage pipeline)
`inventory → analysis → sanity_check → ruling → feasibility → validated`

### Skills to invoke:
→ `/analyze-cve` — CVE to PoC pipeline  
→ `/codebase` — ASVS 5.0 white-box review  
→ `/aikido-triage` — SAST/SCA triage  

---

## Phase 3 — Exploitation

**Goal:** Demonstrate real-world impact through controlled, scoped exploitation.

### Decision tree: What to exploit first?
```
RCE/SQLi-with-exfil → Auth bypass → SSRF-to-internal → Stored XSS → IDOR/BOLA → Info disclosure
```

### Priority modifiers
| Factor | Priority boost |
|--------|---------------|
| Public exploit available | +3 |
| No authentication required | +2 |
| Network accessible | +2 |
| Default credentials | +2 |
| User interaction not required | +1 |

### Skills to invoke:
→ `/web-exploit` — OWASP Top 10 attacks  
→ `/api-security` — API Top 10  
→ `/param-fuzz` — parameter fuzzing  
→ `/business-logic` — logic flaws  
→ `/credential-audit` — credential attacks  

---

## Phase 4 — Post-Exploitation

**Goal:** Show what an attacker could do after gaining a foothold.

### Ordered objectives (stop when scope is met)
1. **Establish persistence** — scheduled tasks, cron, registry keys, web shells
2. **Escalate privileges** — SUID/SUDO, token abuse, kernel exploits
3. **Internal recon** — network discovery, credential files, config dump
4. **Lateral movement** — PTH, PTT, Kerberoasting, NTLM relay
5. **Data exfiltration** — sensitive files, database dump, secrets

### Skills to invoke:
→ `/post-exploit` — privesc + persistence  
→ `/lateral-movement` — pivot techniques  
→ `/ad-assessment` — domain dominance  
→ `/pivot-tunnel` — SOCKS5/Chisel tunneling  

---

## Phase 5 — Reporting

**Goal:** Communicate findings to both executives and engineers.

### Report structure
1. Executive Summary — business risk in plain language
2. Scope & Methodology  
3. Findings — ranked by severity, with evidence, impact, CVSS score
4. Attack chains — how findings combine into full compromise paths
5. Remediation — code/config patches per finding
6. Compliance mapping — OWASP, CWE, CVE references

### Skills to invoke:
→ `/remediate` — generate code patches  
→ `/gh-export` — GitHub issue format  
→ `/request-cves` — CVE submission packages  

---

## Skill Chaining Guide

| If you found... | Chain into... |
|-----------------|---------------|
| SSRF to internal network | `/network-assess` → `/cloud-security` |
| SQLi → DB access | `/post-exploit` (data exfil) |
| LFI/RFI → File system access | `/post-exploit` (privesc via config read) |
| Auth bypass | `/business-logic` |
| Open S3/GCS bucket | `/cloud-security` |
| LLM endpoint found | `/ai-redteam` |
| Windows/AD environment | `/ad-assessment` → `/lateral-movement` |
| Container/K8s metadata | `/container-k8s-security` |
| Source code available | `/codebase` (ASVS review) |
| Multiple low findings | `/exploit-chain` (combine into kill chain) |
