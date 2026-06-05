# /thinking-validation — Hypothesis Validation & Anti-Hallucination Protocols

> **Skill type:** Reasoning Quality  
> **Source:** LuaN1aoAgent causal graph, Autonomous-Pen-Testing v2.4.0 validation pipeline, RedTeamLLM  
> **Applies to:** All skills — call before reporting any finding

---

## Purpose

This skill prevents the #1 failure mode of AI security agents: **reporting findings that don't exist**. It implements the 6-stage validation pipeline and evidence-based reasoning protocols.

---

## The 6-Stage Validation Pipeline

Every raw scanner output passes through all 6 stages before becoming a confirmed finding:

```
STAGE 1: INVENTORY
  Input: Raw scanner/tool output
  Action: Extract unique findings by (host, port, vuln_type)
  Output: Deduplicated finding list
  Rejection: Exact duplicates → discard

STAGE 2: ANALYSIS
  Input: Each unique finding
  Action: Cross-reference with CVE databases, CWE taxonomy
  Action: Check if service version actually matches CVE
  Output: Annotated finding with CVE ID, CVSS score, version match confidence
  Rejection: Version mismatch without manual verification → flag as UNCONFIRMED

STAGE 3: SANITY CHECK
  Input: Annotated finding
  Action: Ask: "Does this make technical sense in context?"
  Action: Example — SQLi on an API that only takes JSON with no SQL backend → suspicious
  Action: Example — RCE finding from a fuzzer with no actual shell output → unconfirmed
  Output: PLAUSIBLE / IMPLAUSIBLE
  Rejection: IMPLAUSIBLE → investigate before proceeding

STAGE 4: RULING
  Input: PLAUSIBLE finding
  Action: Determine exploitability: EXPLOITABLE / UNEXPLOITABLE / NEEDS_MORE_DATA
  Action: Requires at least one active probe result (not just scanner assertion)
  Output: Exploitation ruling with evidence reference
  Rejection: NEEDS_MORE_DATA → run targeted probe, then retry

STAGE 5: FEASIBILITY
  Input: EXPLOITABLE finding
  Action: Assess real-world impact in THIS environment:
    - Is it network-accessible or only local?
    - Does auth bypass exist or is auth required?
    - Are there compensating controls (WAF, firewall)?
  Output: FEASIBLE / MITIGATED
  Rejection: MITIGATED → document control but lower severity

STAGE 6: VALIDATED
  Input: FEASIBLE finding
  Action: Generate/capture evidence artifact
  Action: Write finding to findings.json with all fields
  Action: Attach PoC (Burp .http file or exploit script)
  Output: VALIDATED finding ready for report
```

---

## Evidence Requirements by Severity

| Severity | Minimum Evidence | Required PoC |
|----------|-----------------|--------------|
| Critical (9.0-10.0) | Tool output + manual HTTP dump | Working Burp .http PoC |
| High (7.0-8.9) | Tool output + at least 1 manual probe | Request/response pair |
| Medium (4.0-6.9) | Tool output | Scanner evidence |
| Low (0.1-3.9) | Scanner output | Optional |
| Informational | Observation | None required |

---

## Anti-Hallucination Rules

**Rule 1: No evidence, no finding.**
If the only basis for a finding is "the LLM thinks it might be vulnerable," it doesn't go in the report. Period.

**Rule 2: Version match required for CVEs.**
A finding of CVE-2024-XXXX requires:
- Confirmed service version from active scan (not just banner)
- Version falls within CVE's affected range
- OR: active exploitation proof (service responded to PoC)

**Rule 3: Tool output must be stored.**
Before logging a finding, the raw tool output that supports it must be saved to `evidence/`. Finding without an artifact = unconfirmed.

**Rule 4: Re-test after WAF/filter detection.**
If a WAF was detected, a blocked probe does NOT mean "not vulnerable." Re-test with bypass techniques. A successful bypass is required for confirmation.

**Rule 5: Multi-tool confirmation boosts confidence.**
```
1 tool reports it    → confidence: 50%
2 tools agree        → confidence: 80%
3+ tools agree       → confidence: 95%
Manual PoC works     → confidence: 100% (CONFIRMED)
```

---

## Confidence Scoring Model

```python
def score_finding(finding: Finding) -> float:
    base = 0.5  # scanner assertion
    
    # Version evidence
    if finding.version_match == "exact":
        base += 0.2
    elif finding.version_match == "range":
        base += 0.1
    
    # Active confirmation
    if finding.active_probe_result == "positive":
        base += 0.2
    
    # Multi-tool agreement
    base += min(0.1 * (finding.tool_count - 1), 0.2)
    
    # Compensating controls
    if finding.waf_detected and not finding.waf_bypassed:
        base -= 0.3
    
    # Manual PoC
    if finding.poc_executed and finding.poc_succeeded:
        base = 1.0  # Definitive
    
    return min(base, 1.0)
```

---

## False Positive Indicators

Watch for these signals that a finding might be a false positive:

| Signal | What to do |
|--------|-----------|
| SQLi on endpoint that returns 500 on all inputs | Test with valid input first |
| XSS payload in response but no JS execution | Check Content-Type, CSP headers |
| Directory listing "found" but returns 401/403 | Verify with authenticated request |
| RCE "confirmed" but no command output | Verify out-of-band (DNS callback, time delay) |
| SQLi timing attack but server is slow | Baseline server response time first |
| Nuclei template fired but manual test fails | Check template logic, re-test manually |

---

## The QA Depth Checks

Before completing a scan, verify:

```
□ No endpoint marked "N/A" without a tool that verified it
□ All CRITICAL/HIGH findings have evidence artifacts on disk
□ No scan completed in suspiciously short time (>20 cells in <10 min)
□ Core skill chain executed: recon → web-exploit → param-fuzz → business-logic
□ Every SQLi-eligible endpoint tested
□ Every auth flow tested for bypass
□ Financial/quota endpoints tested for business logic flaws
□ No critical finding left uninvestigated for >20 minutes
□ At least 3 semgrep passes for whitebox scans
```

---

## Exploit Priority Scoring Formula

```
priority_score = (impact × exploitability) / detection_time

Where:
  impact = CVSS base score (0-10)
  exploitability = adjusted CVSS exploitability score (0-3.9)
  detection_time = estimated time before blue team detects (hours)

Priority ratings:
  P1-IMMEDIATE: score ≥ 15  → Exploit now
  P2-HIGH:      score ≥ 8   → Public exploit or high-value target
  P3-MEDIUM:    score ≥ 3   → Document, attempt if time permits
  P4-LOW:       score < 3   → Log as informational

Exploitability modifiers (multiplicative):
  × 2.0  public_exploit_available
  × 0.5  auth_required
  × 1.5  network_accessible (vs local_only)
  × 0.7  user_interaction_required
  × 1.3  default_credentials
  × 1.2  version_match_confirmed
```
