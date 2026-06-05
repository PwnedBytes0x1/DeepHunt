# /email-security — SPF, DKIM, DMARC, Open Relay & Email Infrastructure Attacks

> **Skill type:** Vulnerability Finding / Exploitation  
> **Source:** 0x0pointer/skills `/email-security`, OWASP Testing Guide (OTG-CONFIG-010)  
> **Chains into:** `/red-team-ops` (phishing), `/credential-audit`, `/reporting`  
> **Chained from:** `/osint` (MX record discovery)

---

## Purpose

Audit email security configuration (SPF, DKIM, DMARC, MTA-STS, SMTP), test for open relays, email spoofing, and enumerate exposed email infrastructure for red team phishing campaigns.

---

## Phase 1: DNS Email Record Enumeration

```bash
TARGET="example.com"

# MX records — identify mail servers
dig MX $TARGET
nslookup -type=MX $TARGET

# SPF record (TXT)
dig TXT $TARGET | grep "v=spf1"
# Parse SPF: allowed IPs, includes, redirect, ~all vs -all vs +all

# DKIM — guess selectors (common: default, google, mail, k1, s1, selector1)
for selector in default google mail k1 s1 selector1 selector2 smtp dkim; do
  result=$(dig TXT ${selector}._domainkey.$TARGET 2>/dev/null | grep "v=DKIM1")
  [ -n "$result" ] && echo "DKIM selector: $selector" && echo "$result"
done

# DMARC record
dig TXT _dmarc.$TARGET
# Parse: p=none|quarantine|reject (policy), rua= (report address), pct= (percentage)

# MTA-STS policy
curl -s "https://mta-sts.$TARGET/.well-known/mta-sts.txt"
dig TXT _mta-sts.$TARGET

# BIMI (Brand Indicators for Message Identification)
dig TXT default._bimi.$TARGET
```

---

## Phase 2: SPF Analysis & Spoofing Risk

### SPF Mechanism Scoring

```
+all  → FAIL (everyone is authorized — completely useless SPF)
~all  → SOFTFAIL (unauthorized senders pass but flagged — spoofing possible)
-all  → PASS (hard fail — unauthorized senders rejected)
?all  → NEUTRAL (no policy — spoofing possible)

Spoofing risk:
  +all or missing → Critical — anyone can spoof
  ~all            → High — softfail often accepted by spam filters
  -all            → Low (but still check DMARC)
```

### SPF Lookup Count (10-limit bypass)
```bash
# SPF has a max of 10 DNS lookups — if exceeded, SPF evaluation fails → PERMERROR
# Use dmarcian SPF surveyor or mxtoolbox to count lookups
curl "https://dmarcian.com/spf-survey/?domain=$TARGET"

# Many include: chains exceed 10 → SPF always fails → effective bypass
```

### Test Email Spoofing
```bash
# Send spoofed email (only on authorized engagements)
# Method 1: swaks (Swiss Army Knife SMTP)
swaks --to victim@example.com \
      --from "ceo@target.com" \
      --server target-mx-server.com \
      --header "Subject: Urgent: Password Reset" \
      --body "Please click this link..."

# Method 2: Python smtplib
python3 -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('Test spoofing email body')
msg['Subject'] = 'Test'
msg['From'] = 'ceo@target.com'
msg['To'] = 'victim@target.com'
s = smtplib.SMTP('mail.target.com', 25)
s.sendmail('ceo@target.com', ['victim@target.com'], msg.as_string())
s.quit()
"
```

---

## Phase 3: DKIM Analysis

```bash
# Decode and analyze DKIM public key
selector="_domainkey_selector"
dig TXT ${selector}._domainkey.$TARGET | grep -o '".*"' | tr -d '"' | \
  python3 -c "
import sys, base64
from cryptography.hazmat.primitives.serialization import load_der_public_key
data = sys.stdin.read().replace('p=','').replace(' ','').replace(';','')
try:
    key = load_der_public_key(base64.b64decode(data))
    print(f'Key size: {key.key_size} bits')
    if key.key_size < 1024: print('CRITICAL: Weak DKIM key!')
    elif key.key_size < 2048: print('WARNING: DKIM key < 2048 bits')
except Exception as e:
    print(f'Error: {e}')
"

# Check for DKIM key rotation (old keys still valid?)
# If DKIM key is 512/768/1024 bits — factoring attacks possible (DKIM key rollover needed)
```

---

## Phase 4: DMARC Policy Analysis

