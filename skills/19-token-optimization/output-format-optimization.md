# Output Format Optimization

Structured outputs for maximum information density. Choosing the right format
eliminates waste and makes downstream processing faster.

---

## Format Selection Matrix

| Content Type | Best Format | Worst Format | Density |
|-------------|-------------|--------------|---------|
| Findings list | Table | Prose paragraphs | 5x |
| Step sequence | Numbered list | Prose with "first", "then" | 3x |
| Comparison | Table | Alternating paragraphs | 6x |
| Single answer | One line | Paragraph with context | 10x |
| Command to run | Code block | "You should run the command..." | 4x |
| Key-value data | YAML/JSON | Sentences | 5x |
| Pass/fail checks | Checkbox list | Narrative | 4x |
| Errors/status | Compact log | Full stack trace | 20x |

---

## Tables vs Prose vs Lists

### When to Use Tables
```
Use tables for:
- Multi-attribute findings (CVE, severity, description, fix)
- Comparisons (tool A vs tool B vs tool C)
- Status matrices (endpoint × status code × auth required)
- Vulnerability matrices (param × type × confirmed)

Avoid tables for:
- Single-attribute lists (just use bullets)
- Sequential steps (use numbered list)
- Prose explanation (tables can't carry nuance)
```

**Table example (security findings):**
```
| Endpoint | Param | Vuln | Severity | Payload |
|----------|-------|------|----------|---------|
| /login | username | SQLi | Critical | ' OR 1=1-- |
| /search | q | XSS | High | <img src=x onerror=alert(1)> |
| /upload | file | Unrestricted upload | High | .php extension |
| /api/user | id | IDOR | Medium | Change 1001→1000 |
```
Tokens: ~80. Equivalent prose: ~250. Density gain: 3x.

### When to Use Lists
```
Use bulleted lists for:
- Unordered items with equal priority
- Feature/capability enumeration
- "Things to check" without sequence

Use numbered lists for:
- Ordered steps (sequence matters)
- Priority ranking (1=most important)
- Phase progression

Use flat lists (no nesting) for:
- Simple enumerations
- Tool lists
- Finding summaries

Avoid deep nesting: max 2 levels.
```

**List example (recon checklist):**
```
Web recon checklist:
1. Stack fingerprint (curl -I, whatweb)
2. High-value paths (admin, api, .git, .env)
3. CVE check on stack
4. Auth mechanism identification
5. Parameter discovery on entry points
6. Earliest stopping signal hit → exploit
```
Tokens: 55. Prose equivalent: 180. Gain: 3.3x.

### When to Use Prose
```
Use prose ONLY for:
- Nuanced explanation with causal reasoning
- Ambiguous situations requiring context
- Narrative attack chains (story format aids understanding)
- Anything where rigid structure destroys meaning

Prose is always more token-expensive. Use sparingly.
```

---

## Code Block Optimization

### Always Use Code Blocks For:
```
- Commands (even one-liners)
- Payloads
- Config snippets
- Expected output examples
- Error messages
- File contents
```

### Code Block Density Patterns
```bash
# VERBOSE (tells you what it does, repeats in comment):
# This command uses nmap to scan the target for open ports
# The -sV flag enables service version detection
# The -T4 flag sets aggressive timing
nmap -sV -T4 target.com

# COMPACT (let the command speak):
nmap -sV -T4 target.com    # service scan, aggressive timing

# ULTRA-COMPACT (for experienced readers):
nmap -sV -T4 target.com
```

### Multi-Command Blocks
```bash
# Chain related commands to show workflow:
# Bad (separate blocks, verbose commentary between):
curl -I https://target.com
# Now check the headers...
curl -I https://target.com/admin

# Good (single block, workflow clear):
# Stack + high-value path check:
curl -sI https://target.com | grep -E "Server:|X-Powered-By:|Location:"
for p in admin api .git .env swagger.json actuator; do
  printf "%s: " $p
  curl -so/dev/null -w "%{http_code}\n" https://target.com/$p
done
```

---

## Finding Report Formats

### Minimal Finding Format
```
FINDING: SQL Injection
SEVERITY: Critical
ENDPOINT: POST /api/login
PARAM: username
PAYLOAD: ' OR '1'='1'--
EVIDENCE: Returns user data for any password
IMPACT: Authentication bypass, potential full DB access
FIX: Parameterized queries
```
Tokens: ~55.

### Machine-Parseable Finding Format (YAML)
```yaml
findings:
  - id: FINDING-001
    title: SQL Injection in Login
    severity: critical
    endpoint: POST /api/login
    parameter: username
    cvss: 9.8
    payload: "' OR '1'='1'--"
    confirmed: true
    impact: auth_bypass
    remediation: parameterized_queries
```
Tokens: ~70. Easily parsed by downstream tools.

