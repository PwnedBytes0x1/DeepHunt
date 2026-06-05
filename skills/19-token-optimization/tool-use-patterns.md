# Tool Use Patterns for Efficiency

## The Core Pattern: Funnel, Don't Spray

Inefficient agents run every tool on every target. Efficient agents funnel:
```
Hypothesis → Lightest tool that can confirm/deny → Escalate only if needed
```

---

## Batching: Parallel Over Sequential

### What Can Run in Parallel
```bash
# BAD: Sequential (3x slower)
subfinder -d target.com -silent > subs.txt
httpx -l subs.txt -silent > live.txt
nuclei -l live.txt -t exposures/ > nuclei.txt

# GOOD: Parallel where possible
subfinder -d target.com -silent | httpx -silent | nuclei -t exposures/ -silent &
nmap -sV --top-ports 1000 target.com &
theHarvester -d target.com -b google &
wait
```

### Parallel Fuzzing
```bash
# Test multiple parameters simultaneously
ffuf -u "https://target.com/api?FUZZ=test" -w params.txt &  # Param names
ffuf -u "https://target.com/FUZZ" -w paths.txt &            # Paths
wait
```

---

## Right Tool for Right Job

### Reconnaissance
| Need | Right Tool | Wrong Tool (slow/overkill) |
|------|-----------|--------------------------|
| Quick port scan | `nmap --top-1000` | `masscan` for single target |
| Subdomain enum | `subfinder` (passive first) | `amass -brute` (slow) |
| Tech detection | `whatweb` or curl headers | Full Wappalyzer scan |
| Dir brute | `ffuf` | `dirb` (slower) |
| Screenshot | `gowitness` | Manual browser |

### Web Testing
| Need | Right Tool | Wrong Tool |
|------|-----------|-----------|
| Quick SQLi test | Manual payload first, then `sqlmap --level 1` | `sqlmap --level 5 --risk 3` from the start |
| XSS testing | `dalfox` | Manual in all fields |
| SSRF testing | `curl` with internal IPs | Custom scanner |
| Header checks | `curl -I` | Full spider |
| LFI testing | Manual `../../etc/passwd` | Automated scanner |

### Post-Exploitation
| Need | Right Tool | Wrong Tool |
|------|-----------|-----------|
| Privilege escalation hints | `linpeas.sh --quiet` | Full manual enum |
| File search | `find / -name "*.conf" 2>/dev/null` | Manual directory walking |
| Password extraction | `grep -r "password\|passwd" /etc/ /var/www/` | Full filesystem dump |

---

## Avoid Redundancy

### Don't Re-Enumerate What You Know
```bash
# BAD: Re-running the same thing
nmap target.com          # Run 1
nmap target.com -sV      # Run 2 (could have combined)
nmap target.com -sV -sC  # Run 3 (could have combined)

# GOOD: One comprehensive run
nmap -sV -sC --top-1000 -oA nmap_results target.com
```

### Don't Confirm the Already-Confirmed
```bash
# BAD: Testing the same vuln 3 ways when 1 confirmed it
# After time-based SQLi confirms:
# - Re-test with error-based SQLi
# - Re-test with UNION-based
# - Re-test with boolean-based
# → STOP at confirmation, move to extraction

# GOOD: Confirmed = documented, move on
# Use sqlmap for extraction AFTER confirming manually
```

### Cache Results
```bash
# Save tool output, don't re-run
nmap ... -oA results/nmap_target  # XML + greppable + normal output saved
# Reference file instead of re-running:
grep "open" results/nmap_target.gnmap
```

---

## Tool Invocation Patterns

### The Verification Ladder
```
Level 1: Is it potentially vulnerable? (10 seconds, manual)
  curl https://target.com/api?id=1'
  → If 500 error or SQL error message → YES, escalate

Level 2: Can I confirm the vulnerability? (2 minutes)
  ' AND SLEEP(5)--
  → 5-second response delay → CONFIRMED

Level 3: Can I exploit it? (5 minutes)
  sqlmap -u "https://target.com/api?id=1" --batch --dbs
  → Gets database list → EXPLOITED

DON'T run Level 3 on everything — confirm Level 1 and 2 first.
```

### Error-Driven Tool Selection
```bash
# If manual test returns SQL error → sqlmap
# If manual test returns timeout → time-based payloads
# If manual test returns reflection → XSS tools
# If manual test returns file path → LFI tools
# No response variation → move on, not injectable
```

---

## Command Efficiency Patterns

### Grep-First
```bash
# Don't parse everything — grep for what you need
cat large_output.txt | grep -E "CRITICAL|HIGH|password|secret|token"
# vs reading entire 500-line file
```

### Early Exit Flags
```bash
# Stop after first success
hydra -f ...           # -f = exit after first found
gobuster dir -q ...    # -q = quiet, less output
ffuf ... -of compact   # compact output format
nmap --open ...        # only show open ports
```

### Output Limiting
```bash
# Only top N results
subfinder -d target.com | head -20
# Only unique values
cat endpoints.txt | sort -u
# Only specific fields
cat nmap.xml | python3 -c "import sys; [print(l) for l in sys.stdin if 'open' in l]"
```

---

## When NOT to Use a Tool

```
❌ Don't run sqlmap on endpoints that don't take user input
❌ Don't run nikto on non-HTTP ports
❌ Don't run amass if subfinder gave you 50+ subdomains already
❌ Don't run gobuster if robots.txt already listed all interesting paths
❌ Don't screenshot 200 subdomains when you're only testing 3 of them
❌ Don't run linpeas if you already have root
```

## Tool Budget per Engagement Phase

```
Recon:        4-6 tool calls total (passive→active funnel)
Scanning:     2-4 tool calls (nmap + 1-2 web scanners)  
Testing:      2-3 calls per endpoint (manual→confirm→exploit)
Exploitation: 1-3 calls per vuln (exploit→verify→next)
Post-exploit: 2-4 calls (enum→escalate→persist)
```
