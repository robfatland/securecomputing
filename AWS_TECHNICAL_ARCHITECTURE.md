# AWS Technical Architecture for HIPAA-Compliant Research Environment

## Overview

This document defines the AWS cloud infrastructure supporting the organizational model defined in ORGANIZATIONAL_STRUCTURE.md. The architecture implements technical safeguards required by the HIPAA Security Rule while supporting the research team's needs for secure PHI access and analysis.

---

## AWS Account Structure

### Multi-Account Strategy

```
Root Organization (AWS Organizations)
├── Prod Account (Primary - Production EMR & Research Data)
│   └── Single Department + Research Teams
├── Dev/Test Account (Development, Testing, Training)
├── Security/Logging Account (Centralized logging, audit trails)
└── Backup Account (Disaster recovery, retention)
```

**Rationale**:
- **Isolation**: Production research data isolated from testing
- **Least Privilege**: Separate security account for logging (prevents tampering)
- **Disaster Recovery**: Isolated backup account with restricted access
- **Billing**: Clear separation of costs by function

---

## Core AWS Services Selection

### Data Storage & Management

| Service | Purpose | PHI Access Level | Security Features |
|---------|---------|---|---|
| **RDS (PostgreSQL)** | Primary EMR/research database | Full | Encryption at rest, in transit, automated backups |
| **S3** | Research data, backups, archives | Full | Encryption, versioning, MFA Delete, access logging |
| **DynamoDB** | Audit logs, access metadata | Limited | Encryption, point-in-time recovery, access control |
| **Glacier** | Long-term data retention (7 years) | Archived | Encryption, immutable, restricted access |

### Compute & Access

| Service | Purpose | PHI Access Level |
|---------|---------|---|
| **EC2** | Research workstations (researcher access) | Project data |
| **Lambda** | Automated de-identification pipelines | Full (batch processing) |
| **VPC** | Network isolation and segmentation | Infrastructure |

### Security & Access Control

| Service | Purpose |
|---------|---------|
| **IAM (Identity & Access Management)** | Role-based access control, federated identity |
| **Secrets Manager** | Secure credential storage (DB passwords, API keys) |
| **KMS (Key Management Service)** | Encryption key management, key rotation |
| **VPC Security Groups & NACLs** | Network-level access control |
| **Systems Manager Session Manager** | Secure bastion/session logging (SSH replacement) |

### Monitoring, Logging & Compliance

| Service | Purpose |
|---------|---------|
| **CloudTrail** | API audit logging (who did what, when) |
| **CloudWatch** | Application and system metrics, logs |
| **VPC Flow Logs** | Network traffic logging |
| **AWS Config** | Configuration compliance monitoring |
| **GuardDuty** | Threat detection and intrusion prevention |
| **Macie** | Data discovery and protection (sensitive data scanning) |

### Networking

| Service | Purpose |
|---------|---------|
| **VPC** | Isolated network environment |
| **Private Subnets** | Non-internet-facing resources (databases, EMR systems) |
| **Public Subnets** | Internet-facing resources (bastions, VPN gateways) |
| **VPN** | Secure connectivity for researchers (external collaborator) |
| **PrivateLink** | Secure data sharing with external collaborator institution |

---

## Network Architecture

```
                         Internet
                            ↑
                     [NAT Gateway]
                            ↑
            ┌────────────────┼────────────────┐
            │                                  │
        [VPN] ← External Collaborator    [Public Subnets]
            │                                  │
            │    [Bastion Hosts]              │
            │    [Session Manager Endpoint]   │
            │                                  │
            └────────────────┬────────────────┘
                             │
              [Private Subnets - Application Tier]
                             │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
    [EC2 Research]    [Lambda Pipeline]    [EC2 Services]
    Workstations      De-identification
         │                    │                    │
         └────────────────────┼────────────────────┘
                             │
              [Private Subnets - Data Tier]
                             │
         ┌────────────────────┼────────────────────┐
         │                    │
    [RDS PostgreSQL]         [S3]
    (EMR & Research Data)    (Archives, Backups)
         │                    │
    [KMS Encryption]    [S3 Access Logging]
         │                    │
    [Automated            [Glacier Retention]
     Backups]
         │
    [Backup Account]
```

---

## IAM Role Structure (AWS Identities Mapping Organizational Roles)

### 1. Research Team IAM Roles

