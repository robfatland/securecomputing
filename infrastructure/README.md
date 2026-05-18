# Infrastructure: CDK Deployment

AWS CDK (Python) infrastructure-as-code for the Synthetic PHI Research Environment.

> **Mode:** DESTROY (development). All resources have `RemovalPolicy.DESTROY`. No Object Lock, no MFA Delete, 7-day KMS deletion. See `COST.md` for spend details.

---

## Prerequisites

```bash
# Node.js + CDK CLI
sudo apt install nodejs npm
npm install -g aws-cdk
cdk --version  # Should show 2.x

# Python dependencies
cd ~/securecomputing/infrastructure
pip install -r requirements.txt
```

### AWS Credentials Configuration

CDK needs credentials for the target AWS account. Two approaches depending on your institutional setup:

#### Option A: IAM User (access keys — simpler, less secure)

Used when: you have an IAM User with administrator privileges in the target account (common for sub-accounts with credit-based funding, no SSO infrastructure).

**Setup `~/.aws/credentials`:**

```ini
[default]
aws_access_key_id = YOUR_KEY_FOR_TARGET_ACCOUNT
aws_secret_access_key = YOUR_SECRET_FOR_TARGET_ACCOUNT

[securecomputing]
aws_access_key_id = YOUR_KEY_FOR_TARGET_ACCOUNT
aws_secret_access_key = YOUR_SECRET_FOR_TARGET_ACCOUNT

[other-account-name]
aws_access_key_id = SOME_OTHER_KEY
aws_secret_access_key = SOME_OTHER_SECRET
```

**Setup `~/.aws/config`:**

```ini
[default]
region = us-west-2
output = json
```

**Notes:**
- `[default]` and `[securecomputing]` are identical — `default` is what runs without `--profile`; `securecomputing` is a named reference for explicitness
- Rename any pre-existing `[default]` to a descriptive name so you don't accidentally deploy to the wrong account
- Keep other account profiles for reference but never set them as default while working on this project

**Verify:**
```bash
aws sts get-caller-identity
# Should show the correct account ID for the securecomputing project
```

#### Option B: SSO (federated identity — more secure, institutional)

Used when: your institution (UW IT) provides AWS access via SSO/SAML federation. This is the production-recommended approach.

**Setup:**
```bash
aws configure sso --profile securecomputing
# Prompts for:
#   SSO start URL: https://your-institution.awsapps.com/start
#   SSO region: us-west-2
#   Account ID: (your target account)
#   Role: AdministratorAccess (or equivalent)
```

**Login (required periodically — sessions expire):**
```bash
aws sso login --profile securecomputing
export AWS_PROFILE=securecomputing
aws sts get-caller-identity
```

**For CDK with SSO:**
```bash
export AWS_PROFILE=securecomputing
cdk bootstrap aws://ACCOUNT_ID/us-west-2
cdk deploy --all
```

Or pass explicitly:
```bash
cdk deploy --all --profile securecomputing
```

> 📋 **TEACHING NOTE:** IAM User access keys are long-lived credentials — if leaked, they grant persistent access until rotated. SSO tokens are short-lived (expire in hours). For a real PHI production system, SSO is strongly preferred. For a synthetic/development system with credit-based funding and no institutional SSO, IAM User keys are acceptable with the understanding that they should be rotated periodically and never committed to git.

### Verify Credentials

```bash
aws sts get-caller-identity
```

Expected output:
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

The Account number must match your target account. If it shows a different account, your `[default]` profile is pointing to the wrong credentials.

---

## Commands

| Command | What it does | Cost |
|---------|-------------|------|
| `cdk synth` | Validate code + generate CloudFormation templates (no AWS calls) | $0 |
| `cdk diff` | Show what would change vs. current deployed state | $0 |
| `cdk deploy --all` | Deploy all stacks to AWS | Starts billing (~$400/mo active) |
| `cdk destroy --all` | Delete all resources (Blank Slate) | Stops billing (after 7-day KMS wait) |

### Validate (no deployment)

```bash
cd ~/securecomputing/infrastructure
cdk synth
```

Produces CloudFormation JSON in `cdk.out/`. If this succeeds, the code is valid.

### Deploy

```bash
cd ~/securecomputing/infrastructure
cdk deploy --all --require-approval broadening
```

`--require-approval broadening` prompts before creating IAM or security group changes.

