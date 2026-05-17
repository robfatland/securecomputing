# Risk Assessment

> ⚠️ **TEMPLATE:** This risk assessment is a demonstrator example. You are responsible for modifying this to be accurate to your program. Threat scenarios, likelihood scores, and mitigations must be reviewed against your actual institutional context, threat landscape, and risk tolerance.

## Document Status

| Field | Value |
|-------|-------|
| **Document ID** | RA-001 |
| **Version** | 1.0 (Draft) |
| **Date** | [Date of acceptance] |
| **Status** | Draft — pending sponsor acceptance |
| **Gate** | G2 — this document, when accepted, satisfies Gate G2 |
| **Review cycle** | Quarterly reassessment; immediate review after any incident |

---

## 1. Purpose

This risk assessment identifies threats to the PHI research environment, scores their likelihood and impact, defines mitigations, and documents residual risk accepted by the sponsor (PI). It satisfies the HIPAA Security Rule requirement for risk analysis (45 CFR § 164.308(a)(1)(ii)(A)) and aligns with NIST SP 800-30 methodology.

---

## 2. Scope

### Assets in Scope

| Asset | Type | PHI Content | Location |
|-------|------|-------------|----------|
| S3 landing zone | Data store | Raw PHI (full identifiers, 10K patients) | AWS us-west-2 |
| S3 validated/processed zones | Data store | Raw + derived PHI | AWS us-west-2 |
| RDS database | Data store | Structured PHI (patient records) | AWS us-west-2 (private subnet) |
| EFS shared filesystem | Data store | Working files, intermediate results (may contain PHI) | AWS us-west-2 (private subnet) |
| EC2 IDE hosts | Compute | PHI in memory during processing | AWS us-west-2 (private subnet) |
| EC2/SageMaker notebook hosts | Compute | PHI in memory and notebook output | AWS us-west-2 (private subnet) |
| Bedrock LLM service | AI service | Prompts may contain PHI (gatekeeper mitigates) | AWS us-west-2 |
| Comprehend Medical | AI service | Scans text that may contain PHI | AWS us-west-2 |
| CloudTrail / CloudWatch logs | Audit | Metadata about PHI access (who, what, when) | AWS us-west-2 (audit account) |
| KMS encryption keys | Security | Protects all PHI at rest | AWS us-west-2 |
| AWS Wickr | Communication | Team messages may reference PHI | AWS (encrypted) |
| GitHub repository | Code store | **No PHI** — code only | GitHub cloud |
| ECR container images | Code store | **No PHI** — code artifacts only | AWS us-west-2 |
| Researcher laptops | Endpoint | **No PHI** — thin client only | Physical (various locations) |

### Data Flows

```
UW Clinical DB → (TLS) → S3 Landing Zone → Validation → S3 Validated
                                                              │
                                                              ▼
                                              RDS (structured) + S3 (files)
                                                              │
                                                              ▼
                                              EC2/SageMaker (processing)
                                                              │
                                              ┌───────────────┼───────────────┐
                                              ▼               ▼               ▼
                                          EFS (working)   Bedrock (AI)    Wickr (comms)
                                                          via Gatekeeper
```

---

## 3. Threat Actors

| ID | Actor | Motivation | Capability | Likelihood of Attempt |
|----|-------|-----------|------------|----------------------|
| **TA-1** | Curious insider | Access data beyond approved scope (intellectual curiosity, career advancement) | Has valid credentials; understands system; knows where data lives | Medium |
| **TA-2** | Careless insider | No malicious intent; accidental disclosure through workflow habits | Has valid credentials; uses AI tools; copies/pastes routinely | High |
| **TA-3** | Departing member | Retains access after leaving team; may access data post-departure | Has (or had) valid credentials; knows system | Medium |
| **TA-4** | External attacker | Data theft, ransomware, credential harvesting | Varies: phishing (high capability), exploitation (medium), brute force (low against MFA) | Low-Medium |
| **TA-5** | Misconfigured system | No human actor — configuration drift exposes data | N/A — systemic risk | Medium |

---

## 4. Threat Scenarios and Risk Scoring

### Scoring Methodology (NIST SP 800-30 aligned)

**Likelihood:** How probable is this scenario given the project's controls?
| Score | Level | Meaning |
|-------|-------|---------|
| 1 | Very Low | Unlikely given current controls |
| 2 | Low | Possible but improbable |
| 3 | Medium | Reasonably possible |
| 4 | High | Likely without additional controls |
| 5 | Very High | Expected to occur |

**Impact:** What is the consequence if this scenario occurs?
| Score | Level | Meaning |
|-------|-------|---------|
| 1 | Negligible | No PHI exposed; minor operational disruption |
| 2 | Low | Limited PHI exposure (<10 records); contained quickly |
| 3 | Medium | Moderate PHI exposure (10-500 records); breach notification likely |
| 4 | High | Significant PHI exposure (500+ records); regulatory action likely |
| 5 | Very High | Mass exposure (all 10K records); criminal penalties possible |

**Risk Score:** Likelihood × Impact