**PI IAM Role** (`research-team-pi`)
- Permissions:
  - RDS: Read/Write to approved research databases
  - S3: Read/Write to project-specific research bucket
  - EC2: Start/stop research instances (not terminate)
  - CloudWatch: Read research team logs
  - DynamoDB: Read access audit logs
- MFA Required: Yes
- Session Duration: 12 hours
- Assume Policy: Federated identity (University SSO) OR named AWS principals

**Co-I IAM Role** (`research-team-coi`)
- Similar to PI but:
  - Same data access (RDS, S3)
  - Cannot terminate instances
  - Cannot modify IAM permissions

**Developer IAM Role** (`research-team-developer`)
- Permissions:
  - RDS: Read-only to de-identified datasets (separate schema)
  - S3: Read-only to development/test data; Write to code repository
  - EC2: Start/stop development instances
  - Lambda: Deploy and test data pipeline code (read-only production)
- MFA Required: Yes
- Rationale: Minimum necessary; no access to full PHI in production

**Data Analyst IAM Role** (`research-team-analyst`)
- Permissions:
  - RDS: Read-only to approved research databases
  - S3: Read-only research data bucket
  - EC2: Start/stop analysis instances
  - Athena: Query research data in S3
  - QuickSight: Create analysis visualizations
- MFA Required: Yes

**External Collaborator IAM Role** (`external-collaborator`)
- Permissions:
  - De-identified data only (separate S3 bucket, restricted RDS views)
  - No direct EC2 access; data shared via automated push
  - Read-only to shared datasets
  - VPN-based access only
- MFA Required: Yes
- IP Restriction: External collaborator institution IP ranges only
- Assume Policy: Federated identity (external institution SSO) if available; otherwise MFA tokens

---

### 2. Departmental Administration IAM Roles

**Department Compliance Officer** (`dept-compliance-officer`)
- Permissions:
  - CloudTrail: Read access logs
  - CloudWatch: Read all logs from department
  - DynamoDB: Read audit tables (access history)
  - S3: Read-only to audit logs and compliance documentation
  - AWS Config: Read compliance status
- No direct data access (PHI)
- MFA Required: Yes
- Purpose: Monitor compliance, review access patterns

---

### 3. CISO / Security IAM Roles

**CISO / Security Officer** (`ciso-officer`)
- Permissions:
  - Full CloudTrail read access
  - Full CloudWatch read access
  - Full VPC Flow Logs access
  - AWS Config: Full read and remediation
  - GuardDuty: Full read and response
  - KMS: Key policy management
  - IAM: Read-only to all roles
  - All audit and security services
- MFA Required: Yes, with hardware token
- Purpose: Enterprise security oversight, incident response

**Security Team** (`security-team`)
- Permissions:
  - Same as CISO for read access
  - Can remediate GuardDuty findings
  - Can trigger security group changes (with approval)
  - VPC configuration read-only
- MFA Required: Yes
- Purpose: Operational security, incident response execution

---

### 4. Medical IT IAM Roles

**Medical IT Director** (`medical-it-director`)
- Permissions:
  - RDS: Full access (admin)
  - S3: Full access
  - EC2: Full access (administration)
  - DynamoDB: Full access
  - KMS: Full access (key management)
  - Backup: Full access
  - IAM: Modify research team roles (with approval workflow)
- MFA Required: Yes, with hardware token
- Session Duration: 8 hours
- Purpose: Data custodianship, infrastructure administration

**EMR Data Administrator** (`emr-data-admin`)
- Permissions:
  - RDS: Full access (schema design, data provisioning)
  - S3: Full access (data staging, de-identification output)
  - Lambda: Invoke de-identification pipelines
  - Secrets Manager: Read database credentials
  - DynamoDB: Write to audit logs
- MFA Required: Yes
- Session Duration: 8 hours
- Audit: All actions logged to CloudTrail

**Database Administrator (DBA)** (`database-admin`)
- Permissions:
  - RDS: Full access (backup, recovery, performance tuning)
  - S3: Full access (backup storage)
  - KMS: Encrypt/decrypt for backup operations
  - CloudWatch: Read performance metrics
  - AWS Backup: Full access
- MFA Required: Yes
- Session Duration: 8 hours
- IP Restriction: Allowed IPs only

**Network & Security Operations** (`network-security-ops`)
- Permissions:
  - VPC: Read/modify security groups and NACLs
  - CloudWatch: Read network metrics
  - VPC Flow Logs: Full read access
  - Systems Manager: Read patch compliance
- MFA Required: Yes
- Purpose: Network infrastructure management, incident response

---

### 5. IRB IAM Role

