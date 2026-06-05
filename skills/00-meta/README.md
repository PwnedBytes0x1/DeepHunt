# 🔐 Hacking Skills for AI Agents — Master Index

> **⚠️ AUTHORIZED USE ONLY.** Every skill in this folder is for systems you own or have explicit written permission to test. Unauthorized access is illegal.

## What This Is

A comprehensive, upgraded library of offensive-security **thinking skills** for AI agents. Each skill teaches the LLM *methodology* — not just commands, but how to reason about vulnerabilities, chain findings, validate impact, and adapt to what it discovers.

**v2.0 — OWASP Top 10 2021 Edition**
- Added complete 20-owasp-top10/ module (10 files, 400-800 lines each)
- Added 19-token-optimization/ module (6 files on AI agent efficiency)
- Removed 14-mobile-wireless/ (out of scope for web/cloud-focused engagements)
- Upgraded all existing modules with deeper exploitation detail
- Field manual style throughout: concise, practical, no fluff

---

## Changelog

### v2.0 (2026-05-30)
- **Removed:** `14-mobile-wireless/` — all mobile/Android/iOS content removed (out of scope for web/cloud-focused engagements)
- **Added:** `19-token-optimization/` — 6 new files for AI agent token efficiency (prompt compression, context management, efficient recon, tool batching, output formatting, budget management)
- **Added:** `20-owasp-top10/` — 10 new files, one per OWASP Top 10 2021 category (A01–A10), each with detection, exploitation payloads, bypass techniques, tools, real CVEs
- **Total modules:** 19 active modules (was 18, minus mobile, plus 2 new)

---

## Folder Structure

| Folder | Domain | Files |
|--------|--------|-------|
| `01-roadmap/` | Learning path & engagement lifecycle | 2 |
| `02-reasoning-thinking/` | P-E-R cognition, causal graphs, ReAct, red vs blue | 5 |
| `03-recon-osint/` | Passive/active recon, OSINT, surface mapping, dark web | 4 |
| `04-vulnerability-finding/` | CVE analysis, SAST/SCA, supply chain, credential audit | 4 |
| `05-web-exploitation/` | OWASP Top 10, SQLi, XSS, SSRF, SSTI, SSL/TLS | 3 |
| `06-api-security/` | OWASP API Top 10, GraphQL, gRPC, JWT/OAuth | 2 |
| `07-network-exploitation/` | Network assessment, pivoting, tunneling | 2 |
| `08-post-exploitation/` | Privesc (basic + deep), persistence, credential harvesting | 2 |
| `09-lateral-movement/` | AD lateral movement, credential reuse & harvest chains | 2 |
| `10-cloud-container/` | AWS/Azure/GCP, K8s, container escape, IAM privesc | 2 |
| `11-active-directory/` | ADCS ESC1-8, Kerberos delegation, BloodHound, DCSync | 2 |
| `12-ai-redteam/` | LLM Top 10, RAG/MCP attacks, NeMo Guardrails generation | 3 |
| `13-exploit-dev-binary/` | Binary exploitation, payload crafting, malware RE | 2 |
| `15-red-team-ops/` | C2, advanced EDR evasion, phishing, opsec | 3 |
| `16-reporting-remediation/` | Report generation, CVSS/EPSS scoring | 2 |
| `17-frameworks-tools/` | Tool registry (60+), Metasploit mastery | 2 |
| `18-ctf-methodology/` | CTF strategy, AI agent CTF workflow | 2 |
| `19-token-optimization/` | **NEW** AI agent token efficiency & context management | 6 |
| `20-owasp-top10/` | **NEW** OWASP Top 10 2021 — full field manuals | 10 |

**Total: 62 skill files**

---

## OWASP Top 10 Module (20-owasp-top10/)

| File | Vulnerability | Key Subtypes |
|------|--------------|--------------|
| A01-broken-access-control.md | Broken Access Control | IDOR, privesc, path traversal, CORS, force browse |
| A02-cryptographic-failures.md | Cryptographic Failures | Weak algos, hardcoded secrets, insecure transmission |
| A03-injection.md | Injection | SQLi, NoSQLi, SSTI, XXE, OS command, LDAP |
| A04-insecure-design.md | Insecure Design | Race conditions, business logic, rate limiting |
| A05-security-misconfiguration.md | Security Misconfiguration | Default creds, S3, debug endpoints, headers |
| A06-vulnerable-components.md | Vulnerable Components | CVE exploitation, Log4Shell, supply chain |
| A07-authentication-failures.md | Auth Failures | Brute force, JWT attacks, MFA bypass, session |
| A08-software-integrity-failures.md | Integrity Failures | Deserialization, CI/CD attacks, supply chain |
| A09-logging-failures.md | Logging Failures | Log injection, detection evasion, covering tracks |
| A10-ssrf.md | SSRF | Blind SSRF, cloud metadata, gopher, bypasses |

Each file includes: Overview, Detection, Indicators, Testing Steps, Exploitation, Verification, Common Problems, Tools, Bypasses, Remediation, Real CVEs.

---

## Token Optimization Module (19-token-optimization/)

| File | Topic |
|------|-------|
| agent-token-budget.md | Budget allocation, context window management |
| prompt-compression.md | Linguistic, structural, ML-based compression |
| efficient-recon.md | Minimal-call recon, filtering before LLM |
| output-format-optimization.md | Dense formats, JSON schema, structured output |
| tool-use-patterns.md | Batching, caching, progressive disclosure |
| context-management.md | Sliding windows, summarization, scratchpad |

---

## How Skills Work

Skills are **prompts that teach methodology**, not scripts. The LLM reads a skill, internalizes the attack pattern, and generates contextual paths through the target.

### The Universal Engagement Loop

```
/osint → /recon → /web-exploit → /api-security → /post-exploit → /report
                        ↓
                 /owasp-top10 → /lateral-movement → /cloud-security
```

### Reasoning Pattern (P-E-R)

1. **Plan** — build a causal DAG of what to test and in what order
2. **Execute** — run tools, capture evidence, log findings
3. **Reflect** — validate findings, eliminate false positives, update plan

---

## Safety Contract

- HIR (Human Intervention Required) pauses before RCE/DB-dump/domain takeover
- Every exploit action logged with evidence
- Scope enforcement: reject any target not in engagement authorization
- Stealth mode: respect rate limits, avoid triggering IDS on production
- False positive elimination: validate before reporting
