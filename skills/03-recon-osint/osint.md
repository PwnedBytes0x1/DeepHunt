# /osint — Passive Reconnaissance & Open Source Intelligence

> **Skill type:** Recon  
> **Source:** 0x0pointer/skills `/osint`, 0xsteph/pentest-ai-agents `osint-collector`, superhackers `recon-and-enumeration`  
> **Chains into:** `/recon`, `/threat-modeling`, `/web-exploit`  
> **Chained from:** `/engagement-lifecycle` (Phase 2 start)

---

## Purpose

Gather maximum intelligence about the target **without touching it**. Every OSINT finding is a breadcrumb that reduces uncertainty and focuses active testing.

---

## Phase 1: DNS & Certificate Intelligence

### Certificate Transparency Logs
```bash
# crt.sh — find all certificates for a domain (reveals subdomains)
curl -s "https://crt.sh/?q=%.example.com&output=json" | \
  jq -r '.[].name_value' | sort -u | grep -v '\*'

# certspotter
curl -s "https://certspotter.com/api/v0/certs?domain=example.com" | \
  jq -r '.[].dns_names[]' | sort -u
```

### DNS Enumeration
```bash
# Zone transfer attempt (often fails but worth trying)
dig axfr @ns1.example.com example.com

# Subdomain brute force
subfinder -d example.com -o subdomains.txt
amass enum -passive -d example.com -o amass-subdomains.txt

# Resolve all subdomains
cat subdomains.txt | httpx -silent -status-code -title -o live-subdomains.txt

# DNS record enumeration
dnsrecon -d example.com -t std,brt,axfr,bing,yand,snoop
```

### What to look for:
- Dev/staging/admin subdomains (often less protected)
- Old/deprecated subdomains (version vulnerabilities)
- Cloud provider subdomains (CNAME takeover candidates)
- Internal subdomains accidentally exposed

---

## Phase 2: Search Engine Intelligence

### Google Dorking
```
# Find login pages
site:example.com inurl:login OR inurl:admin OR inurl:signin

# Find exposed files
site:example.com filetype:pdf OR filetype:doc OR filetype:xls

# Find config/backup files
site:example.com ext:config OR ext:bak OR ext:sql OR ext:.env

# Find exposed AWS buckets
site:s3.amazonaws.com "example"

# Find error messages (reveals tech stack)
site:example.com "error" OR "exception" OR "stack trace"

# Find internal tools
site:example.com "internal" OR "intranet" OR "vpn"
```

### Shodan / Censys Intelligence
```bash
# Shodan — find all IPs associated with org
shodan search "org:\"Example Corp\"" --fields ip_str,port,hostnames
shodan search "hostname:example.com" --fields ip_str,port,product,version
shodan search "ssl.cert.subject.cn:example.com" --fields ip_str,port

# Censys
censys search "example.com" --index hosts

# What to capture:
# - Open ports and services
# - Service versions (CVE hunting)
# - SSL certificate details
# - Banner information
```

### Wayback Machine / Historical Data
```bash
# Find historical endpoints (old APIs, removed pages)
waybackurls example.com | sort -u > wayback-urls.txt
gau example.com | sort -u > gau-urls.txt

# Extract interesting patterns
cat wayback-urls.txt | grep -E "\.(php|asp|aspx|jsp|env|config|bak|sql)" 
cat wayback-urls.txt | grep -E "/(admin|api|v[0-9]|internal|debug)"
```

---

## Phase 3: Leaked Credential Intelligence

### Public Breach Data
```bash
# Check for domain in breach databases
# Use HaveIBeenPwned API (requires key)
curl -H "hibp-api-key: YOUR_KEY" \
  "https://haveibeenpwned.com/api/v3/breacheddomain/example.com"

# IntelX API search
# dehashed.com API search
# Note: Use only for authorized engagements
```