**IRB Coordinator** (`irb-coordinator`)
- Permissions:
  - S3: Read-only to protocol documentation and compliance artifacts
  - DynamoDB: Read-only to audit trail (which researchers accessed what)
  - CloudWatch: Read research team access patterns
- No direct PHI access
- MFA Required: Yes
- Purpose: Protocol compliance monitoring, audit trail review

---

## Access Control Patterns

### Pattern 1: Research Data Access

```
Researcher (with IAM role + MFA)
    ↓
[IAM Authentication & Authorization]
    ↓
[Resource-Based Policy Check (S3, RDS)]
    ↓
[Encryption Key Access via KMS]
    ↓
[Data Access Granted]
    ↓
[Access logged to CloudTrail + DynamoDB audit table]
    ↓
[Compliance review triggers if anomalies detected]
```

### Pattern 2: De-Identification Pipeline

```
Medical IT Admin initiates de-identification
    ↓
[IAM Role: emr-data-admin]
    ↓
[Lambda Function invoked]
    ↓
[Lambda reads full PHI from RDS (with KMS key)]
    ↓
[De-identification logic applied]
    ↓
[Output written to separate S3 bucket]
    ↓
[Output encrypted with KMS]
    ↓
[Audit log entry created]
    ↓
[Researchers granted access to de-identified data only]
```

### Pattern 3: External Data Sharing

```
External Collaborator requests data
    ↓
[Data request reviewed by PI + Compliance Officer]
    ↓
[De-identified dataset prepared]
    ↓
[Pushed to PrivateLink or secure S3 location]
    ↓
[External Collaborator pulls via VPN + IAM]
    ↓
[Audit trail created in central logging account]
    ↓
[Expiration date enforced on shared data]
```

---

## Encryption Strategy

### Encryption at Rest

**RDS (EMR & Research Databases)**
- AWS RDS Encryption (AES-256)
- Customer-managed KMS keys (not AWS-managed)
- Key rotation: Annual
- Key policy: Only Medical IT Director and DBA can decrypt
- Backups encrypted with same key

**S3 (Data Storage)**
- S3 Server-Side Encryption with Customer-Managed KMS keys
- Default bucket encryption enforced
- Bucket policy denies unencrypted uploads
- Access logging destination also encrypted

**EBS Volumes (EC2 Instances)**
- Encrypted with Customer-Managed KMS keys
- Snapshots encrypted with same key

**DynamoDB (Audit Logs)**
- Encryption at rest with AWS-managed keys (or customer-managed)
- Point-in-time recovery enabled

### Encryption in Transit

**Database Connections**
- RDS: SSL/TLS required (enforce_ssl parameter set to true)
- Connection string requires SSL certificate verification

**API Calls**
- All AWS API calls via HTTPS (enforced by AWS)
- AWS Signature Version 4 signing

**VPN (External Collaborator)**
- IPSec or OpenVPN with TLS
- AES-256 encryption
- Perfect forward secrecy enabled

**S3 Data Transfer**
- HTTPS enforced
- Bucket policy denies HTTP requests

---

## Logging & Audit Trail

### CloudTrail (API-Level Auditing)

**Enabled for**: All API calls across all services
**Logs**: Who, What, When, Where, Why for every action
**Storage**: S3 bucket in Logging Account (separate account, write-only)
**Retention**: 7 years (per HIPAA requirement)
**Encryption**: KMS-encrypted in S3
**Integrity**: CloudTrail Log File Validation enabled

**Example CloudTrail Events**:
- `researcher-pi` assumed role at 2026-04-30 09:15:22
- `emr-data-admin` executed Lambda function `de-identify-patient-data`
- `external-collaborator` accessed S3 object `de-identified-cohort-2026.csv`
- `medical-it-director` rotated RDS master password
- `database-admin` created RDS backup

### DynamoDB Audit Table (Application-Level Auditing)

**Purpose**: Track PHI access at application level
**Table Structure**:

```
{
  "AccessEventID": "uuid",
  "Timestamp": "2026-04-30T09:15:22Z",
  "IAMRole": "research-team-analyst",
  "Action": "SELECT * FROM patients WHERE study_id = ?",
  "ResourceAccessed": "arn:aws:rds:us-east-1:123456789:db:emr-research",
  "DatasetIdentifier": "cohort-anesthesia-2024",
  "RecordsAccessed": 150,
  "IPAddress": "192.168.1.100",
  "Result": "SUCCESS",
  "JustificationReference": "IRB-2026-001-Data-Request-42"
}
```

