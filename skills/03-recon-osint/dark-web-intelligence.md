# /dark-web-intel — Dark Web & Breach Intelligence Gathering

> **Skill type:** OSINT / Threat Intelligence  
> **Source:** Recorded Future methodology, Intel 471, Hudson Rock threat intel  
> **Chains into:** `/credential-audit`, `/osint`, `/reporting`  
> **Chained from:** `/osint` (extended intelligence phase)

---

## Purpose

Gather threat intelligence from dark web forums, breach databases, and underground marketplaces. Identify stolen credentials, leaked data, and threat actor mentions related to the target — before attackers use them.

---

## ⚠️ Legal Notice
Dark web intelligence gathering must be passive (no purchasing, no participation in criminal activity). Use commercial threat intelligence platforms or public breach notification services only.

---

## Phase 1: Breach Database Intelligence

```bash
# HaveIBeenPwned — individual email check
curl -H "hibp-api-key: YOUR_KEY" \
  "https://haveibeenpwned.com/api/v3/breachedaccount/user@target.com"

# HaveIBeenPwned — domain-wide breach check (enterprise API)
curl -H "hibp-api-key: YOUR_KEY" \
  "https://haveibeenpwned.com/api/v3/breacheddomain/target.com"

# IntelligenceX — comprehensive breach data
# https://intelx.io/ — search emails, domains, IPs in breach data

# Dehashed — reverse lookup of breach data
curl -H "Authorization: Basic $(echo 'email:api_key' | base64)" \
  "https://api.dehashed.com/search?query=domain:target.com&size=100"

# Snusbase — breach database search
# Scylla.sh — free breach search
curl "https://scylla.sh/search?q=target.com&size=10"

# Parse for target.com credentials
cat breachdata.json | jq '.[] | select(.email | endswith("@target.com")) | {email, password, source}'
```

---

## Phase 2: Leaked Credentials on GitHub / Pastebin

```bash
# GitHub code search (via web or API)
# Search patterns for target domain:
# "target.com" password
# "target.com" secret  
# "target.com" api_key
# "@target.com" AND "password"

# GitHub API search
curl -H "Authorization: token GITHUB_TOKEN" \
  "https://api.github.com/search/code?q=%22target.com%22+%22password%22" | \
  jq '.items[] | {html_url, repository: .repository.full_name}'

# Pastebin / Gist monitoring
# pastehunter — monitor paste sites for keywords
python3 pastehunter.py -s "target.com"

# GitGuardian API
curl -H "Authorization: Token GG_API_KEY" \
  "https://api.gitguardian.com/v1/incidents?search=target.com"
```

---

## Phase 3: Dark Web Monitoring (Commercial Platforms)

```bash
# These require subscriptions but provide structured threat intel:

# Recorded Future — comprehensive dark web + CVE + threat actor intel
# Intel 471 — cybercriminal underground monitoring
# Flashpoint — threat intelligence platform
# Hudson Rock — compromised credentials monitoring
# SpyCloud — stolen credentials from malware logs

# Free tier options:
# DarkOwl — limited dark web search
# Tor Project search engines (manual, read-only)
# OnionSearch — search Tor hidden services

# What to look for:
# 1. Target company name mentioned on forums (e.g., breach announcements)
# 2. Employee credentials in stealer logs (RedLine, Raccoon, Vidar)
# 3. Source code or internal documents posted for sale
# 4. Target mentioned as victim on ransomware leak sites
```

---

## Phase 4: Stealer Log Analysis

```bash
# Stealer malware (RedLine, Raccoon, AZORult) exfiltrate:
# - Browser saved passwords
# - Session cookies
# - System info + screenshots
# - Crypto wallets

# Hudson Rock Cavalier API (free tier available)
curl "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-domain?domain=target.com"
# Returns: number of compromised machines, employees affected, recent infections

# Check for specific email
curl "https://cavalier.hudsonrock.com/api/json/v2/osint-tools/search-by-email?email=employee@target.com"

# Parsed intelligence from stealer logs often contains:
# - Active session cookies (can be used to bypass MFA!)
# - Corporate VPN credentials
# - Internal tool passwords (Jira, Confluence, GitHub)
# - AWS/GCP credentials saved in browser
```

---

## Phase 5: Ransomware Leak Site Monitoring

```bash
# Check if target has been listed on ransomware leak sites
# (Publicly visible, no Tor needed)

# DDoSecrets (non-profit, public interest leaks)
curl "https://ddosecrets.com/search?q=target+company"

# Ransomware.live — aggregates ransomware gang victim listings
curl "https://api.ransomware.live/recentvictims" | \
  jq '.[] | select(.company | test("target"; "i"))'

# Manual checks on clearnet ransomware sites:
# RansomLook.io — aggregator
# Ransomlook.io API: curl "https://www.ransomlook.io/api/targets"

# What to do if target is listed:
# → Flag as Critical in pre-engagement brief
# → Assume credentials in those leaked files are compromised
# → Recommend immediate credential rotation before/during assessment
```

---

## Phase 6: Threat Actor Intelligence

```bash
# Has a specific threat actor targeted this industry/org?

# MITRE ATT&CK — threat group profiles
curl "https://attack.mitre.org/groups/" | grep target_sector

# AlienVault OTX — open threat exchange
curl -H "X-OTX-API-KEY: YOUR_KEY" \
  "https://otx.alienvault.com/api/v1/search/pulses?q=target.com&limit=10"

# VirusTotal — check IPs/domains for malware associations
curl -H "x-apikey: YOUR_VT_KEY" \
  "https://www.virustotal.com/api/v3/domains/target.com"

# Shodan — historical data
shodan host TARGET_IP
shodan domain target.com
```

---

## Intelligence Report Template

```markdown
## Threat Intelligence Summary — [Target]
## Date: [Date]

### Breach Exposure
- **Compromised accounts found:** [N] accounts from [N] breaches
- **Most recent breach:** [Name], [Date], [Data types leaked]
- **Stealer log infections:** [N] corporate machines compromised (Hudson Rock)
  - Most recent: [Date]
  - Credentials at risk: VPN, [Cloud provider], [Internal tool]

### Dark Web Mentions
- [Count] forum mentions in past 12 months
- Ransomware listing: [Yes/No — Group name if yes]
- Source code / internal docs for sale: [Yes/No]

### Recommended Actions (Pre-Engagement)
1. Force password reset for all accounts in breach databases
2. Invalidate all active sessions (stolen session cookies)
3. Enable FIDO2 MFA on all externally-accessible services
4. Review VPN access logs for anomalous logins

### Active Threat Actors
Groups known to target [industry]: [Group names from MITRE ATT&CK]
Recent TTPs: [Relevant techniques]
```
