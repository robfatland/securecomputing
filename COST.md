\newpage

<!-- SOURCE: COST.md -->

# Cost Management

This document tracks AWS service costs for the project infrastructure. The system is built in **DESTROY mode** (development/synthetic) — no Object Lock, no MFA Delete, 7-day KMS deletion, no multi-AZ redundancy. This enables clean tear-down and minimizes spend.

> **Funding:** AWS credits (not dollars). Avoid AWS Marketplace services that charge real money.

---

## Build Mode: Cheap + DESTROY-Compatible

| Design Choice | Cheap Option Used | Monthly Cost | Risk Accepted |
|---------------|-------------------|--------------|---------------|
| RDS PostgreSQL | Single-AZ, db.t3.micro (2 vCPU, 1GB) | ~$13 | No failover — instance crash requires restore from backup (~5 min) |
| DocumentDB | Single instance, db.t3.medium | ~$55 | No replica — same single-point-of-failure risk |
| EFS | One-Zone storage class | ~$8 (50GB) | Data in one AZ — AZ failure = temporary unavailability |
| S3 | Standard, single region, no replication | ~$12 (500GB) | Region failure = unavailable (extremely rare for us-west-2) |
| NAT Gateway | Single AZ | ~$33 | AZ failure = no GitHub access until recovered |
| VPC Endpoints | Minimal set (see below) | ~$50–80 | Fewer endpoints = some services accessed via NAT instead of private path |
| EC2 IDE (×6) | t3.medium (2 vCPU, 4GB) | ~$30 each = $180 | Less RAM than m5.xlarge — adequate for 11K patients; may need resize for imaging data |
| SageMaker | ml.t3.medium, idle-stop 60min | ~$15 each | Smaller instance; auto-stops aggressively |
| Monitoring | GuardDuty + Config; skip Macie initially | ~$10 | No automated PHI discovery — rely on policy/training |
| Multi-AZ | None (all single-AZ) | Saves ~$100/mo | Any AZ failure = downtime until recovery |

---

## Estimated Monthly Spend

### Active Use (business hours, Mon–Fri 6AM–6PM)

| Category | Services | Monthly |
|----------|----------|---------|
| Compute (EC2 ×6) | t3.medium, ~160 hrs/mo each | $180 |
| Database (RDS) | db.t3.micro, ~160 hrs/mo | $13 |
| Database (DocumentDB) | db.t3.medium, ~160 hrs/mo | $55 |
| Storage (S3) | ~500 GB | $12 |
| Storage (EFS) | ~50 GB One-Zone | $8 |
| Networking (NAT) | ~160 hrs/mo | $33 |
| Networking (VPC Endpoints ×8) | 24/7 | $58 |
| Monitoring (GuardDuty + Config) | Always on | $10 |
| KMS (4 keys) | Always on | $4 |
| SageMaker (×6) | ~80 hrs/mo each (idle-stop) | $24 |
| CloudTrail | Data events | $5 |
| **Total active** | | **~$400/month** |

### Hibernated (all compute stopped)

| Category | Monthly |
|----------|---------|
| Storage (S3 + EFS + EBS) | ~$30 |
| VPC Endpoints (if left running) | $58 |
| KMS + monitoring | $14 |
| **Total hibernated** | **~$100/month** |
| **If VPC Endpoints deleted** | **~$45/month** |

### DESTROY (blank slate)

| Monthly | $0 (after 7-day KMS wait) |
|---------|---------------------------|

---

## VPC Endpoints: Cost vs. Need

Each Interface Endpoint costs $0.01/hr = $7.30/month. We minimize by deploying only essential ones:

| Endpoint | Needed? | Justification |
|----------|---------|---------------|
| S3 (Gateway) | [x] Yes | Free (Gateway type) — always include |
| SSM | [x] Yes | Researcher access to EC2 (no SSH alternative) |
| KMS | [x] Yes | All encryption/decryption operations |
| CloudWatch Logs | [x] Yes | Log shipping from all compute |
| ECR (api + dkr) | [x] Yes (2 endpoints) | Container image pulls |
| STS | [x] Yes | IAM role assumption |
| Bedrock | [x] Yes | AI inference |
| Comprehend Medical | [x] Yes | Gatekeeper PHI detection |
| **Subtotal (8 Interface)** | | **$58/month** |
| SageMaker (api + runtime) | [!] Defer | Add when SageMaker is actively used |
| SNS | [!] Defer | Alerts can route via CloudWatch → Lambda → NAT |
| Secrets Manager | [!] Defer | Low-frequency access; can use NAT |
| ECS | [!] Defer | Add when container pipelines are running |
| Lambda | [!] Defer | Lambda in VPC can use NAT for invocations |

