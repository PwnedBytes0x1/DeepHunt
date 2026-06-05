# /threat-modeling — PASTA + STRIDE + Attack Tree Methodology

> **Skill type:** Reasoning / Planning  
> **Source:** 0x0pointer/skills `/threat-modeling`, superhackers `security-assessment`, STRIDE/DREAD  
> **Chains into:** All exploitation skills  
> **Chains from:** `/recon`, `/osint`

---

## Purpose

Before exploiting, model the threat landscape. Threat modeling converts "we found some stuff" into a structured, prioritized attack plan aligned with business risk.

---

## PASTA Framework (Process for Attack Simulation and Threat Analysis)

### Stage 1: Define Objectives
```
Business objectives: What does this system need to do?
Security objectives: What must never happen?
  - Data breach: PII/PCI/PHI exposure
  - Service disruption: SLA violations
  - Integrity failure: corrupted records, fraudulent transactions
  - Unauthorized access: account takeover, privilege abuse
```

### Stage 2: Define Technical Scope
```
Components in scope:
  □ Web application (frontend + API)
  □ Mobile apps (iOS/Android)
  □ Backend services (microservices, queues, workers)
  □ Databases (RDBMS, NoSQL, search)
  □ Infrastructure (cloud, containers, network)
  □ Third-party integrations (OAuth providers, payment processors)
  □ CI/CD pipeline
  □ Admin interfaces
```

### Stage 3: Decompose the Application
```
For each component, identify:
  - Data flows (draw DFD)
  - Trust boundaries (where does trust change?)
  - External entities (who talks to this system?)
  - Entry points (where can attackers inject input?)
  - Assets (what data/functionality is valuable?)
```

### Stage 4: Threat Analysis
```
For each trust boundary crossing, apply STRIDE:
  Spoofing     → Can attacker impersonate a user/service?
  Tampering    → Can attacker modify data in transit or at rest?
  Repudiation  → Can attacker deny performing an action?
  Info Disclosure → Can attacker read sensitive data they shouldn't?
  DoS          → Can attacker deny service to legitimate users?
  Elevation of Privilege → Can attacker gain more access than authorized?
```

### Stage 5: Vulnerability & Weakness Analysis
```
Map identified threats to:
  - OWASP Top 10 (web)
  - OWASP API Top 10 (APIs)
  - CWE Top 25 (code-level weaknesses)
  - Known CVEs for identified tech stack
```

### Stage 6: Attack Modeling
```
For each high-priority threat, build an attack tree:
  Root: Attack objective (e.g., "Steal all user PII")
  Branches: Alternative paths to achieve objective
  Leaves: Specific technical attacks

Prioritize by: likelihood × impact
```

### Stage 7: Risk and Countermeasures
```
For each attack:
  Current controls: What's already in place?
  Residual risk: What risk remains despite controls?
  Recommended mitigations: Specific, actionable fixes
  Mitigation priority: P1-P4 based on risk score
```

---

## STRIDE Threat Matrix Template

| Component | Spoofing | Tampering | Repudiation | Info Disclosure | DoS | Elevation |
|-----------|----------|-----------|-------------|-----------------|-----|-----------|
| Login API | JWT forgery | Password reset token manipulation | Auth log gaps | Credential in logs | Brute force | Admin endpoint bypass |
| File upload | Filename spoofing | Magic byte bypass | No audit log | Source code leakage via LFI | ZIP bomb | Web shell upload |
| Admin panel | Session hijacking | CSRF state change | Missing audit trail | Debug endpoint exposure | Slowloris | IDOR to admin |
| Payment API | Merchant impersonation | Amount tampering | Webhook forgery | CC data in logs | Replay attack | Price manipulation |

---

## Attack Tree Example: Account Takeover

```
[Goal: Take over a user account]
├── [Credential theft]
│   ├── Phishing (social engineering)
│   ├── Credential stuffing (from leaked DBs)
│   ├── Password brute force
│   │   └── Requires: no rate limiting, no lockout
│   └── Credential extraction
│       ├── SQLi → password hash dump → crack offline
│       └── XSS → steal session cookie
├── [Session hijacking]
│   ├── Session fixation
│   ├── CSRF → add attacker-controlled recovery email
│   └── XSS → exfiltrate session token
├── [Auth bypass]
│   ├── JWT algorithm confusion (RS256 → HS256)
│   ├── OAuth state parameter manipulation
│   └── Password reset token predictability
└── [Account recovery abuse]
    ├── Security question bypass
    └── SMS OTP interception (SIM swap)
```

---

## DREAD Risk Scoring

Score each threat 1-10 on five dimensions:

| Dimension | Question |
|-----------|---------|
| **D**amage | How bad is the damage if exploited? |
| **R**eproducibility | How easy is it to reproduce? |
| **E**xploitability | How easy is it to exploit? |
| **A**ffected users | How many users are impacted? |
| **D**iscoverability | How easy is it for an attacker to discover? |

```
DREAD score = (D + R + E + A + D) / 5
High risk: ≥ 7.0
Medium risk: 4.0–6.9
Low risk: < 4.0
```

---

## 4-Question Threat Model (Quick Assessment)

For time-constrained assessments:

1. **What are we building?** — Component map + data flows
2. **What can go wrong?** — STRIDE for each component
3. **What are we going to do about it?** — Mitigations per threat
4. **Did we do a good job?** — Threat model review + coverage check

---

## Output Artifacts

```
threat-model/
├── component-map.md          ← architecture overview
├── data-flow-diagram.png     ← DFD with trust boundaries
├── attack-tree.md            ← attack trees per objective
├── risk-register.csv         ← all threats with DREAD scores
└── mitigation-plan.md        ← prioritized remediation actions
```

---

## Integration with Pentest Planning

Use the threat model to prioritize your engagement:

```
High DREAD + Easy access  → Test first (P1)
High DREAD + Hard access  → Test second (P2)
Low DREAD + Easy access   → Test third (P3)
Low DREAD + Hard access   → Document, skip if time-constrained (P4)
```

Chain: threat model findings → `/web-exploit` → `/api-security` → `/business-logic` in threat-model priority order.