| Risk Level | Score Range | Response |
|------------|-------------|----------|
| **Low** | 1–4 | Accept; monitor |
| **Medium** | 5–9 | Mitigate; document acceptance of residual risk |
| **High** | 10–15 | Mitigate before proceeding; escalate to sponsor |
| **Critical** | 16–25 | Must mitigate before system authorization; cannot accept |

---

### TA-1: Curious Insider

| ID | Scenario | Likelihood | Impact | Risk | Mitigation | Residual |
|----|----------|-----------|--------|------|------------|----------|
| TA1-1 | Student queries patient records outside their approved study cohort | 3 | 3 | 9 (Med) | Database views enforce cohort boundaries; row-level security; audit logs detect out-of-scope queries | 2×3=6 (Med) |
| TA1-2 | Researcher accesses another researcher's working files on EFS | 2 | 2 | 4 (Low) | POSIX permissions on EFS; IAM authorization; access logged | 1×2=2 (Low) |
| TA1-3 | Team member attempts to access audit logs to cover tracks | 2 | 4 | 8 (Med) | Audit logs in separate account; no researcher access to audit bucket; immutable (versioning + MFA delete) | 1×4=4 (Low) |
| TA1-4 | Researcher uses Bedrock to summarize records beyond their scope | 2 | 3 | 6 (Med) | Bedrock access scoped by IAM role; queries logged; gatekeeper logs all prompts; database views prevent data retrieval beyond scope regardless of prompt | 1×3=3 (Low) |

---

### TA-2: Careless Insider

| ID | Scenario | Likelihood | Impact | Risk | Mitigation | Residual |
|----|----------|-----------|--------|------|------------|----------|
| TA2-1 | Researcher pastes error message containing MRN into external AI (ChatGPT) | 4 | 3 | 12 (High) | Network blocks external AI from research environment; gatekeeper scans outbound prompts; training emphasizes this scenario | 2×3=6 (Med) |
| TA2-2 | Researcher commits notebook with PHI output cells to GitHub | 3 | 3 | 9 (Med) | nbstripout pre-commit hook; .gitignore excludes data files; pre-commit PHI regex scanning; PR review required | 1×3=3 (Low) |
| TA2-3 | Researcher discusses patient details in personal email/Slack | 3 | 3 | 9 (Med) | Policy: Wickr only for PHI-related discussion; training; no email/Slack access from research environment | 2×3=6 (Med) |
| TA2-4 | Code developed on localhost contains hardcoded PHI (test values from memory) | 2 | 2 | 4 (Low) | Pre-commit hooks scan for PHI patterns; code review on PR; training on synthetic test data practices | 1×2=2 (Low) |
| TA2-5 | Researcher downloads PHI to laptop (circumventing no-download policy) | 2 | 4 | 8 (Med) | No download capability in IDE/notebook (clipboard disabled for data, no SCP/SFTP out); network egress blocked; DLP monitoring | 1×4=4 (Low) |
| TA2-6 | AI prompt contains PHI that gatekeeper fails to detect (novel format) | 3 | 2 | 6 (Med) | Bedrock is BAA-covered (contained even if PHI passes through); gatekeeper supplemented with regex for known formats; periodic review of missed detections | 2×2=4 (Low) |

---

### TA-3: Departing Member

| ID | Scenario | Likelihood | Impact | Risk | Mitigation | Residual |
|----|----------|-----------|--------|------|------------|----------|
| TA3-1 | Student graduates; credentials remain active; accesses data months later | 3 | 3 | 9 (Med) | Monthly access review (Phase 5); offboarding checklist; PI notified of all departures; IT revokes within 24 hours of notification | 1×3=3 (Low) |
| TA3-2 | Departing member copies data before leaving | 2 | 4 | 8 (Med) | No download capability; network egress blocked; access audit detects bulk queries; exit interview includes HIPAA reminder | 1×4=4 (Low) |
| TA3-3 | Former member's SSO session token still valid after departure | 2 | 3 | 6 (Med) | Session timeout enforced (max 8 hours); SSO deprovisioning propagates to AWS within 1 hour; MFA required for new sessions | 1×3=3 (Low) |

---

### TA-4: External Attacker

| ID | Scenario | Likelihood | Impact | Risk | Mitigation | Residual |
|----|----------|-----------|--------|------|------------|----------|
| TA4-1 | Phishing attack compromises researcher's UW SSO credentials | 3 | 4 | 12 (High) | MFA required (phishing-resistant: hardware key or push notification); session monitoring; GuardDuty anomaly detection; IP-based access restrictions | 2×4=8 (Med) |
| TA4-2 | Compromised laptop used to access research environment | 2 | 3 | 6 (Med) | MFA required; session timeout; no PHI cached on laptop; GuardDuty detects anomalous access patterns; VPC restricts lateral movement | 1×3=3 (Low) |
| TA4-3 | Exploitation of unpatched vulnerability in EC2 instance | 2 | 4 | 8 (Med) | Automated patching (SSM Patch Manager); security groups restrict inbound; no public IPs; vulnerability scanning; container immutability | 1×4=4 (Low) |
| TA4-4 | Ransomware encrypts research data | 2 | 4 | 8 (Med) | S3 versioning; RDS automated backups; EFS backups; KMS keys in separate account; no direct internet access from compute | 1×3=3 (Low) |
| TA4-5 | Credential stuffing against AWS console | 1 | 4 | 4 (Low) | SSO federation (no direct AWS console passwords); MFA; account lockout; CloudTrail detects failed attempts | 1×4=4 (Low) |

