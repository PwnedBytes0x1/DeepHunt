# /reporting + /remediate + /request-cves — Security Report Generation

> **Skill type:** Reporting  
> **Source:** 0x0pointer/skills `/remediate`, `/gh-export`, `/request-cves`  
> **Chains into:** End of engagement  
> **Chained from:** All exploitation skills (findings)

---

## Part 1: Report Structure

### Executive Summary (Non-Technical)
```markdown
## Executive Summary

During the [duration] security assessment of [target], [N] vulnerabilities were 
identified across [scope areas]. Of these, [X] are rated Critical or High severity 
and require immediate remediation.

**Key Findings:**
- **Critical:** [brief description] — enables [business impact]
- **High:** [brief description] — enables [business impact]

**Business Risk:** If left unaddressed, these vulnerabilities could enable 
an attacker to [worst case: data breach / ransomware / financial fraud].

**Recommended Immediate Actions:**
1. [Action 1 within 24h]
2. [Action 2 within 1 week]
3. [Action 3 within 30 days]
```

### Technical Finding Format
```markdown
## Finding [N]: [Title]

| Field | Value |
|-------|-------|
| **Severity** | Critical (CVSS 9.8) |
| **CVSS Vector** | CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| **CVE** | CVE-2021-XXXXX (if applicable) |
| **CWE** | CWE-89 (SQL Injection) |
| **OWASP** | A03:2021 - Injection |
| **Affected** | https://target.com/api/search |

### Description
[Clear technical description of the vulnerability]

### Steps to Reproduce
1. Navigate to https://target.com/api/search
2. Set parameter `q` to: `' OR 1=1--`
3. Observe that all records are returned

### Evidence
![Screenshot](evidence/sqli-all-records.png)
```
Request: GET /api/search?q='%20OR%201%3D1-- HTTP/1.1
Response: {"users": [...all 50000 users...]}
```

### Impact
An attacker can extract all user data from the database, including 
passwords, emails, and PII. CVSS Environmental Score adjusted to 9.8 
due to 50,000 affected users.

### Remediation
**Immediate:** Use parameterized queries:
\`\`\`python
# Vulnerable:
cursor.execute("SELECT * FROM users WHERE name='" + user_input + "'")

# Fixed:
cursor.execute("SELECT * FROM users WHERE name=?", (user_input,))
\`\`\`

**Additional Controls:**
- Enable WAF rule for SQLi detection
- Implement principle of least privilege on DB user
- Enable query logging for anomaly detection

### References
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [CWE-89](https://cwe.mitre.org/data/definitions/89.html)
```

---

## Part 2: Auto-Generated Code Patches (/remediate)

For every confirmed finding, generate specific code fixes:

### SQLi Fix
```python
# Vulnerable (Python/SQLite)
def search_users(name):
    conn.execute("SELECT * FROM users WHERE name='" + name + "'")

# Fixed
def search_users(name):
    conn.execute("SELECT * FROM users WHERE name=?", (name,))
```

### XSS Fix
```javascript
// Vulnerable
document.getElementById('output').innerHTML = userInput;

// Fixed
const div = document.createElement('div');
div.textContent = userInput;  // textContent escapes HTML
document.getElementById('output').appendChild(div);

// Or use DOMPurify for rich HTML
document.getElementById('output').innerHTML = DOMPurify.sanitize(userInput);
```

### IDOR Fix
```python
# Vulnerable
@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    return db.query("SELECT * FROM users WHERE id=?", user_id)

# Fixed — add ownership check
@app.route('/api/users/<int:user_id>')
@require_auth
def get_user(user_id):
    current_user = get_current_user()  # From JWT/session
    if current_user.id != user_id and not current_user.is_admin:
        return {"error": "Forbidden"}, 403
    return db.query("SELECT * FROM users WHERE id=?", user_id)
```

### JWT Fix
```javascript
// Vulnerable — accepts algorithm:none
const decoded = jwt.verify(token, secret);  // jwt library may accept alg:none

// Fixed — explicitly specify algorithm
const decoded = jwt.verify(token, secret, { algorithms: ['HS256'] });
// Or for RS256:
const decoded = jwt.verify(token, publicKey, { algorithms: ['RS256'] });
```

---

## Part 3: CVE Submission Package (/request-cves)

### MITRE CVE Submission Form
```
Product: [Product Name and Version]
Vendor: [Vendor Name]
Vulnerability Type: [CWE description]
Description: 
  [Product Name] version [X.Y.Z] and earlier is vulnerable to [vulnerability type].
  An unauthenticated remote attacker can [impact] by [method].

CVSS Vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H

Affected Versions: <= [version]
Fixed Version: [version] (or "Unpatched")

Timeline:
  - [date]: Vulnerability discovered
  - [date]: Vendor notified
  - [date]: Vendor confirmed
  - [date]: Fix released (or "Vendor unresponsive after 90 days")
  - [date]: Public disclosure

Reporter: [Your name/organization]
```

### GitHub Security Advisory (GHSA) Draft
```markdown
---
title: [Vulnerability title]
labels: [severity: critical]
---

## Summary
[Brief description]

## Severity
Critical (CVSS 9.8)

## Affected Versions
- `<= [version]`

## Details
[Technical details]

## PoC
```
[PoC code or steps]
```

## Impact
[Business impact description]

## Patches
Patched in version [X.Y.Z].

## Workarounds
[If any]

## References
- [CVE link]
- [Advisory link]
```

---

## findings.json Schema

```json
{
  "engagement": {
    "target": "example.com",
    "start": "2025-05-30",
    "end": "2025-05-30",
    "assessor": "AI Agent"
  },
  "summary": {
    "critical": 2,
    "high": 4,
    "medium": 7,
    "low": 12,
    "informational": 8
  },
  "findings": [
    {
      "id": "FINDING-001",
      "title": "SQL Injection in Search API",
      "severity": "CRITICAL",
      "cvss_score": 9.8,
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
      "cwe": "CWE-89",
      "owasp": "A03:2021",
      "affected": ["https://api.example.com/search"],
      "evidence_files": ["evidence/sqli-response.txt", "evidence/sqli-screenshot.png"],
      "poc_file": "pocs/finding-001-sqli.http",
      "patch_file": "patches/finding-001-fix.py",
      "mitre_technique": "T1190",
      "validated": true,
      "confidence": 1.0
    }
  ]
}
```
