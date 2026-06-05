# Agent Token Budget Management

## Core Principle

Every token spent is a tradeoff. High token usage ≠ high quality work. The goal is **maximum signal per token** — actionable output, not verbose reasoning.

---

## Task Scoping — Define Before You Start

### The 3-Question Pre-flight
Before starting any task, answer these three:
1. **What is the minimum viable output?** (What MUST be produced)
2. **What can be skipped if time/tokens run short?** (Nice-to-have vs must-have)
3. **What's the stopping condition?** (When is "done" actually done?)

### Scope Compression Patterns
```
❌ Vague: "Research the target and find vulnerabilities"
✅ Scoped: "Find SQLi in /api/search endpoint. Stop after first confirmed PoC."

❌ Vague: "Enumerate the network"  
✅ Scoped: "Nmap top-1000 ports on 10.0.0.0/24. Report only open ports. Skip OS detection."

❌ Vague: "Check all OWASP Top 10"
✅ Scoped: "Test A01-A03 on login and search endpoints. One PoC per finding max."
```

---

## Context Pruning — Keep Working Memory Lean

### What Stays in Context
- **Active task definition** (what you're doing RIGHT NOW)
- **Last 2-3 tool results** (only the relevant parts)
- **Confirmed findings** (brief, not verbose)
- **Blocking questions** (if any)

### What Gets Dropped
- Full HTML/source dumps when you only needed one field
- Repeated tool output headers/footers
- Successful intermediate steps that produced no useful data
- Duplicate search results from multiple queries

### Pruning Commands (for agents)
```python
# Pattern: Extract only what matters from large tool output
# Bad: Store entire 50KB nmap output
# Good: Store only the 10 lines of open ports

# Bad: Store entire HTTP response (headers + body)
# Good: Store only status code + relevant header/body snippet

# Aggressive pruning rule: 
# If you haven't referenced a piece of context in 3+ steps, discard it
```

---

## Selective Tool Use — Pick Right Tool First Time

### Decision Tree: Which Tool to Use

```
Need to test a single URL?
  → curl (1 command, instant result)
  
Need to spider/crawl a site?
  → gospider or hakrawler (faster than manual browsing)
  
Need to find subdomains?
  → subfinder first (passive, fast), then amass (slower, more thorough) ONLY if subfinder insufficient

Need to test SQLi?
  → Manual payload first → confirm vuln → THEN use sqlmap
  (Don't run sqlmap on every parameter by default)
  
Need to read a file?
  → grep/cat with specific line ranges, NOT cat entire file

Need to check many endpoints?
  → ffuf with tight filters (--hc for expected codes), NOT manual curl loop
```

### Tool Efficiency Tier
```
Tier 1 (Low token cost, use freely):
  curl, grep, head/tail, wc, ls, find -name

Tier 2 (Medium cost, use purposefully):  
  nmap, ffuf, nikto, sqlmap --level 1

Tier 3 (High cost, use sparingly):
  Full spider runs, aggressive nmap (-A), sqlmap --level 5, full Burp scans
  → Only use Tier 3 after Tier 1/2 confirms the attack surface is real
```

---

## When to Stop — Stopping Conditions

### Hard Stops
- **Found confirmed PoC** → Stop testing that attack vector, document and move on
- **Tested 3 variations of same attack with no result** → Move on
- **Tool returning only errors/timeouts for 5+ runs** → Blocked, note and move on
- **Same data appearing in 3+ search results** → No new info, stop searching

### Soft Stops
- **Target is rate-limiting you** → Slow down or pivot
- **Context is > 70% of limit** → Summarize and compact before continuing
- **In a loop** → You've run the same type of command 3 times, step back and rethink

### The 3-Strike Rule
```
Strike 1: Try attack vector → no result → vary payload
Strike 2: Try different angle → no result → vary approach  
Strike 3: Try one more variant → no result → STOP, DOCUMENT, MOVE ON

Don't spend 15 tokens on an attack that Strike 1 suggested won't work.
```

---

## Memory Tiers — What to Keep Where

```
Hot (in context):
  - Current task + immediate sub-task
  - Last confirmed finding
  - Current working hypothesis

Warm (in notes/file):
  - All confirmed findings so far
  - Enumerated endpoints
  - Tested/failed attack paths (avoid re-testing)

Cold (done, no longer needed):
  - Raw tool output already processed
  - Dead-end paths
  - Setup steps completed
```

### Compact Progress Tracking
```markdown
## Current Progress (compact format)
Target: target.com
Phase: Exploitation (A03 - SQLi)
Confirmed: 
  - /api/search?q= → SQLi (time-based, 5s delay confirmed)
  - /admin → 403 (not bypassed)
Testing next: /api/user?id= → IDOR
Blocked: /api/payments → rate limited
```

---

## Budget Allocation by Task Type

| Task | Recommended Token Budget | Key Constraint |
|------|-------------------------|----------------|
| Recon (passive) | Low | Stop at first actionable finding |
| Recon (active) | Medium | Top-1000 ports, not full range by default |
| Vuln testing (one endpoint) | Low-Medium | Max 3 payload variations per type |
| Exploitation (confirmed vuln) | Medium | Get PoC, don't perfect it |
| Full pentest engagement | High | Budget per phase, not per tool |
| Report writing | Medium | Template reuse, fill specifics only |
