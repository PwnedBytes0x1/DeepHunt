# /attack-surface-mapping — Complete Attack Surface Analysis

> **Skill type:** Recon / Analysis  
> **Source:** ckduy/redamon recon pipeline, superhackers assessment-orchestrator  
> **Chains into:** All exploitation skills  
> **Chained from:** `/osint`, `/recon`

---

## Purpose

Build a complete, structured map of everything that can be attacked. This is the bridge between passive OSINT and active exploitation — a living document that gets updated as testing proceeds.

---

## The 7 Attack Surfaces

### Surface 1: External Web Applications
```
Discovery: httpx + content discovery
Key questions:
  - What endpoints exist? (crawl + fuzz)
  - What HTTP methods are accepted? (OPTIONS probing)
  - What auth mechanisms are in use? (JWT, session, OAuth, API key)
  - What frameworks/CMS are running? (version-specific CVEs)
  - Is there a WAF? (type determines bypass techniques)
  - Are there debug/test endpoints exposed?
```

### Surface 2: API Attack Surface
```
Discovery: spec hunting + kiterunner + JS bundle extraction
Key questions:
  - Is there an OpenAPI/Swagger spec? (auto-enumerate)
  - REST vs GraphQL vs gRPC vs SOAP?
  - What objects/resources are exposed? (BOLA candidates)
  - What authentication is required per endpoint?
  - Are there undocumented/shadow endpoints? (version drift)
  - What's the rate limiting posture?
```

### Surface 3: Network Services
```
Discovery: nmap full-port + UDP scan
Key questions:
  - What non-web services are exposed? (SSH, RDP, databases, SMB)
  - What versions? → CVE hunting
  - Are admin interfaces internet-exposed? (Kubernetes dashboard, Consul, Etcd)
  - Are cloud metadata endpoints reachable from the target?
  - What's the network segmentation like?
```

### Surface 4: Authentication & Authorization
```
Discovery: manual + automated auth testing
Key questions:
  - How does login work? → brute force / spray candidates
  - Password reset flow? → predictable tokens?
  - MFA implementation? → bypass candidates
  - Session management? → fixation, timeout, revocation
  - OAuth/OIDC flows? → state parameter, PKCE bypass
  - JWT → algorithm confusion, weak secret, missing expiry
```

### Surface 5: Cloud Infrastructure
```
Discovery: cloud metadata + provider-specific scanning
Key questions:
  - AWS/GCP/Azure? → IMDS endpoint accessible via SSRF?
  - Public S3/GCS buckets? → data exposure, write access
  - IAM roles? → overpermissioned? can escalate?
  - Serverless functions? → injectable inputs?
  - Container registry → pull images → secrets in layers?
```

### Surface 6: CI/CD & Supply Chain
```
Discovery: GitHub/GitLab org scan + pipeline config review
Key questions:
  - Are GitHub Actions/GitLab CI configs exposed?
  - Third-party dependencies → vulnerable versions?
  - Secrets in CI/CD environment variables?
  - Unpinned dependencies in package.json/requirements.txt?
  - Code signing? → can attacker inject code?
```

### Surface 7: AI/LLM Components
```
Discovery: endpoint probing + JS source analysis
Key questions:
  - Is there an LLM endpoint? → prompt injection surface
  - RAG implementation? → poisoning surface
  - Agent with tool calling? → tool abuse surface
  - System prompt exposed? → jailbreak + extraction
  - MCP server? → MCP Top 10 testing
```

---

## Attack Surface Map Template

```markdown
# Attack Surface Map — [Target Name]
## Generated: [date]

### External Entry Points
| URL/Host | Port | Service/Version | Auth | Notes |
|----------|------|-----------------|------|-------|
| https://app.example.com | 443 | nginx/1.18 + React | JWT | Main application |
| https://api.example.com | 443 | Express 4.18 | Bearer token | REST API |
| https://admin.example.com | 8080 | Apache 2.4.49 | Basic Auth | Admin panel |
| 1.2.3.4 | 22 | OpenSSH 7.9p1 | Key+password | SSH |

### API Endpoints
| Endpoint | Method | Auth Required | Notes |
|----------|--------|---------------|-------|
| /api/v1/users | GET | Yes (admin) | Returns all users |
| /api/v1/users/{id} | GET | Yes (any) | IDOR candidate |
| /api/v1/orders | POST | Yes | Business logic |
| /api/v2/internal | GET | No | 🚨 Unauthenticated! |

### Data Assets (High Value Targets)
| Asset | Location | Classification | Impact if Exposed |
|-------|----------|---------------|-------------------|
| User PII | PostgreSQL users table | PII/GDPR | Regulatory + reputational |
| Payment data | Stripe + local cache | PCI-DSS | Financial + legal |
| API keys | .env in source | Secret | Full system compromise |

### Tech Stack
| Layer | Technology | Version | Known CVEs |
|-------|-----------|---------|-----------|
| Frontend | React | 18.2 | None critical |
| Backend | Node.js | 18.12 | Check NVD |
| Framework | Express | 4.18 | CVE-2022-24999 |
| Database | PostgreSQL | 14.2 | None critical |
| Server | nginx | 1.18.0 | Check NVD |
| OS | Ubuntu | 20.04 | Check NVD |

### Third-Party Integrations
| Service | Purpose | Attack Vector |
|---------|---------|--------------|
| Stripe | Payments | Webhook forgery, amount manipulation |
| AWS S3 | File storage | Bucket misconfiguration, SSRF |
| Twilio | SMS/OTP | OTP bypass, IDOR on phone numbers |
| Google OAuth | Social login | OAuth state manipulation |

### Attack Surface Scoring
| Surface | Complexity | Expected Findings | Priority |
|---------|-----------|-------------------|----------|
| API endpoints | Medium | IDOR, auth bypass | P1 |
| Admin panel (Apache 2.4.49) | Low | CVE-2021-41773 | P1 |
| Auth flows | Medium | Password reset issues | P2 |
| Business logic | High | Price manipulation | P2 |
| Cloud infra | Medium | IAM misconfiguration | P3 |
```

---

## Automated Surface Mapper

```bash
#!/bin/bash
# Quick attack surface enumeration
TARGET=$1
OUTPUT_DIR="attack-surface-$TARGET-$(date +%Y%m%d)"
mkdir -p $OUTPUT_DIR

echo "[*] Running OSINT..."
subfinder -d $TARGET -o $OUTPUT_DIR/subdomains.txt
cat $OUTPUT_DIR/subdomains.txt | httpx -silent -o $OUTPUT_DIR/live-hosts.txt

echo "[*] Port scanning..."
nmap -sS -T4 -p- $(cat $OUTPUT_DIR/live-hosts.txt | tr '\n' ' ') \
  -oA $OUTPUT_DIR/nmap-results

echo "[*] Tech fingerprinting..."
whatweb -i $OUTPUT_DIR/live-hosts.txt --log-json=$OUTPUT_DIR/tech-stack.json

echo "[*] API discovery..."
for host in $(cat $OUTPUT_DIR/live-hosts.txt); do
  ffuf -u $host/FUZZ -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
    -mc 200,301,401 -o $OUTPUT_DIR/api-$(echo $host | md5sum | cut -c1-8).json
done

echo "[*] Vuln scanning..."
nuclei -l $OUTPUT_DIR/live-hosts.txt -s critical,high -o $OUTPUT_DIR/nuclei-critical.json

echo "[*] Attack surface map complete. Review: $OUTPUT_DIR/"
```
