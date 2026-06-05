# /ctf-methodology — CTF Strategy & Competition Reasoning

> **Skill type:** CTF / Competition  
> **Source:** EvanThomasLuke/Awesome-AI-Hacking-Agents (CTF section), NYU D-CIPHER, EnIGMA (ICML 2025)  
> **Chains into:** All exploitation skills (based on challenge category)

---

## CTF Category Decision Tree

```
Received a challenge → What category?

┌─ Web ─────────────────────────────────────────────────┐
│ → Check: URL parameters, cookies, headers, source code │
│ → Test: SQLi, XSS, SSRF, SSTI, path traversal, LFI    │
│ → Look for: Flag in DB, /flag, /etc/passwd, env vars   │
└────────────────────────────────────────────────────────┘

┌─ Crypto ──────────────────────────────────────────────┐
│ → Identify: Cipher type (XOR, RSA, AES, custom)       │
│ → Weaknesses: Short key, low exponent (RSA), ECB mode │
│ → Tools: SageMath, CrypTool, John (hash cracking)     │
└────────────────────────────────────────────────────────┘

┌─ Pwn / Binary ────────────────────────────────────────┐
│ → Run: checksec, strings, file command                 │
│ → Debug: GDB with pwndbg/peda                         │
│ → Check: Buffer overflow, format string, heap exploit  │
│ → Tools: pwntools, ROPgadget                          │
└────────────────────────────────────────────────────────┘

┌─ Reverse Engineering ─────────────────────────────────┐
│ → Static: Ghidra, radare2, strings                    │
│ → Dynamic: GDB, ltrace, strace, Frida                 │
│ → Patterns: Anti-debug, obfuscation, license checks   │
└────────────────────────────────────────────────────────┘

┌─ Forensics ───────────────────────────────────────────┐
│ → File type: binwalk, exiftool, file command          │
│ → Steganography: steghide, zsteg, stegseek, strings   │
│ → Memory: volatility3                                  │
│ → PCAP: wireshark, tshark                            │
└────────────────────────────────────────────────────────┘

┌─ OSINT ───────────────────────────────────────────────┐
│ → Username: sherlock, holehe, maigret                  │
│ → Image: reverse image search, exiftool              │
│ → Domain: whois, dig, crt.sh                         │
│ → Metadata: exiftool, strings                        │
└────────────────────────────────────────────────────────┘

┌─ Misc / Jail ─────────────────────────────────────────┐
│ → Python jail: restricted_shell bypass               │
│ → Sandbox escape: check imports, __builtins__        │
│ → Common bypasses: exec, eval, __import__, os.system │
└────────────────────────────────────────────────────────┘
```

---

## CTF Reasoning Framework (AI Agent Edition)

### Structured Approach (from D-CIPHER / EnIGMA)

```
Step 1: OBSERVE
  - What do we know about the challenge?
  - What files/inputs are provided?
  - What is the expected output format (flag format)?
  - Are there any obvious clues in the challenge description?

Step 2: HYPOTHESIZE  
  - What category does this belong to?
  - What vulnerability class is likely?
  - What does the flag format tell us?

Step 3: ENUMERATE
  - Run initial recon (file, strings, netcat, curl)
  - Enumerate all accessible resources
  - Don't assume — verify

Step 4: EXPLOIT
  - Start with the simplest possible exploit
  - If blocked → try next hypothesis
  - Document what you tried and why it failed

Step 5: REFLECT
  - Am I stuck in a loop? (same failed approach 3+ times)
  - What haven't I tried yet?
  - What would a different angle look like?
  - Should I search for public writeups for similar challenges?
```

---

## Common CTF Patterns

### Web CTF Quick Wins
```bash
# Check source code first!
curl -s https://ctf-challenge.com | grep -i "flag\|CTF\|comment\|hidden"
view-source:https://ctf-challenge.com

# robots.txt and sitemap
curl https://ctf-challenge.com/robots.txt
curl https://ctf-challenge.com/sitemap.xml

# Check cookies
curl -v https://ctf-challenge.com 2>&1 | grep -i "set-cookie"

# JWT decode
echo "eyJh..." | cut -d. -f2 | base64 -d 2>/dev/null | python3 -m json.tool
```

### Crypto Quick Wins
```python
# XOR with single byte key
ciphertext = bytes.fromhex("1a2b3c...")
for key in range(256):
    plaintext = bytes(b ^ key for b in ciphertext)
    if b"flag{" in plaintext or b"CTF{" in plaintext:
        print(f"Key: {key}, Plain: {plaintext}")

# RSA small e (e=3) with no padding
# If e=3 and m^3 < n: m = cube_root(c)
from gmpy2 import iroot
m, exact = iroot(c, 3)
flag = m.to_bytes(100, 'big').decode('ascii', errors='ignore')
```

### Binary Quick Start
```bash
# Initial analysis
file binary
strings binary | grep -E "flag|CTF|pass|secret"
checksec --file=binary

# Dynamic run
strace ./binary 2>&1 | head -30
ltrace ./binary 2>&1 | head -30
./binary <<< "AAAA"  # Test with simple input

# GDB quick check
gdb ./binary
run
bt  # backtrace on crash
info registers
```

---

## Steganography Toolkit

```bash
# Image steganography
strings image.png | grep -E "flag|CTF"
exiftool image.png
binwalk -e image.png  # Extract embedded files
steghide extract -sf image.jpg  # Extract with empty password
stegseek image.jpg /usr/share/wordlists/rockyou.txt  # Crack password

# PNG specific
pngcheck image.png
zsteg image.png  # LSB steganography

# Audio steganography
sox audio.wav -t wav output.wav  # Analyze
audacity audio.wav  # Visual analysis
steghide extract -sf audio.wav

# File analysis
file unknown_file
xxd unknown_file | head -20  # Hex dump - check magic bytes
```

---

## Flag Format Recognition

```
Standard: CTF{...}, FLAG{...}, flag{...}
Hex: 0x666c61677b...
Base64: ZmxhZ3s...
ROT13: PGS{...}  → flag{}
Binary: 01100110 01101100 01100001 01100111  → "flag"
```