### Bulk Findings (Table)
```
| ID | Title | Sev | Endpoint | Confirmed |
|----|-------|-----|----------|-----------|
| F1 | SQLi | Crit | /login#user | ✓ |
| F2 | XSS | High | /search#q | ✓ |
| F3 | IDOR | Med | /api/user#id | ✓ |
| F4 | CSRF | Low | /settings | Suspected |
```
Tokens: ~80 for 4 findings. Prose equivalent: ~400.

---

## Tool Output Compression

### nmap Output Reduction
```bash
# Raw nmap output (300+ lines for full scan):
# Compress to essential:
nmap -oG - target.com | grep "Ports:" | \
  grep -oP '\d+/open/tcp/[^/]*/[^,/]+' | \
  awk -F/ '{print $1 " " $5 " " $7}'

# Output:
# 22 ssh OpenSSH_8.2p1
# 80 http Apache/2.4.29
# 443 https Apache/2.4.29
# 3306 mysql MySQL/5.7.36

# 4 lines vs 300 lines. Same actionable info.
```

### HTTP Response Compression
```python
# Don't log full response; extract signal:
import requests, re

r = requests.get('https://target.com')
print({
    'status': r.status_code,
    'server': r.headers.get('Server',''),
    'powered': r.headers.get('X-Powered-By',''),
    'csp': bool(r.headers.get('Content-Security-Policy')),
    'hsts': bool(r.headers.get('Strict-Transport-Security')),
    'size': len(r.content),
    'title': re.search(r'<title>(.*?)</title>', r.text, re.I).group(1)[:50] if '<title>' in r.text.lower() else '',
})
# Output: single dict, ~80 chars vs full HTTP response (potentially MBs)
```

### JSON Response Compression
```python
# Full API response might be 5000 tokens
# Extract only relevant fields:
import json, sys

def extract_fields(obj, fields):
    if isinstance(obj, list):
        return [extract_fields(i, fields) for i in obj[:10]]  # Max 10 items
    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if k in fields}
    return obj

response = json.loads(full_response_text)
# Instead of printing everything:
print(json.dumps(extract_fields(response, ['id', 'username', 'email', 'role']), indent=2))
```

---

## Log and Error Output Filtering

### Filter Before Displaying
```bash
# Full nmap script output: 1000+ lines
# Filter to findings only:
nmap --script vuln target.com | grep -E "VULNERABLE|CVE-|risk:|CRITICAL" | head -20

# Full gobuster output: 500+ lines
# Filter to interesting status codes:
gobuster dir -u https://target.com -w wordlist.txt 2>/dev/null | \
  grep -E "\(Status: 200\)|\(Status: 301\)|\(Status: 403\)" | \
  grep -v "\.css\|\.js\|\.png\|\.jpg\|\.ico"

# Full sqlmap output: very verbose
sqlmap -u "URL?id=1" --dbs --batch 2>&1 | \
  grep -E "available databases|^\[|Type:|Title:|Payload:" | head -30
```

### Error Message Compression
```
# Full stack trace (200+ lines) → extract signal:
python3 app.py 2>&1 | tail -5
# Shows: final error + immediate context

# OR:
python3 app.py 2>&1 | grep -E "Error:|Exception:|line [0-9]+" | head -10
```

---

## Status and Progress Formats

### Compact Progress Indicators
```
# Instead of: "I have completed step 1 of 5. Now I am moving on to step 2..."
# Use:
[1/5] Port scan ✓
[2/5] Web fingerprint ✓
[3/5] CVE check... (running)
[4/5] SQLi test pending
[5/5] Report pending
```

### Compact Status Summary
```
# Instead of verbose status report:
STATUS: Phase 2 of 3
  Completed: port scan (22,80,443,3306 open), stack fingerprint (Apache 2.4.29/PHP 7.4/MySQL)
  Active: CVE-2021-41773 verification
  Pending: SQLi testing, credential extraction
  Blockers: none
  ETA calls: ~3
```

---

## Anti-Patterns

```
1. Explaining format choices
   BAD: "I'll present this as a table to make it easier to read..."
   GOOD: [just use the table]

2. Repeating information in different formats
   BAD: Table of findings, then prose summary of same findings
   GOOD: Table only

3. Showing all tool output unfiltered
   BAD: paste entire nmap output
   GOOD: extract 5 relevant lines

4. Verbose section headers
   BAD: "## Findings from the Vulnerability Assessment"
   GOOD: "## Findings"

5. Numbered lists for non-sequential items
   BAD: "1. The server uses Apache. 2. PHP is also running. 3. MySQL is the database."
   GOOD: Stack: Apache/PHP/MySQL

6. Empty table cells
   BAD: Sparse table with many N/A cells
   GOOD: Only create table when most cells have data; else use list
```
