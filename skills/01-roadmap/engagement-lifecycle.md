# /engagement-lifecycle — Full Engagement Planning & Orchestration

> **Skill type:** Orchestration  
> **Chains into:** All phase skills  
> **Chained from:** `/roadmap`

---

## Purpose

This skill teaches an AI agent how to plan, execute, and conclude a complete security engagement from kickoff to final report. It covers scope definition, rules of engagement, phase orchestration, and the evidence archival process.

---

## Pre-Engagement Checklist

Before starting ANY engagement, confirm:

```
□ Scope document signed — what's in scope, what's explicitly out
□ Rules of Engagement (ROE) defined:
  □ Testing hours (business hours only? 24x7?)
  □ Destructive testing allowed? (e.g., DoS testing)
  □ Social engineering authorized?
  □ Physical access in scope?
  □ Cloud infrastructure in scope?
□ Emergency contact established (who to call if something breaks)
□ Data handling rules understood (no exfil of real PII)
□ Legal authorization in writing
□ Starting IP/VPN credentials provided
```

---

## Engagement Types

### Black-Box External
- No credentials, no source code
- Start: external IP or domain
- Path: OSINT → port scan → fingerprint → exploit → post-exploit
- Skills chain: `/osint` → `/recon` → `/web-exploit` → `/api-security` → `/post-exploit`

### Grey-Box
- Low-privilege credentials provided
- Start: login endpoint + creds
- Path: authenticated scanning → privilege escalation
- Skills chain: `/web-exploit` → `/business-logic` → `/credential-audit` → `/post-exploit`

### White-Box (Source Code Review)
- Full source code + architecture docs
- Start: codebase + deployment info
- Path: ASVS review → sink tracing → PoC writing
- Skills chain: `/codebase` → `/analyze-cve` → `/remediate`

### API Assessment
- OpenAPI/Swagger spec (or spec hunting)
- Path: surface discovery → OWASP API Top 10
- Skills chain: `/api-security` → `/business-logic` → `/credential-audit`

### Cloud Assessment
- Cloud console access (read-only role recommended)
- Path: IAM enumeration → misconfiguration → escalation
- Skills chain: `/cloud-security` → `/container-k8s-security` → `/ad-assessment`

### AI/LLM Red Team
- Target: LLM application endpoint
- Path: probe → injection → bypass → extraction
- Skills chain: `/ai-redteam` → `/colang-gen`

---

## The 6-Phase Engagement Loop

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: PLANNING                                      │
│  • Scope review, ROE, threat modeling                   │
│  • Attack surface map                                    │
│  • Engagement directory init                            │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 2: RECONNAISSANCE                                │
│  • OSINT (passive, no target contact)                   │
│  • Active recon (port scan, fingerprint, DNS)           │
│  • API surface discovery                                │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 3: VULNERABILITY DISCOVERY                       │
│  • DAST scanning, SAST if source available              │
│  • CVE matching for discovered services                  │
│  • Manual probing for business logic flaws              │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 4: EXPLOITATION  [HIR pause for RCE/SQLi exfil] │
│  • Exploit validated findings (P1 first)                │
│  • Chain vulnerabilities into attack paths              │
│  • Capture evidence: screenshot, HTTP dump, output      │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 5: POST-EXPLOITATION  [HIR pause for pivoting]   │
│  • Privilege escalation                                 │
│  • Lateral movement                                     │
│  • Internal recon, data exfil (in scope only)           │
└─────────────────┬───────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────────┐
│  Phase 6: REPORTING & CLEANUP                           │
│  • Write findings.json + PoCs in pocs/                  │
│  • Generate HTML/PDF report                             │
│  • Remove persistence artifacts (shells, users, etc.)   │
│  • Archive evidence                                     │
└─────────────────────────────────────────────────────────┘
```

---

## Engagement Directory Structure

```
engagement-<target>-<date>/
├── scope.md                    ← authorization & scope
├── findings.json               ← machine-readable findings
├── report.html                 ← human-readable report
├── pocs/                       ← Burp .http files + exploit scripts
│   ├── finding-001-sqli.http
│   └── finding-002-ssrf.py
├── evidence/                   ← screenshots, scan outputs
│   ├── nmap-full.txt
│   ├── nuclei-output.jsonl
│   └── screenshots/
├── recon/                      ← raw recon data
│   ├── subdomains.txt
│   ├── ports.txt
│   └── tech-fingerprint.json
└── tools/                      ← wordlists, custom scripts
```

---

## Scope Enforcement Rules (Non-Negotiable)

```python
# Every tool call MUST validate target
def validate_target(target_ip: str, allowed_scope: list[str]) -> bool:
    """Reject any target not in authorized scope."""
    for cidr in allowed_scope:
        if ip_in_cidr(target_ip, cidr):
            return True
    raise ScopeViolation(f"Target {target_ip} is out of scope. Aborting.")

# Before ANY exploit action:
# 1. Check target is in scope
# 2. Check action type — if RCE/DB-dump/domain takeover → HIR pause
# 3. Log action with timestamp, target, tool, output
# 4. Capture evidence artifact
```

---

## QA Depth Enforcement

The agent must NOT rubber-stamp findings. Checks to enforce:

| Check | What it catches |
|-------|----------------|
| No bulk N/A marking | >10 cells marked N/A with no tool evidence → blocked |
| Coverage integrity | Marked tested but no artifact on disk → blocked |
| Premature completion | Thorough scan without 3 semgrep passes → blocked |
| Follow-up on criticals | Critical finding > 20 min old with no follow-up → directive injected |
| Skill chain enforcement | SQLi-eligible endpoint with no `/web-exploit` invoked → blocked |

---

## Human Intervention Required (HIR) Gates

Pause and confirm with operator before:
- Attempting RCE (remote code execution)
- Database extraction (dumps beyond schema)
- Domain controller compromise
- Exfiltrating any file that might contain real PII
- Destructive actions (deleting files, modifying databases)
- Pivoting to a new network segment not in initial scope
- Social engineering a real employee

---

## Finishing an Engagement

```
□ All HIR-gated actions resolved or documented
□ findings.json complete with CVSS scores
□ PoC for every confirmed finding
□ Coverage matrix showing what was tested
□ Cleanup: remove web shells, backdoor accounts, artifacts
□ Evidence archived (immutable, timestamped)
□ Report generated with executive summary
□ CVE requests drafted for qualifying findings
□ Debrief notes written for future engagements
```
