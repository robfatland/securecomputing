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

> [i] **TEACHING NOTE:** IAM User access keys are long-lived credentials — if leaked, they grant persistent access until rotated. SSO tokens are short-lived (expire in hours). For a real PHI production system, SSO is strongly preferred. For a synthetic/development system with credit-based funding and no institutional SSO, IAM User keys are acceptable with the understanding that they should be rotated periodically and never committed to git.

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

> [i] **TEACHING NOTE:** The ability to destroy infrastructure without the tools that created it is a resilience requirement. If your CDK environment is corrupted, your laptop is lost, or the AI assistant is discontinued — you can still clean up using only a browser and the AWS Console. CloudFormation tracks everything CDK created; you just delete the stacks.

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

---

## Full Build Procedure (tested May 2026)

This is the complete sequence from blank AWS account to working system with data uploaded. Follow in order.

### 1. Prerequisites

```bash
# CDK CLI
sudo apt install nodejs npm
npm install -g aws-cdk

# Python dependencies
cd ~/securecomputing/infrastructure
pip install -r requirements.txt

# AWS credentials pointing to correct account (see credential setup above)
aws sts get-caller-identity
# Must show the target account ID
```

### 2. Bootstrap CDK (one-time per account)

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
cdk bootstrap aws://$ACCOUNT_ID/us-west-2
```

### 3. Deploy all stacks

```bash
cd ~/securecomputing/infrastructure
cdk deploy --all --require-approval broadening
```

Prompts for approval on security changes (answer `y`). Takes ~10 minutes total. All 5 stacks must show [x].

### 4. Verify deployment

```bash
# Find the data bucket name
aws s3 ls | grep securecomputing-storage
# Note the bucket name (auto-generated, e.g., securecomputing-storage-databuckete3889a50-xxxxx)

# Find instance IDs
aws ec2 describe-instances \
  --filters "Name=tag:project,Values=securecomputing" "Name=instance-state-name,Values=running" \
  --query 'Reservations[].Instances[].[InstanceId,Tags[?Key==`researcher`].Value|[0]]' \
  --output table
```

### 5. Verify EC2 connectivity

```bash
# Install SSM plugin (one-time)
curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
sudo dpkg -i session-manager-plugin.deb
rm session-manager-plugin.deb

# Connect to an instance
aws ssm start-session --target INSTANCE_ID

# Inside EC2 — verify network controls:
curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://www.google.com
# Should show "000" (blocked)

curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://github.com
# Should show "200" or "301" (allowed)

exit
```

### 6. Upload synthetic data

Requires data to have been generated first (see `securecomputing-datagen/BUILD.md`).

```bash
# Set bucket name (from step 4)
BUCKET=$(aws s3 ls | grep securecomputing-storage | awk '{print $3}')
echo "Uploading to: $BUCKET"

# Upload all datasets (~896 MB, takes a few minutes)
aws s3 cp ~/securecomputing-data/pd0/ s3://$BUCKET/landing/pd0/ --recursive
aws s3 cp ~/securecomputing-data/pd1/ s3://$BUCKET/landing/pd1/ --recursive
aws s3 cp ~/securecomputing-data/pd2/ s3://$BUCKET/landing/pd2/ --recursive
aws s3 cp ~/securecomputing-data/pd3/ s3://$BUCKET/landing/pd3/ --recursive
aws s3 cp ~/securecomputing-data/manifest.json s3://$BUCKET/landing/manifest.json

# Verify
aws s3 ls s3://$BUCKET/landing/ --summarize --recursive | tail -3
```

### 7. Verify data accessible from EC2

```bash
aws ssm start-session --target INSTANCE_ID

# Inside EC2:
export AWS_DEFAULT_REGION=us-west-2
aws s3 ls s3://BUCKET_NAME/landing/
# Should list pd0/, pd1/, pd2/, pd3/, manifest.json

exit
```

### 8. System is operational

At this point:
- [x] Infrastructure deployed (VPC, KMS, S3, RDS, EFS, EC2, monitoring)
- [x] Network controls verified (GitHub allowed, general internet blocked)
- [x] Data uploaded and accessible from research compute
- [x] Auto-start/stop scheduled (6AM–6PM Pacific, Mon–Fri)
- [x] CloudTrail logging all API calls
- [x] GuardDuty monitoring for threats

---

## Destroy and Rebuild Test

To verify the Blank Slate Rule:

```bash
# Destroy everything
cd ~/securecomputing/infrastructure
cdk destroy --all
# Answer 'y' to each stack

# Verify blank slate
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName, `SecureComputing`)]' \
  --output table
# Should return empty

aws s3 ls | grep securecomputing
# Should return nothing

aws ec2 describe-instances \
  --filters "Name=tag:project,Values=securecomputing" \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' \
  --output table