### GitHub Secret Hunting
```bash
# trufflehog — scan GitHub org
trufflehog github --org=example-corp --only-verified

# gitleaks — scan a repository
gitleaks detect --source /path/to/repo --report-format json

# Manual GitHub search
# Search: "example.com" password OR secret OR api_key
# Search: "example.com" filename:.env
# Search: org:example-corp extension:json api_key
```

### Common secrets to hunt:
```
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY
GITHUB_TOKEN, GITLAB_TOKEN
DATABASE_URL, MONGODB_URI
API_KEY, SECRET_KEY, PRIVATE_KEY
JWT_SECRET, SESSION_SECRET
TWILIO_AUTH_TOKEN, SENDGRID_API_KEY
```

---

## Phase 4: Technology Stack Intelligence

### Passive Stack Fingerprinting
```bash
# whatweb — identify CMS, frameworks, libraries
whatweb https://example.com

# wappalyzer — browser extension or CLI
wappalyzer https://example.com

# BuiltWith — via web or API
# Netcraft — technology survey
```

### Job Postings Intelligence
Job postings reveal the tech stack:
```
"We use: React, Node.js, PostgreSQL, AWS ECS, Redis"
→ Attack surface: GraphQL/REST API, JWT auth, AWS metadata, Redis misconfiguration

"Looking for: Django/Python, MySQL, nginx, Docker"
→ Attack surface: Django admin, SQL injection, nginx misconfiguration
```

### OSINT Social Engineering Targets
```bash
# Employee enumeration
theHarvester -d example.com -l 500 -b linkedin,google,bing

# LinkedIn enumeration (via API or manual)
# -> Job titles reveal: DB admins, cloud engineers, security team size
# -> Names → phishing target list

# Social media profiles
sherlock username  # find user across platforms
holehe email@example.com  # check email across services
maigret username  # comprehensive username check
```

---

## Phase 5: Infrastructure Intelligence

### Cloud Provider Detection
```bash
# Check for cloud-hosted infrastructure
# AWS IP range check
curl -s https://ip-ranges.amazonaws.com/ip-ranges.json | \
  python3 -c "import json,sys; [print(p['ip_prefix']) for p in json.load(sys.stdin)['prefixes'] if p.get('service')=='EC2']" | \
  grep "$(dig +short example.com)"

# Check for S3 buckets
# bucket-name patterns: example-com, examplecom, example_assets
aws s3 ls s3://example-com 2>/dev/null || echo "Not accessible"

# GCS bucket check
curl -s "https://storage.googleapis.com/example-com/"
```

### Subdomain Takeover Candidates
```bash
# Check for dangling CNAME records
subjack -w subdomains.txt -t 100 -timeout 30 -o takeover-candidates.txt

# Common takeover fingerprints:
# GitHub Pages: "There isn't a GitHub Pages site here"
# Heroku: "No such app"
# Netlify: "Not Found - Request ID"
# S3: "NoSuchBucket"
# Azure: "404 Web Site not found"
```

---

## OSINT Findings Template

```json
{
  "domain": "example.com",
  "subdomains": ["api.example.com", "admin.example.com", "dev.example.com"],
  "exposed_services": [
    {"host": "api.example.com", "port": 443, "service": "nginx/1.18.0"},
    {"host": "admin.example.com", "port": 8080, "service": "Apache/2.4.49"}
  ],
  "leaked_credentials": [
    {"source": "GitHub", "type": "AWS_ACCESS_KEY", "repo": "example-corp/app"}
  ],
  "tech_stack": ["React", "Node.js", "PostgreSQL", "AWS"],
  "employees": ["john.doe@example.com", "jane.smith@example.com"],
  "takeover_candidates": ["blog.example.com → nonexistent.github.io"],
  "interesting_urls": ["/admin/login", "/api/v1/users", "/.env.bak"]
}
```

---

## Chain Into Active Recon

After OSINT, feed findings into:
- `/recon` — active port scanning using discovered IPs/subdomains
- `/credential-audit` — test any discovered credentials
- `/web-exploit` — test dev/staging subdomains
- `/cloud-security` — investigate AWS/GCP/Azure exposure
- `/analyze-cve` — investigate identified service versions
