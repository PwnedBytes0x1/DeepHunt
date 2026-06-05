# Prompt Compression Techniques

## Why Compress

LLM context windows are finite. In long agentic tasks, prompt bloat kills performance:
- Tool results accumulate → context fills up → early context dropped
- More tokens in = more tokens processed = slower, more expensive
- Verbose prompts dilute signal → model focuses on wrong things

**Target:** 30-60% compression of instructions without losing actionability.

---

## Technique 1: Eliminate Filler Phrases

### Remove Zero-Value Phrases
```
❌ "Please make sure to carefully check all the parameters and ensure that..."
✅ "Check all parameters."

❌ "As a skilled penetration tester, you should approach this systematically..."
✅ (Delete entirely — role is implied)

❌ "It's important to note that you should always..."
✅ "Always..." or just state the instruction

❌ "Feel free to use any tools available to you..."
✅ (Delete — tools are available by definition)
```

### Common Filler → Delete List
- "Please note that..."
- "It's worth mentioning..."
- "As mentioned above..."
- "Keep in mind that..."
- "Make sure to..."
- "Don't forget to..."
- "You should be aware that..."
- "It's important to understand..."

---

## Technique 2: Structure Over Prose

### Prose vs Structured Comparison
```
❌ PROSE (verbose):
"First you should run nmap against the target to discover open ports, 
and then after you have the list of ports you should try to identify 
the services running on those ports, and if you find any web services 
you should then use nikto or a similar tool to scan for vulnerabilities."

✅ STRUCTURED (compressed):
1. nmap -top-ports 1000 TARGET
2. Identify web services from results
3. nikto -h TARGET on each web port
```

### Use Tables for Comparisons
```
❌ PROSE: "If you find SQLi, use sqlmap. If you find XSS, use XSStrike. 
If you find SSRF, test manually with curl."

✅ TABLE:
| Vuln | Tool |
|------|------|
| SQLi | sqlmap |
| XSS | XSStrike |
| SSRF | curl |
```

### Use Code Blocks for Commands
```
❌ "Run nmap with the dash A flag and the dash p dash (dash) flag set 
to 1 through 65535 against the target IP address"

✅ nmap -A -p- TARGET_IP
```

---

## Technique 3: Role Compression

### Pre-load Role Context Once
```
❌ REPEATED in every message:
"You are an expert penetration tester with 10 years of experience 
conducting security assessments..."

✅ SET ONCE in system prompt, never repeat:
"You are a pentest agent. Be terse. Prefer action over explanation."
```

### Implicit Role Assumptions
```
❌ "As a security researcher, you know that SQL injection occurs when..."
✅ (Delete the explanation — the model knows what SQLi is)

❌ "Remember that you have access to tools like nmap, sqlmap, and burp..."
✅ (Delete — tools are listed in context)
```

---

## Technique 4: Reference Compression

### Use Abbreviations and Anchors
```
Define once, reference short:
❌ "https://target.com/api/v1/user/profile endpoint"  (every time)
✅ Define: T=/api/v1/user/profile  → Use: "test T for IDOR"

❌ "administrator account with credentials admin:admin123"
✅ Define: ADMIN=admin:admin123

❌ "the previously discovered SQL injection vulnerable parameter 'id'"
✅ "SQLi@id param" (after first mention)
```

### Cross-Reference by Number
```
❌ "The vulnerability we found in the login endpoint earlier..."
✅ "Finding #1" (if findings are numbered in notes)
```

---

## Technique 5: Output Format Optimization

### Request Compressed Output
```
❌ Asking for: "Please provide a detailed explanation of what you found..."
✅ Asking for: "Output: STATUS | FINDING | NEXT_STEP only"

❌ "Explain your reasoning step by step..."
✅ "Show only final result + confidence level"

❌ Default tool output (often very verbose)
✅ Pipe through: | grep -E "open|FOUND|SUCCESS|ERROR" 
              or: | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=None))"
```

### Compact Finding Format
```
# Full verbose finding (expensive)
## SQL Injection in /api/search
The /api/search endpoint was found to be vulnerable to time-based blind 
SQL injection. During testing, the parameter 'q' was found to accept 
unsanitized input...

# Compact finding (cheap)
SQLI | /api/search?q= | time-based blind | 5s delay | sqlmap confirmed
```

---

## Technique 6: Context Window Management

### Summarize-and-Trim Pattern
When context grows large, replace old detailed content with summary:

```
# BEFORE (verbose, taking 2000 tokens):
[Full nmap output, 50 lines]
[Full gobuster output, 200 lines]  
[Full nikto output, 100 lines]

# AFTER summarize-and-trim (100 tokens):
ENUM COMPLETE:
- Ports: 22,80,443,8080,8443
- Paths found: /admin, /api, /uploads, /.git
- Nikto: X-Frame-Options missing, Outdated Apache 2.4.49
```

### The Rolling Summary Rule
After every 5 tool uses, compact your progress state:
```
PROGRESS SNAPSHOT:
Target: target.com
Done: recon, port scan, web enum
Findings: [compact list]
Current: testing A03 injection on /api/search
Next: IDOR testing on /api/user/{id}
Remaining: A05, A07 testing
```

---

## Quick Reference: Compression Ratios

| Content Type | Typical Size | Compressed | Method |
|---|---|---|------|
| Nmap full output | 500 tokens | 20 tokens | Extract open ports only |
| HTTP response | 300 tokens | 15 tokens | Status + key headers + body snippet |
| Search results | 400 tokens | 30 tokens | Title + 1-line summary per result |
| Task instructions | 800 tokens | 200 tokens | Bullets + code blocks, no prose |
| Progress state | 200 tokens | 40 tokens | Compact table format |
| Error messages | 150 tokens | 20 tokens | Error type + key line only |