# Should return empty (or all "terminated")

aws kms list-aliases \
  --query 'Aliases[?contains(AliasName, `securecomputing`)]' \
  --output table
# Should show "pending deletion" or return empty

# If all checks pass: blank slate confirmed.
# Rebuild from scratch: repeat steps 2–7 above.
# (Step 2 bootstrap can be skipped if CDKToolkit stack still exists)
```

> [x] **Blank slate verified May 18, 2026.** DESTROY completed with no errors; all verification checks returned empty. System can be rebuilt from documentation.

The rebuild should produce an identical working system. The only variable is the bucket name (auto-generated, different each deploy).

---

## Known Issues and Fixes Applied

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `cdk synth` fails: "must configure PUBLIC subnets for NAT" | CDK requires a public subnet to place NAT Gateway | Added minimal /28 public subnet |
| `cdk synth` fails: "oneZone availabilityZones undefined" | EFS One-Zone needs explicit AZ | Added `availability_zones=[vpc.availability_zones[0]]` |
| `cdk synth` fails: "encryption_key unexpected argument" | CDK API doesn't support `encryption_key` on `BlockDeviceVolume.ebs()` | Removed; use account default encryption |
| RDS deploy fails: "Cannot find version 16.4" | Specific minor version not available in us-west-2 | Changed to `VER_16` (latest 16.x) |
| Google reachable from EC2 (should be blocked) | Security group had `any_ipv4()` on port 443 (S3 fallback rule) | Removed; S3 uses prefix list rule instead |
| `aws s3 ls` hangs from EC2 | Security group blocked S3 Gateway Endpoint traffic | Added egress rule for S3 prefix list `pl-68a54001` |
| PostgreSQL version enum | `VER_16_4` not recognized | Use `VER_16` (CDK resolves to latest available) |

---

## Researcher Access: IDE and Notebooks

Researchers access their EC2 instances via SSM port forwarding — no public IP, no SSH keys, no inbound firewall rules. The browser on the researcher's laptop connects to `localhost` which tunnels through SSM to the EC2.

### VS Code Server (code-server)

**One-time setup on the EC2 (via SSM session):**

```bash
aws ssm start-session --target INSTANCE_ID

# Inside EC2:
curl -fsSL https://code-server.dev/install.sh | sh
# Start with a password (or use --auth none for development)
code-server --bind-addr 0.0.0.0:8080 --auth password
# Set password when prompted, then Ctrl+C (we'll run it as a service below)

# Run as background service:
sudo systemctl enable --now code-server@$USER
# Edit config to set port and auth:
mkdir -p ~/.config/code-server
cat > ~/.config/code-server/config.yaml << 'EOF'
bind-addr: 0.0.0.0:8080
auth: password
password: CHOOSE_A_PASSWORD
cert: false
EOF
sudo systemctl restart code-server@$USER
```

**To connect (from your laptop):**

```bash
# Terminal 1: start port forward
aws ssm start-session --target INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8080"],"localPortNumber":["8080"]}'

# Terminal 2 (or browser): open http://localhost:8080
# Enter the password you set above
```

You now have VS Code in your browser, running on the EC2, with access to all project data.

### Jupyter Lab

**One-time setup on the EC2:**

```bash
aws ssm start-session --target INSTANCE_ID

# Inside EC2:
pip install jupyterlab
jupyter lab --generate-config
# Set a password:
jupyter lab password

# Start Jupyter (background):
nohup jupyter lab --no-browser --port 8888 --ip 0.0.0.0 &
```

**To connect (from your laptop):**

```bash
# Terminal 1: start port forward
aws ssm start-session --target INSTANCE_ID \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8888"],"localPortNumber":["8888"]}'

# Browser: open http://localhost:8888
# Enter the password you set
```

### Access Pattern Summary

```
Researcher laptop
├── Terminal: aws ssm start-session (port forward)
└── Browser: http://localhost:8080 (VS Code) or :8888 (Jupyter)
        │
        ▼ (SSM tunnel — encrypted, authenticated, no public IP)
EC2 instance (private subnet)
├── code-server on port 8080
├── jupyter lab on port 8888
├── EFS mounted (shared files)
└── Access to S3, RDS, Bedrock via VPC endpoints
```

### Team Authentication (Production)

For the demonstrator (single user, IAM keys): `aws ssm start-session` uses your local access key.

For a real team (multiple researchers): Use IAM Identity Center (SSO):
1. Each researcher runs `aws sso login --profile securecomputing`
2. Gets temporary credentials (expire in 8 hours)
3. Runs `aws ssm start-session --target THEIR_INSTANCE_ID`
4. No long-lived keys on anyone's laptop

Each researcher connects only to their own instance (enforced by IAM policy scoping `ssm:StartSession` to instances tagged with their name).