**Strategy:** Start with 8 essential endpoints. Add others as needed. Each addition is $7.30/month.

---

## DocumentDB: Cost Options and Risk

| Option | Config | Monthly | Risk |
|--------|--------|---------|------|
| **Cheapest (our choice)** | Single db.t3.medium instance | $55 | No failover; instance failure = downtime + manual recovery |
| **Moderate** | 1 primary + 1 replica | $110 | Automatic failover; read scaling |
| **Production** | 1 primary + 2 replicas, Multi-AZ | $165+ | Full HA; survives AZ failure |

**Why we accept the risk:** This is synthetic data. If DocumentDB goes down, we wait for it to recover or redeploy from CDK. No real patients are affected. A production system with real PHI would use the moderate or production option.

**Alternative considered:** Skip DocumentDB entirely and use only RDS PostgreSQL (store patient documents as JSONB columns). Saves $55/month. Tradeoff: less natural document queries, but PostgreSQL JSONB is quite capable. This is a viable simplification if budget is tight.

---

## RDS: Cost Options and Risk

| Option | Config | Monthly | Risk |
|--------|--------|---------|------|
| **Cheapest (our choice)** | db.t3.micro, Single-AZ | $13 | 1GB RAM (tight for complex queries); no failover |
| **Moderate** | db.t3.small, Single-AZ | $26 | 2GB RAM; still no failover |
| **Production** | db.t3.medium+, Multi-AZ | $55+ | Automatic failover; adequate RAM |

**Why db.t3.micro works for now:** OMOP tables are ~600MB on disk. With 1GB RAM, simple queries work fine. Complex joins across millions of rows may spill to disk (slower but functional). If performance is an issue, resize to t3.small ($13/mo more).

---

## Cost Reduction Tactics

| Tactic | Savings | Implemented |
|--------|---------|-------------|
| Auto-stop EC2 (6PM daily) | ~60% of compute cost | [x] In design |
| SageMaker idle-stop (60 min) | ~50% of SageMaker cost | [x] In design |
| Stop RDS/DocumentDB when not in use | ~60% of database cost | Manual (hibernate procedure) |
| Delete VPC Endpoints during hibernation | $58/month | Manual (recreate via CDK on wake) |
| Use t3.medium instead of m5.xlarge | $110/mo per instance saved | [x] In design |
| Skip Macie initially | $50–100/month | [x] In design |
| Skip DocumentDB entirely (use PostgreSQL JSONB) | $55/month | [!] Consider if budget tight |
| One-Zone EFS | ~47% of EFS cost | [x] In design |

---

## What NOT to Use (costs real dollars, not credits)

- AWS Marketplace AMIs or containers (may charge separately)
- AWS Support plans (Business/Enterprise tier)
- Route 53 hosted zones ($0.50/month each — minor but unnecessary for this project)
- AWS Transfer Family (SFTP endpoint — $0.30/hr = $219/month; use AWS CLI upload instead)

---

## Production Upgrade Path

When transitioning from synthetic to real PHI, upgrade these:

| Component | Development | Production | Additional Cost |
|-----------|-------------|-----------|-----------------|
| RDS | Single-AZ, t3.micro | Multi-AZ, t3.medium+ | +$40/month |
| DocumentDB | Single instance | Primary + replica | +$55/month |
| EFS | One-Zone | Standard (multi-AZ) | +$7/month (50GB) |
| S3 | Single region | Cross-region replication | +$12/month |
| Monitoring | Skip Macie | Add Macie | +$50–100/month |
| Object Lock | Disabled | Enabled on audit bucket | $0 (feature, not service) |
| MFA Delete | Disabled | Enabled on audit bucket | $0 |
| KMS deletion | 7-day wait | 30-day wait | $0 |
| **Total upgrade** | | | **+$165–215/month** |