First deploy requires bootstrapping (one-time per account/region):
```bash
cdk bootstrap aws://ACCOUNT_ID/us-west-2
```

### Destroy (Blank Slate)

```bash
cd ~/securecomputing/infrastructure
cdk destroy --all
```

Deletes all CloudFormation stacks and their resources. S3 buckets are auto-emptied (DESTROY mode). KMS keys enter 7-day pending deletion.

### Destroy WITHOUT CDK or AI Assistance

If CDK is unavailable, the AI coding assistant is unavailable, or the Python environment is broken — the infrastructure can still be destroyed using only the AWS CLI or Console. This is the "break glass" procedure:

**Option A: AWS CLI only (no CDK, no Python, no AI)**

```bash
# List all project stacks
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `SecureComputing`)].StackName' \
  --output text

# Empty S3 buckets first (CloudFormation can't delete non-empty buckets)
# Find bucket names:
aws s3 ls | grep securecomputing

# Empty each bucket:
aws s3 rm s3://BUCKET_NAME --recursive

# Delete stacks in reverse dependency order:
aws cloudformation delete-stack --stack-name SecureComputing-Monitoring
aws cloudformation wait stack-delete-complete --stack-name SecureComputing-Monitoring

aws cloudformation delete-stack --stack-name SecureComputing-Compute
aws cloudformation wait stack-delete-complete --stack-name SecureComputing-Compute

aws cloudformation delete-stack --stack-name SecureComputing-Storage
aws cloudformation wait stack-delete-complete --stack-name SecureComputing-Storage

aws cloudformation delete-stack --stack-name SecureComputing-KMS
aws cloudformation wait stack-delete-complete --stack-name SecureComputing-KMS

aws cloudformation delete-stack --stack-name SecureComputing-VPC
aws cloudformation wait stack-delete-complete --stack-name SecureComputing-VPC

# Verify nothing remains:
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `SecureComputing`)]'
# Should return empty

# Optionally remove CDK bootstrap:
aws cloudformation delete-stack --stack-name CDKToolkit
```

**Option B: AWS Console (no CLI, no code, no AI)**

1. Log in to https://console.aws.amazon.com
2. Navigate to S3 → empty all project buckets
3. Navigate to CloudFormation → delete stacks in order: Monitoring, Compute, Storage, KMS, VPC
4. Wait for each to reach DELETE_COMPLETE before deleting the next
5. Verify no SecureComputing stacks remain

**KMS keys:** After stack deletion, KMS keys enter "pending deletion" for 7 days. No action needed — they auto-delete. Verify at: KMS Console → Customer managed keys → should show "Pending deletion."

> 📋 **TEACHING NOTE:** The ability to destroy infrastructure without the tools that created it is a resilience requirement. If your CDK environment is corrupted, your laptop is lost, or the AI assistant is discontinued — you can still clean up using only a browser and the AWS Console. CloudFormation tracks everything CDK created; you just delete the stacks.

### Check what's deployed

```bash
cdk list          # Show all stacks
cdk diff          # Show pending changes
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

---

## Stack Architecture

```
app.py
 ├── SecureComputing-VPC        (networking, endpoints, flow logs)
 ├── SecureComputing-KMS        (4 encryption keys)
 ├── SecureComputing-Storage    (S3, RDS PostgreSQL, EFS)
 ├── SecureComputing-Compute    (6 EC2 IDE instances, auto-start/stop)
 └── SecureComputing-Monitoring (CloudTrail, GuardDuty, Config rules)
```

Dependencies flow top-to-bottom: Storage needs VPC + KMS; Compute needs VPC + KMS; Monitoring needs VPC + KMS + Storage.

---

## Estimated Monthly Spend

| State | Cost |
|-------|------|
| Active (business hours) | ~$400/month |
| Hibernated (compute stopped) | ~$100/month |
| Destroyed (blank slate) | $0 |

See `COST.md` for detailed breakdown.

---

## Operational Scripts (future)

| Script | Purpose |
|--------|---------|
| `ops/hibernate.sh` | Stop all compute; optionally delete VPC endpoints |
| `ops/wake.sh` | Restart compute; recreate endpoints if deleted |
| `ops/destroy.sh` | `cdk destroy --all` + verification script |
| `ops/verify_blank_slate.py` | Enumerate remaining resources; alert on orphans |
