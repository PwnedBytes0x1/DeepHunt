# Context Management for Long Agentic Tasks

## The Context Window Problem

In long pentest engagements or multi-step agentic tasks:
- Tool outputs accumulate → context fills
- Early important context gets dropped
- Model loses track of the original goal
- Repeated re-reading of same info wastes budget

**Solution:** Treat context like RAM. Keep hot data accessible, flush cold data to files.

---

## Memory Tiers

### Tier 1: Active Context (in prompt)
- Current task + immediate next step
- Last 2-3 tool outputs (summarized)
- Current working hypothesis
- Critical blocking info

**Max size:** ~500-800 tokens  
**Rule:** If it's not relevant to the next 2-3 actions, move it out

### Tier 2: Session File (quick reference)
- All confirmed findings (compact format)
- Tested endpoints + results
- Credentials/tokens found
- Failed attack paths (avoid re-trying)

**Location:** `notes.md` in working directory  
**Access pattern:** Read at session start, append only during session

### Tier 3: Archive (deep storage)
- Raw tool outputs
- Full HTTP responses
- Completed phase outputs

**Location:** `raw/` directory  
**Access pattern:** Only when you need to re-verify a specific finding

---

## Sliding Window Strategy

### For Long Tasks (100+ steps)

Keep a rolling "last N" window in active context:
```
ACTIVE WINDOW (always in context):
- Task objective (1 sentence)
- Current phase
- Last 3 actions + outcomes
- Next planned action

TRIMMED OUT after window slides:
- Actions from > 3 steps ago (summarized in notes.md)
- Tool outputs already processed
- Dead-end paths already tried
```

### Trigger: When to Compact
```
Compact context when ANY of these are true:
□ You've made 10+ tool calls since last compact
□ Context is > 60% of limit
□ You're about to start a new phase
□ You're about to spawn a sub-task
```

### How to Compact
```bash
# Pattern: Summarize what you know → flush details → start fresh summary

# Step 1: Write summary to file
cat > notes.md << 'EOF'
## Session Summary - [timestamp]

### Target
target.com (IP: 1.2.3.4)

### Confirmed Findings
1. [HIGH] SQLi: /api/search?q= (time-based, MySQL)
2. [MED] IDOR: /api/user/{id} (increment id 1-100 works)

### Enumeration Completed
- Ports: 22, 80, 443, 8080
- Paths: /api, /admin(403), /upload, /login
- Subs: api.target.com, admin.target.com

### Tested & Negative
- /login: no SQLi, no brute force (rate limited)  
- /api/products: no injection, read-only

### Current State
Testing: /upload endpoint for unrestricted file upload
Next: If upload works → web shell via PHP upload
EOF

# Step 2: Drop detailed tool outputs from context, keep only notes.md reference
```

---

## Summarization Patterns

### Tool Output → 1-Liner
```
Full nmap output (50 lines) → "ports: 22,80,443 | nginx 1.18 + PHP 7.4"
Full gobuster output (200 lines) → "paths: /api, /admin(403), /upload, /login"
SQLmap output (100 lines) → "SQLi confirmed: time-based, DB=production, tables=users,orders"
Nikto output (80 lines) → "findings: X-Frame missing, Outdated Apache 2.4.49"
```

### Phase Summary Template
```markdown
## Phase: Web Enumeration — COMPLETE
Duration: ~15 min | Tools: nmap, ffuf, nikto, whatweb
Result:
- Tech: nginx + PHP 7.4 + MySQL + Laravel
- Attack surface: /login, /api/search, /api/user/{id}, /upload
- Quick wins: Apache version exposed, debug mode on, X-Debug header accepted
Transition to: Exploitation phase
```

---

## Sub-Agent Context Passing

When delegating to a sub-agent, pass ONLY what they need:

```
❌ BAD: Pass entire conversation history
✅ GOOD: Pass compact task brief

Sub-agent brief template:
---
TARGET: target.com
YOUR JOB: Test /api/user/{id} for IDOR. Try IDs 1-200.
CONTEXT: Authenticated as user_id=50. Session: [token]
SUCCESS: Find any IDs that return other users' data
OUTPUT FORMAT: id|name|email per line, or "NONE FOUND"
STOP CONDITION: After finding 3 valid IDs, or after testing all 1-200
---
```

### What Sub-Agents Should Return
```
❌ Full tool logs and verbose output
✅ Compact findings + confirmed PoCs only

Return format:
RESULT: [SUCCESS/FAIL/PARTIAL]
FINDINGS:
  - id=1: admin@target.com (admin role)
  - id=3: john@target.com (user role)
TESTED: ids 1-50 (stopped after 3 findings as instructed)
NEXT: Run ids 51-200 OR proceed to exploitation
```

---

## Checkpoint Pattern

For very long tasks, write checkpoints to disk:

```bash
# Checkpoint file structure
cat > checkpoint.json << 'EOF'
{
  "target": "target.com",
  "phase": "exploitation",
  "completed_phases": ["recon", "scanning", "enumeration"],
  "findings": [
    {"severity": "high", "type": "sqli", "location": "/api/search?q=", "verified": true},
    {"severity": "medium", "type": "idor", "location": "/api/user/{id}", "verified": true}
  ],
  "credentials": [
    {"user": "admin@target.com", "pass": "Admin123!", "source": "brute_force"}
  ],
  "next_action": "exploit_sqli_for_db_dump",
  "blocked": ["/admin → 403 not bypassed"]
}
EOF
```

**When to write checkpoint:**
- Before starting a long operation (so you can resume if interrupted)
- After completing each major phase
- Before making irreversible changes

---

## Context Anti-Patterns

```
❌ Reading the same file multiple times (cache the result)
❌ Running the same reconnaissance tool twice
❌ Keeping full HTTP responses in context (keep only relevant lines)
❌ Re-explaining task context you already know
❌ Verbose "thinking out loud" (reasoning tokens) when you know the answer
❌ Keeping failed tool outputs in context (summarize: "X didn't work, reason Y")
❌ Building up state in model's "memory" instead of files (session restarts lose it)
```

## Context Budget Quick Rules

```
Rule 1: Tool output → extract 3-5 relevant lines → discard rest
Rule 2: After 10 steps → write compact summary → trim context
Rule 3: New phase → save old phase summary → start fresh context
Rule 4: Sub-task → brief it tightly → get compact results back
Rule 5: "I know this already" → don't re-read it → reference the filename
```
