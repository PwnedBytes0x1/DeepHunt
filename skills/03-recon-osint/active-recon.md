# /recon — Active Reconnaissance & Service Enumeration

> **Skill type:** Recon  
> **Source:** superhackers `recon-and-enumeration`, pentest-ai-agents `recon-advisor`, Autonomous-Pen-Testing recon pipelines  
> **Chains into:** `/web-exploit`, `/api-security`, `/network-exploit`, `/analyze-cve`  
> **Chained from:** `/osint`

---

## Purpose

Map the exact attack surface: every open port, every running service, every web endpoint, every API route. Active recon is where hypothesis meets evidence.

---

## Recon Pipeline Selection

Choose based on engagement type and stealth requirements:

| Pipeline | Tools | Use Case | Time |
|----------|-------|----------|------|
| **full** | nmap → whatweb → wafw00f → nikto → ffuf → nuclei | Comprehensive assessment | 2-4h |
| **quick** | nmap → whatweb → ffuf | Fast initial sweep | 15-30m |
| **subdomain** | subfinder → httpx | Domain attack surface mapping | 5-15m |
| **stealth** | nmap (slow SYN T1) → whatweb | Evasive, IDS-avoiding | 4-8h |
| **api** | kiterunner → httpx → spec-hunting | API surface discovery | 30-60m |

---

## Phase 1: Port Scanning

### Fast initial sweep
```bash
# Top 1000 ports — fastest
nmap -sS -T4 --top-ports 1000 -oN nmap-fast.txt $TARGET

# Full port range (after fast scan confirms host is up)
nmap -sS -T4 -p- -oN nmap-full.txt $TARGET

# UDP top 100 (often missed)
nmap -sU -T3 --top-ports 100 -oN nmap-udp.txt $TARGET
```

### Service version detection
```bash
# Version + OS detection + default scripts on open ports
nmap -sV -sC -O -p $(grep "^[0-9]" nmap-full.txt | cut -d/ -f1 | tr '\n' ',') \
  -oA nmap-detailed $TARGET

# Aggressive scan (when stealth not needed)
nmap -A -p- $TARGET -oA nmap-aggressive
```

### Masscan for speed
```bash
# Very fast full-port scan (use carefully — very noisy)
masscan -p1-65535 $TARGET --rate=10000 -oJ masscan-results.json
rustscan -a $TARGET --ulimit 5000 -- -sV -sC
```

### Parse results
```bash
# Extract open ports and services
grep "open" nmap-detailed.nmap | awk '{print $1, $3, $4}' | sort > services.txt
# Format: port/protocol  state  service/version
```

---

## Phase 2: Web Technology Fingerprinting

### HTTP probing
```bash
# Probe all discovered hosts for HTTP/HTTPS
httpx -l live-subdomains.txt -status-code -title -tech-detect \
  -follow-redirects -o httpx-results.txt

# More details
httpx -l live-subdomains.txt -json -o httpx-detailed.json \
  -include-response -screenshot
```

### Technology stack detection
```bash
# whatweb
whatweb -a 3 https://example.com -t 20 --log-json=whatweb.json

# wafw00f — WAF detection
wafw00f https://example.com

# Output important for:
# - Identifying CMS (WordPress, Drupal → known CVEs)
# - Identifying frameworks (React, Angular → different attack surface)
# - WAF type → determines bypass techniques
```

---

## Phase 3: Content & Directory Discovery

### Directory fuzzing
```bash
# ffuf — fast web fuzzer
ffuf -u https://example.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -mc 200,301,302,401,403 -c -t 40 -o ffuf-dirs.json

# Extended wordlists for thorough scan
ffuf -u https://example.com/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-big.txt \
  -mc 200,301,302,401,403 -c -t 20 -o ffuf-dirs-full.json

# gobuster
gobuster dir -u https://example.com -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -o gobuster-dirs.txt -t 40 -x php,asp,aspx,jsp,html,js

# feroxbuster — recursive
feroxbuster -u https://example.com -w /usr/share/seclists/... \
  -o feroxbuster.txt --depth 3 --auto-tune
```

### Interesting paths to check manually:
```
/admin, /administrator, /wp-admin, /console, /management
/.env, /.git, /.svn, /.DS_Store, /robots.txt, /sitemap.xml
/api, /api/v1, /api/v2, /graphql, /swagger, /openapi.json
/actuator (Spring Boot), /metrics, /health, /debug
/phpinfo.php, /info.php, /server-status, /server-info
/backup, /bak, /old, /test, /dev, /staging
```

---

## Phase 4: API Surface Discovery

### Spec hunting
```bash
# Common spec locations
for path in /swagger.json /swagger.yaml /openapi.json /openapi.yaml \
  /api-docs /docs/api /api/swagger.json /v1/swagger.json \
  /api/v1/docs /redoc /api/schema; do
  curl -s -o /dev/null -w "%{http_code} $path\n" https://example.com$path
done

# kiterunner — API endpoint discovery
kr scan https://example.com -w api-routes.kite --fail-status-codes 400,401,404,403,501,502,426,411
```

### JavaScript bundle analysis
```bash
# Extract API endpoints from JS bundles
# Download all .js files from page source
cat httpx-results.txt | while read url; do
  curl -s "$url" | grep -oE '"(/api/[^"]+)"' | sort -u
done

# katana — crawl and extract endpoints
katana -u https://example.com -d 5 -jc -kf all -o katana-endpoints.txt
```

---

## Phase 5: Vulnerability Scanning

### Nuclei — template-based scanning
```bash
# Run all templates (comprehensive but slow)
nuclei -u https://example.com -o nuclei-results.json -je -nc

# Targeted by severity
nuclei -u https://example.com -s critical,high -o nuclei-critical.json

# Specific categories
nuclei -u https://example.com -tags cve,oast,sqli,xss -o nuclei-web.json

# Use custom templates from your curated set
nuclei -u https://example.com -t custom-templates/ -o nuclei-custom.json
```

### Nikto — web server misconfigs
```bash
nikto -h https://example.com -output nikto-results.txt -Format txt
nikto -h https://example.com -Tuning x -output nikto-nox.txt  # no false positive categories
```

---

## Recon Findings Template

```json
{
  "target": "example.com",
  "scan_time": "2025-05-30T07:43:00Z",
  "open_ports": [
    {"port": 443, "service": "https", "version": "nginx/1.18.0"},
    {"port": 8080, "service": "http-alt", "version": "Apache/2.4.49"},
    {"port": 22, "service": "ssh", "version": "OpenSSH_7.9p1"}
  ],
  "web_technologies": ["React 18", "Node.js", "Express", "PostgreSQL"],
  "waf_detected": "Cloudflare",
  "directories": ["/admin/", "/api/v1/", "/.git/"],
  "api_endpoints": ["/api/v1/users", "/api/v1/orders", "/api/v1/admin"],
  "nuclei_findings": [
    {"template": "CVE-2021-41773", "severity": "critical", "host": "8080"}
  ],
  "interesting_files": ["/.env (403)", "/robots.txt (disallows: /admin, /api)"]
}
```

---

## Chain Decision Tree

```
If Apache 2.4.49 found on port 8080 → /analyze-cve CVE-2021-41773
If WordPress detected → /web-exploit with wpscan
If /api/ directory found → /api-security
If /.git/ found → git dump → /codebase
If admin panel found → /credential-audit
If cloud metadata hints → /cloud-security
If Active Directory indicators → /ad-assessment
If SSL/TLS issues → /ssl-tls-audit
```
