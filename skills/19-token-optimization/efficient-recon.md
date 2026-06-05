# Efficient Recon — Maximum Intel, Minimum Tool Calls

## The Recon Budget Mindset

Recon has diminishing returns. The first 20% of recon effort yields 80% of actionable intel. The trap is continuing to enumerate forever when you already have enough to start testing.

**Rule:** Recon stops when you have enough to start the next phase — not when you've found everything.

---

## Priority Stack — What to Find First

### Must-Have Before Anything Else
```
1. Live hosts (is the target up?)
2. Open ports (what's exposed?)
3. Technology fingerprint (what's running?)
4. Entry points (login, search, upload, API endpoints)
```

### Good to Have (if fast)
```
5. Subdomains (expanded attack surface)
6. Historical data (Wayback, shodan)
7. Known CVEs for detected versions
```

### Skip Unless Specifically Needed
```
- Full 65535 port scan (use top-1000 first)
- Recursive deep spidering (start with 2 levels)
- OS fingerprinting (-O) unless escalation matters
- Banner grabbing beyond what -sV provides
- All subdomain tools (one is enough to start)
```

---

## Layered Recon: Fast → Slow

### Layer 1: Passive (0 network noise, instant)
```bash
# Run ALL of these before touching the target:
whois target.com
dig target.com A AAAA MX TXT
curl -s "https://crt.sh/?q=%.target.com&output=json" | \
  python3 -c "import sys,json; [print(r['name_value']) for r in json.load(sys.stdin)]" | sort -u
# Shodan/Censys search (passive)
# theHarvester (passive sources only)
theHarvester -d target.com -b google,bing,certspotter -f passive_recon.html
```

### Layer 2: Light Active (low noise)
```bash
# Only run if passive didn't give you enough
subfinder -d target.com -silent
nmap -sV --top-ports 1000 target.com
curl -sI https://target.com  # Tech stack from headers
```

### Layer 3: Moderate Active (some noise)
```bash
# Only run specific tools for specific gaps
# "I need to find API endpoints" → feroxbuster on /api
# "I need more subdomains" → amass passive mode
# NOT: run all tools by default
```

### Layer 4: Aggressive (noisy - only if authorized scope allows)
```bash
# Full port scan only when top-1000 missed something obvious
nmap -p- --min-rate 5000 target.com
# Aggressive nikto only when quick scan found interesting tech
nikto -h https://target.com -Tuning 123bde
```

---

## Early Stopping Signals

Stop recon and move to testing when you see:

```
Signal 1: Login form found → Test auth attacks NOW, don't wait for full enum
Signal 2: API endpoints with parameters → Test injection NOW
Signal 3: File upload functionality → Test upload bypass NOW
Signal 4: Known vulnerable tech version (CVE exists) → Test CVE NOW
Signal 5: Admin panel found → Test default creds NOW
```

**The Golden Rule:** If you have an attack surface, attack it. Don't keep enumerating.

---

## Tool-Specific Efficiency Settings

### Nmap — Fast Mode
```bash
# Good default (fast, finds 95% of open ports)
nmap -sV -T4 --top-ports 1000 target.com

# NOT this (slow, marginal improvement)
nmap -sV -A -p- -T3 target.com  # Takes 10x longer

# If you specifically need UDP
nmap -sU --top-ports 100 target.com  # Top 100 UDP only

# Targeted version detection (after finding open ports)
nmap -sV -p 80,443,8080,8443 target.com
```

### Gobuster/FFuF — Efficient Web Enum
```bash
# Good: Start with medium wordlist + common extensions
ffuf -u https://target.com/FUZZ \
  -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
  -e .php,.asp,.aspx,.jsp,.txt,.bak \
  -mc 200,301,302,403 \
  -t 50 -c

# NOT: use massive wordlists upfront
# SecLists/Discovery/Web-Content/big.txt → use only if medium found nothing

# Stop after finding: login, admin, api, upload, config
# These are your targets — don't enumerate everything
```

### Subfinder — Subdomain Discovery
```bash
# Good: One passive tool first
subfinder -d target.com -silent -o subdomains.txt

# Then: Check which are live
httpx -l subdomains.txt -silent -status-code -title -o live_subs.txt

# Only run amass if subfinder < 5 results
# NOT: run 5 subdomain tools by default
```

---

## Recon Output — Compact Storage

### Compact Recon Summary Format
```
TARGET INTEL
============
Domain: target.com
IPs: 1.2.3.4 (main), 5.6.7.8 (mail)
Subdomains: admin.target.com, api.target.com, dev.target.com (dev= interesting)
Open ports: 22, 80, 443, 8080, 3306
Tech: nginx/1.20.1, PHP/7.4.3, MySQL (from errors)
CVEs: PHP 7.4.3 → CVE-2021-21702 (minor), nginx 1.20.1 → no critical

ENTRY POINTS (prioritized):
1. /admin → HTTP 403 (bypass attempt)
2. /api/v1/ → REST API (test injection, auth)
3. /upload → File upload form (test bypass)
4. /login → Auth form (test brute force, SQLi)

SKIP: /static/, /assets/, /css/ (no attack surface)
```

### Tracking Tested vs Untested
```
[ ] /admin → TO TEST
[x] /login → TESTED, no SQLi, brute force pending
[!] /api/search → VULNERABLE (SQLi confirmed)
[-] /api/users → 403 BLOCKED
```

---

## Recon Checklist (Minimal Version)

```
Fast passive recon (< 5 min):
[ ] DNS: dig A, MX, TXT, CNAME
[ ] Cert transparency: crt.sh for subdomains
[ ] Shodan: any exposed services/old versions
[ ] Wayback: archive.org for old endpoints

Active recon (< 15 min):
[ ] nmap top-1000 ports + service detection
[ ] Tech fingerprint from headers/errors
[ ] Directory enum with medium wordlist
[ ] Check robots.txt, sitemap.xml, /.well-known/

Stop here if you have attack surface. Move to exploitation.
```