---

### TA-5: Misconfigured System

| ID | Scenario | Likelihood | Impact | Risk | Mitigation | Residual |
|----|----------|-----------|--------|------|------------|----------|
| TA5-1 | S3 bucket policy accidentally allows public access | 2 | 5 | 10 (High) | S3 Block Public Access (account-level); AWS Config rule detects public buckets; Macie alerts on exposed data; IaC prevents manual changes | 1×5=5 (Med) |
| TA5-2 | Security group opened too broadly (0.0.0.0/0 inbound) | 2 | 4 | 8 (Med) | AWS Config rule detects open security groups; no public subnets for PHI resources; Security Hub flags; IaC enforces baseline | 1×4=4 (Low) |
| TA5-3 | KMS key policy grants overly broad decrypt permissions | 2 | 4 | 8 (Med) | Key policies reviewed at creation; AWS Config monitors key policy changes; least-privilege enforced in IaC | 1×4=4 (Low) |
| TA5-4 | CloudTrail logging accidentally disabled | 2 | 3 | 6 (Med) | AWS Config rule requires CloudTrail enabled; Organization-level trail (cannot be disabled by member account); alert on trail status change | 1×3=3 (Low) |
| TA5-5 | IAM role creep — permissions accumulate beyond minimum necessary | 3 | 3 | 9 (Med) | IAM Access Analyzer; quarterly permission review; IaC defines roles (drift detected); least-privilege starting point | 2×3=6 (Med) |
| TA5-6 | Gatekeeper service fails silently — prompts bypass PHI scanning | 2 | 3 | 6 (Med) | Health check monitoring on gatekeeper; fail-closed design (if gatekeeper is down, Bedrock access is blocked, not bypassed); alert on gatekeeper errors | 1×3=3 (Low) |

---

## 5. Risk Summary

### By Risk Level (pre-mitigation)

| Level | Count | Scenarios |
|-------|-------|-----------|
| **High (10-15)** | 3 | TA2-1 (paste to external AI), TA4-1 (phishing), TA5-1 (public S3) |
| **Medium (5-9)** | 14 | Various — see detail above |
| **Low (1-4)** | 4 | TA1-2, TA2-4, TA4-5, TA2-5 (pre-mitigation low) |

### By Risk Level (post-mitigation / residual)

| Level | Count | Scenarios |
|-------|-------|-----------|
| **High** | 0 | None — all high risks mitigated to medium or below |
| **Medium (5-9)** | 5 | TA1-1, TA2-1, TA2-3, TA4-1, TA5-1 |
| **Low (1-4)** | 16 | All others |

### Top Residual Risks (requiring ongoing attention)

| ID | Scenario | Residual Score | Ongoing Control |
|----|----------|---------------|-----------------|
| TA2-1 | Paste PHI to external AI | 6 | Network blocks + gatekeeper + training; monitor for bypass attempts |
| TA4-1 | Phishing → credential compromise | 8 | MFA + anomaly detection; phishing awareness training; consider hardware keys |
| TA2-3 | PHI in unauthorized channels | 6 | Policy + training; Wickr as approved alternative; periodic reminder |
| TA1-1 | Curious insider queries beyond scope | 6 | Database views + audit; monthly access review catches patterns |
| TA5-1 | Public S3 bucket | 5 | Account-level block + Config rule + Macie; IaC prevents drift |

---

## 6. Risk Acceptance

> 📋 **GENERIC:** The following acceptance statement is template language. Your version must be signed by the actual sponsor with specific reference to the residual risks they are accepting.

I, Dr. D.R. Smith, as project sponsor and designated Security Officer, have reviewed this risk assessment. I accept the residual risks documented above, acknowledging that:

1. All identified high risks have been mitigated to medium or below
2. Residual medium risks are managed through ongoing controls (monitoring, training, periodic review)
3. This risk assessment will be reassessed quarterly and immediately after any security incident
4. New threats or changes to the environment will trigger a reassessment

**Signature:** _________________ **Date:** _________

---

## 7. Review Schedule

| Trigger | Action |
|---------|--------|
| Quarterly (scheduled) | Review all risk scores; update for new threats; verify mitigations still effective |
| After any security incident | Immediate reassessment of affected scenarios; update scores and mitigations |
| Team change (onboarding/offboarding) | Review TA-3 scenarios; verify access controls |
| Infrastructure change | Review TA-5 scenarios; verify new resources are covered |
| New AI service or tool introduced | Review TA-2 scenarios; update AI-specific risks |