**Access**: 
- Researchers cannot read audit logs
- Compliance Officer can review their team's access
- CISO can review all logs
- System automatically writes all queries

### CloudWatch (Application & System Logging)

**Logs**:
- RDS slow query logs (queries taking >1 second)
- Lambda execution logs (de-identification pipeline)
- EC2 application logs (research software)
- VPN connection logs

**Retention**: 
- 90 days operational (searchable)
- Archived to S3/Glacier after 90 days

### VPC Flow Logs (Network-Level Auditing)

**Captures**: All network traffic in/out of subnets
**Fields**: Source IP, Destination IP, Port, Protocol, Bytes, Action (ACCEPT/REJECT)
**Purpose**: 
- Detect unauthorized network access attempts
- Track data exfiltration attempts
- Investigate security incidents
- Compliance evidence (network monitoring)

**Storage**: CloudWatch Logs and S3
**Retention**: 7 years

---

## Compliance Monitoring

### AWS Config Rules (Automated Compliance)

**Enabled Rules**:
- `encrypted-volumes`: Ensure all EBS volumes are encrypted
- `rds-encryption-enabled`: Ensure RDS encryption is on
- `s3-bucket-server-side-encryption-enabled`: Verify S3 encryption
- `iam-mfa-enabled-for-console-access`: Verify MFA on all users
- `restricted-ssh`: Ensure SSH port restricted to approved IPs
- `s3-bucket-versioning-enabled`: Verify S3 versioning for recovery
- `required-tags`: Verify all resources tagged appropriately
- `guardduty-enabled`: Verify GuardDuty is active

**Remediation**: 
- Auto-remediate minor violations (e.g., enable versioning)
- Manual review required for security group changes
- Alert CISO for policy violations

### GuardDuty (Threat Detection)

**Monitors For**:
- Unusual API calls
- Attempts to disable security controls
- Cryptocurrency mining activity
- Reconnaissance activity (port scanning, DNS queries)

**Response**: 
- Automatic alerts to Security Team
- Automatic suspension of suspicious IAM principals (optional)
- Manual investigation required

### Macie (Data Discovery & Protection)

**Scans**:
- S3 buckets for sensitive data patterns (names, addresses, medical record numbers)
- Identifies if de-identified data still contains PHI
- Finds unencrypted or unlogged sensitive data

**Findings**: 
- Alerts to CISO if PII detected in unexpected locations
- Can automatically remediate (move files, enable encryption)

---

## Access Request & Approval Workflow

### Research Data Access Request

1. **Requestor** (e.g., Data Analyst) submits request to PI
   - What data needed?
   - Why is it needed?
   - How long is access needed?
   - Security attestation (I understand HIPAA, will not share data)

2. **PI approves** (certifies minimum necessary)

3. **Compliance Officer reviews** (verifies IRB approval, approved study scope)

4. **Medical IT Admin provisions access**
   - Creates RDS database view (if applicable) with only needed data
   - Modifies IAM role to grant access
   - Documents approval chain
   - Logs to DynamoDB audit table

5. **Access granted** with:
   - Session time limit (usually 30-90 days)
   - IP restrictions (if applicable)
   - Data use restrictions (usage monitoring)
   - Automatic expiration

6. **Access review** (monthly by PI or Compliance Officer)
   - Did researcher access data as justified?
   - Any anomalies?
   - Renew or revoke access?

---

## Backup & Disaster Recovery

### RDS Backup Strategy

**Automated Daily Backups**:
- Time: 02:00 UTC daily
- Retention: 35 days
- Multi-AZ read replica: Maintained in separate AZ
- Storage location: Default (AWS-managed S3)

**Manual Backups**:
- Weekly full backup (Monday 02:00 UTC)
- Stored in Backup Account (separate AWS account)
- Replicated to second region for disaster recovery
- 7-year retention

**Recovery Testing**:
- Quarterly: Restore backup to test instance, verify data integrity
- Document: Restore time, data validation results

### S3 Backup Strategy

**Versioning**: 
- Enabled on all research data buckets
- Allows recovery of deleted or overwritten objects
- 7-year retention of all versions

**Cross-Region Replication**:
- Research data replicated to us-west-2 region
- Encrypted with same KMS key
- Replication failure alerts to Medical IT

**Glacier Archive**:
- Objects older than 1 year automatically transitioned to Glacier
- 7-year retention per HIPAA
- Encrypted, immutable (cannot delete for 7 years)

