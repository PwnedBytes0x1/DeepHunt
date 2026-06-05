# OWASP Top 10 2021 — Module Index

Field manuals for each OWASP Top 10 2021 category. Each file follows the same structure:
Overview → Detection → Indicators → Testing → Exploitation → Verification → Problems → Tools → Bypasses → Remediation → Real Examples

| File | Category | CVSS Range | Key Attack Types |
|------|----------|------------|-----------------|
| A01-broken-access-control.md | Broken Access Control | 4.3–9.8 | IDOR, path traversal, CORS, JWT privesc |
| A02-cryptographic-failures.md | Cryptographic Failures | 5.3–9.1 | Hash cracking, secret scanning, ECB |
| A03-injection.md | Injection | 5.0–10.0 | SQLi, SSTI, XXE, OS command, NoSQLi |
| A04-insecure-design.md | Insecure Design | 4.0–9.8 | Race conditions, business logic, reset flaws |
| A05-security-misconfiguration.md | Security Misconfiguration | 3.1–9.8 | Default creds, S3, actuator, Redis RCE |
| A06-vulnerable-components.md | Vulnerable Components | 3.1–10.0 | Log4Shell, Struts, supply chain, dep confusion |
| A07-authentication-failures.md | Auth Failures | 4.3–9.8 | JWT alg confusion, brute force, MFA bypass |
| A08-software-integrity-failures.md | Integrity Failures | 5.0–10.0 | Java deserialization, pickle, CI/CD injection |
| A09-logging-monitoring-failures.md | Logging Failures | N/A | Log injection, log poisoning, evasion |
| A10-ssrf.md | SSRF | 5.0–9.8 | Cloud metadata, Redis RCE, blind SSRF |

## Quick Attack Chains

### SSRF → RCE
```
A10 (SSRF) → cloud metadata → IAM creds → S3/EC2 access
A10 (SSRF) → internal Redis → gopher:// → cron RCE
```

### Auth Bypass → Data Access
```
A07 (JWT alg none) → admin endpoint → A01 (IDOR) → data dump
A05 (default creds) → admin panel → A03 (SQLi) → full DB
```

### Supply Chain → System Compromise
```
A06 (Log4Shell) → JNDI injection → LDAP → classload → RCE
A08 (deserialization) → gadget chain → OS command → shell
```