```bash
# Parse DMARC policy
dig TXT _dmarc.$TARGET | grep -o '".*"' | tr -d '"'

# Risk assessment
# p=none    → Critical: only monitoring, no enforcement — spoofing succeeds
# p=quarantine → Medium: spoofed emails go to spam (depends on spam filter)
# p=reject  → Low: spoofed emails rejected (strongest protection)

# pct=N → Only applies policy to N% of emails
# pct=10 with p=reject → 90% of spoofed emails still pass!

# rua/ruf → Report delivery (who gets DMARC aggregate/forensic reports)
```

---

## Phase 5: Open Relay Testing

```bash
# An open relay forwards email from/to anyone — major spam abuse vector

# Connect directly to SMTP
telnet mail.target.com 25

# SMTP commands to test relay
EHLO attacker.com
MAIL FROM: <external@attacker.com>
RCPT TO: <external@gmail.com>   # External to external = relay attempt
DATA
Subject: Relay test
.
QUIT

# If "250 OK" received after DATA → Open relay CONFIRMED (Critical)

# Automated open relay check
nmap --script smtp-open-relay -p 25,465,587 mail.target.com
swaks --to test@gmail.com --from fake@attacker.com --server mail.target.com

# Also test authenticated relay abuse
# Can a low-privilege user relay to external domains?
```

---

## Phase 6: SMTP Security Checks

```bash
# STARTTLS support (encryption in transit)
nmap --script smtp-commands -p 25 mail.target.com | grep -i "starttls\|tls"
openssl s_client -starttls smtp -connect mail.target.com:587

# Auth mechanisms
nmap --script smtp-commands -p 25 mail.target.com | grep "AUTH"
# AUTH PLAIN / LOGIN in cleartext on port 25 → credentials in cleartext

# Enumerate users
nmap --script smtp-enum-users --script-args smtp-enum-users.methods=VRFY,EXPN,RCPT \
  -p 25 mail.target.com

# VRFY user enumeration
vrfy_test() {
  echo -e "VRFY $1\nQUIT" | nc -w3 mail.target.com 25
}
vrfy_test "admin"
vrfy_test "root"
vrfy_test "postmaster"

# Version fingerprinting → CVE hunting
nmap -sV -p 25,465,587 mail.target.com
# Exim < 4.94 → many critical CVEs
# Postfix version disclosure
# Sendmail version
```

---

## Phase 7: Email Header Analysis

```bash
# From a received email, analyze full headers for intelligence
# Reveals: originating IP, MTA path, MX chain, authentication results

# Key fields in Received-SPF: PASS / FAIL / SOFTFAIL / NEUTRAL
# Key fields in DKIM-Signature: valid signature = not spoofed
# Key fields in Authentication-Results: dmarc=pass / fail
# X-Originating-IP: real sender IP (often leaked)
# Received: shows full relay path

# Python email header analyzer
python3 -c "
import email, sys
msg = email.message_from_string(open('email.eml').read())
for key in ['From','Reply-To','Return-Path','X-Originating-IP','Received-SPF',
            'DKIM-Signature','Authentication-Results']:
    v = msg.get(key)
    if v: print(f'{key}: {v}')
"
```

---

## Email Security Finding Severity

| Finding | Severity | Impact |
|---------|----------|--------|
| No SPF record | High | Anyone can spoof domain |
| SPF +all | Critical | Explicit permission to spoof |
| SPF ~all (no DMARC) | High | Softfail often accepted |
| No DMARC | High | SPF/DKIM failures not enforced |
| DMARC p=none | High | Monitoring only, no protection |
| DMARC pct < 100 | Medium | Partial enforcement |
| Open relay | Critical | Spam/phishing platform |
| SMTP VRFY enabled | Low | User enumeration |
| Weak DKIM key (≤1024) | High | Key factoring → email forgery |
| No STARTTLS | High | Email in cleartext in transit |
| Auth over cleartext port | High | Credential interception |
| Missing MTA-STS | Medium | SMTP downgrade attack |

---

## Remediation Recommendations

```
SPF: "v=spf1 ip4:MAIL_SERVER_IP include:sendgrid.net -all"
     → Use -all (hard fail), not ~all

DKIM: Generate 2048-bit RSA keys, rotate annually
      openssl genrsa -out dkim-private.pem 2048
      openssl rsa -in dkim-private.pem -pubout -out dkim-public.pem

DMARC: "_dmarc.example.com TXT v=DMARC1; p=reject; pct=100; rua=mailto:dmarc@example.com"
       → Start with p=quarantine, move to p=reject after monitoring

MTA-STS: Enable to prevent SMTP downgrade attacks
         https://mta-sts.example.com/.well-known/mta-sts.txt
         version: STSv1
         mode: enforce
         mx: mail.example.com
         max_age: 604800
```