### RTO/RPO

**Recovery Time Objective (RTO)**: 4 hours
- RDS failure: Promote read replica or restore from backup (< 1 hour)
- S3 failure: Use cross-region replica (immediate)

**Recovery Point Objective (RPO)**: 1 hour
- Daily backup sufficient for most data loss scenarios
- Real-time replication for S3

---

## Security Best Practices Implementation

### 1. Principle of Least Privilege
- Each IAM role grants minimum necessary permissions
- No wildcard permissions (no `*` in IAM policies)
- Regular access reviews (quarterly)

### 2. Defense in Depth
- Network layer: Security groups, NACLs, VPC isolation
- Application layer: Database-level permissions, encryption
- Identity layer: MFA, federated SSO, session logging
- Monitoring layer: CloudTrail, GuardDuty, VPC Flow Logs

### 3. Immutability & Audit Trails
- CloudTrail logs immutable (stored in separate account)
- DynamoDB audit table cannot be deleted by researchers
- Versioning on S3 preserves history
- Database transaction logs retained

### 4. Separation of Duties
- Researchers cannot manage their own access (PI/Compliance Officer approves)
- Medical IT cannot approve access (researchers request)
- CISO monitors both researchers and IT administrators
- Audit logs stored in separate account (different credentials)

### 5. Encryption Always
- KMS-managed keys for all sensitive data
- No plaintext passwords (Secrets Manager)
- TLS for all in-transit data

---

## Disaster Scenarios & Response

### Scenario 1: Ransomware Attack on RDS

**Detection**: 
- GuardDuty alerts on suspicious encryption activity
- CloudWatch alerts on unusual Lambda invocations
- Database admin notices massive DELETE operations

**Response**:
1. Isolate affected instance (modify security group to deny all)
2. Notify CISO and incident response team
3. Restore from unaffected backup (prior to infection)
4. Conduct forensics (CloudTrail review, log analysis)
5. Implement remediation (patch vulnerability)

### Scenario 2: Insider Threat (Rogue Researcher Exfiltration)

**Detection**:
- VPC Flow Logs show unusual egress traffic
- CloudTrail shows bulk data downloads
- Macie detects PHI in unexpected S3 locations

**Response**:
1. Immediately revoke IAM role for suspected user
2. Isolate their EC2 instances
3. Review CloudTrail for past actions
4. Notify CISO, compliance, legal
5. Provide evidence to investigation team

### Scenario 3: Encryption Key Compromise

**Detection**:
- KMS logs show unusual key access
- GuardDuty alerts on key operations from unexpected principals

**Response**:
1. Immediately disable compromised key (KMS key policy change)
2. Activate backup key (schedule key rotation)
3. Re-encrypt all data with new key
4. Review CloudTrail for data accessed with compromised key
5. Notify all users of key rotation

---

## Testing & Validation

### Quarterly Security Testing

1. **Penetration Testing**: External firm tests for vulnerabilities
2. **Backup Recovery Testing**: Restore sample backup, verify integrity
3. **Disaster Recovery Drill**: Failover to backup infrastructure
4. **Access Control Testing**: Verify least privilege enforced
5. **Encryption Testing**: Verify all data encrypted appropriately

### Annual Audit

- Third-party HIPAA compliance audit
- Review all policies and procedures
- Verify controls are operating effectively
- Test incident response capabilities
- Validate training records and compliance

---

## Compliance Artifacts Generated by This Architecture

### Automated Evidence

- **CloudTrail logs**: Evidence of monitoring, accountability
- **AWS Config reports**: Evidence of encryption, security group configuration
- **IAM access reports**: Evidence of least privilege, access control
- **Backup reports**: Evidence of business continuity planning
- **GuardDuty findings**: Evidence of threat monitoring
- **Macie reports**: Evidence of data discovery and protection

### Required Manual Documentation

- **Policies and Procedures**: Data handling, incident response, access controls
- **Risk Assessment**: Identified threats, mitigating controls, residual risk
- **Business Associate Agreements**: Contracts with external collaborators
- **Training Records**: Documentation of HIPAA training
- **Security Incident Log**: Records of incidents and responses
- **Access Request Approvals**: Documentation of who approved what access

---

## Next Steps

1. Detailed Infrastructure-as-Code (Terraform/CloudFormation)
2. IAM Role and Policy Definitions
3. Encryption Key Management Strategy
4. Incident Response Playbooks
5. Training Materials & Compliance Documentation
6. Test Infrastructure and Security Validation
