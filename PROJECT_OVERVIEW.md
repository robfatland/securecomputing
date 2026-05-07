# Project1: Synthetic PHI Environment on AWS

## Project Overview

This project aims to build a comprehensive synthetic working environment on the AWS cloud designed to support learning and baseline understanding of PHI (Protected Health Information) handling under NIST guidelines for HIPAA compliance.

## Objectives

- **Establish a baseline understanding** of working with PHI data (clinical data, EHR systems, etc.)
- **Implement HIPAA-compliant** infrastructure and practices following NIST guidelines
- **Create a synthetic PHI environment** with realistic but entirely fabricated data
- **Enable safe exploration** of PHI handling, storage, transmission, and processing patterns
- **Understand HIPAA compliance** as a holistic framework combining organizational and technical controls

## Key Characteristics

- **Synthetic Data**: All content is made-up and intended to resemble real PHI without using actual patient information
- **AWS-Native**: Infrastructure will be deployed on AWS cloud services
- **NIST/HIPAA-Aligned**: Design and implementation will follow NIST guidance for HIPAA compliance
- **Learning-Focused**: The environment serves as a sandbox for understanding PHI workflows and security requirements

## Critical Insight: HIPAA as Organizational + Technical Framework

**Common Misunderstanding**: HIPAA compliance is ~80% technical engineering (encryption, firewalls, access controls).

**Reality**: HIPAA compliance is ~80% organizational/social engineering and ~20% technical engineering.

### The HIPAA Structure

The Security Rule breaks down as:
- **Administrative Safeguards** (~60%): Policies, procedures, role definitions, training, risk management, accountability
- **Physical Safeguards** (~20%): Facility access controls, workstation security, equipment management
- **Technical Safeguards** (~20%): Encryption, access controls, audit logging, intrusion detection

### Why This Matters for Our Project

Real-world breaches are more often caused by:
- Missing or inadequate policies and procedures
- Insufficient workforce training
- Lack of Business Associate Agreements
- Undocumented access justifications
- Missing risk assessments and audit trails
- Unclear roles and responsibilities

than by technical vulnerabilities.

**Our approach will integrate both**:
- Properly configured AWS technical infrastructure
- Documented organizational policies and procedures
- Defined roles with clear responsibilities
- Risk management and audit frameworks
- Training materials and accountability mechanisms
- Evidence of compliance through documentation

---

## HIPAA Regulatory Framework

### HIPAA Overview

**HIPAA (Health Insurance Portability and Accountability Act)** is the federal law protecting patient health information. It applies to:
- **Covered Entities**: Hospitals, clinics, health plans, healthcare providers
- **Business Associates**: Third-party vendors processing PHI on behalf of covered entities

### HIPAA's Three Core Rules

#### 1. Privacy Rule
**Purpose**: Controls how Protected Health Information (PHI) can be used and disclosed

**Key Requirements**:
- Patients must be informed how their data will be used (Notice of Privacy Practices)
- Use/disclosure only for authorized purposes (treatment, payment, operations, research with authorization)
- **Minimum Necessary Principle**: Access only the minimum information needed for the stated purpose
- Patients have rights: Access, amendment, accounting of disclosures

**For Research**:
- IRB review and approval required for all human subjects research
- Researcher must demonstrate: Why PHI is needed? Why is it the minimum necessary?
- Business Associate Agreements required for external institutions
- Patient authorization OR waiver of authorization (for de-identified data)

#### 2. Security Rule
**Purpose**: Establishes standards for protecting electronic PHI (ePHI)

**Three Components** (and why HIPAA compliance is 80% organizational, 20% technical):

- **Administrative Safeguards** (~60% of Security Rule)
  - Policies and procedures for PHI handling
  - Risk assessment and management
  - Workforce security and training
  - Access control administration (who gets access to what, why, how long)
  - Incident response procedures
  - Business Associate oversight
  - Sanctions policies (consequences for non-compliance)

- **Physical Safeguards** (~20% of Security Rule)
  - Facility access controls (badge access, security guards)
  - Workstation security (screen privacy, locked computers)
  - Equipment and media controls (secure disposal, encryption)

- **Technical Safeguards** (~20% of Security Rule)
  - Access controls (authentication, authorization, encryption keys)
  - Audit controls (logging who accessed what)
  - Integrity controls (ensuring data wasn't altered)
  - Transmission security (encryption in transit)

**Important**: HIPAA does NOT mandate specific technologies. It says WHAT must be protected, not HOW. Compliance requires demonstrating that your controls are appropriate for your risk level.

#### 3. Breach Notification Rule
**Purpose**: Requires notification of patients when their PHI is exposed

**Key Requirements**:
- If unsecured PHI is accessed by unauthorized individuals: Notify affected individuals within 60 days
- Notify U.S. Department of Health & Human Services (HHS)
- If breach affects 500+ residents: Notify media
- Document all breaches (even small ones) for audit trail

**Penalties**: 
- $100-$50,000 per violation
- Up to $1.5 million per category annually
- Criminal penalties: Up to $250,000 fine and 10 years imprisonment (for intentional disclosure)

---

## NIST Cybersecurity Framework & HIPAA Alignment

### NIST Overview

**NIST (National Institute of Standards and Technology)** is a U.S. government agency providing cybersecurity standards and guidance. While NIST is not legally required for HIPAA, it is frequently used to demonstrate compliance because NIST provides technical implementation details that HIPAA does not.

### NIST Cybersecurity Framework (CSF)

**Five Core Functions** (applicable to HIPAA):

1. **Identify**
   - Understand your assets (servers, databases, networks where PHI resides)
   - Understand business context (what is PHI, where does it flow?)
   - Risk assessment (what could go wrong, and what's the impact?)
   - For HIPAA: Conduct and document risk assessment annually

2. **Protect**
   - Implement safeguards (encryption, access controls, firewalls)
   - Develop policies and procedures
   - Train workforce on security and HIPAA
   - Manage third-party (Business Associate) security
   - For HIPAA: Implement Administrative, Physical, and Technical Safeguards

3. **Detect**
   - Monitor systems for suspicious activity
   - Maintain logs and audit trails
   - Alert on anomalies (unauthorized access attempts, data exfiltration)
   - For HIPAA: Maintain audit controls; detect breaches

4. **Respond**
   - Have an incident response plan
   - Investigate breaches when detected
   - Mitigate damage and contain breach
   - For HIPAA: Breach notification procedures (notify HHS, patients within 60 days)

5. **Recover**
   - Restore systems after incident
   - Backup and disaster recovery procedures
   - Improve controls to prevent recurrence
   - For HIPAA: Recovery procedures documented; 7-year retention of backups

### NIST SP 800-66: Implementing the HIPAA Security Rule

**Purpose**: Provides detailed technical guidance on how to implement HIPAA Security Rule requirements

**Key Sections**:
- Mapping HIPAA rules to NIST controls
- Implementation guidance for each Administrative, Physical, and Technical Safeguard
- Examples of compliance evidence (audit logs, policies, training records)
- Risk management processes

### NIST SP 800-53: Security and Privacy Controls

**Purpose**: Comprehensive catalog of security controls applicable to information systems

**Relevance to Project**:
- Many controls map directly to HIPAA requirements
- Provides technical details on encryption, access control, audit logging
- Used as template for security policy development
- Common reference in compliance audits

### Key NIST Principles Reflected in Our Architecture

| NIST Principle | How It's Implemented in Project |
|---|---|
| **Defense in Depth** | Multiple security layers: network (VPC, security groups), application (database views), identity (IAM), encryption (KMS), monitoring (CloudTrail) |
| **Least Privilege** | Each role gets minimum necessary permissions (PI cannot access non-study patients; Developer cannot decrypt keys) |
| **Separation of Duties** | Different people approve, provision, use, and audit access; audit logs stored in separate account |
| **Audit Trail** | Four-layer logging: CloudTrail (APIs), DynamoDB (application), CloudWatch (system), VPC Flow Logs (network) |
| **Continuous Monitoring** | Real-time alerts via GuardDuty (threats), Macie (data exposure), AWS Config (compliance drift) |
| **Encryption Always** | All data encrypted at rest (KMS) and in transit (TLS); separate encryption keys per environment |
| **Authentication & Authorization** | MFA required for all roles; federated identity via University SSO; IP restrictions for sensitive roles |
| **Immutability** | Audit logs cannot be deleted; S3 versioning; Glacier retention |
| **Incident Response** | Defined workflows, automatic alerting, forensic capabilities (CloudTrail review) |

---

## Compliance as Governance: Why 80% is Organizational

The HIPAA Security Rule allocates ~60% of requirements to **Administrative Safeguards**—this is where real HIPAA compliance lives.

### Real-World Examples

**Scenario 1: Encryption at Rest (20% Technical)**
- Technical solution: AWS KMS encryption on RDS database
- But HIPAA compliance requires:
  - Policy: "All PHI databases must be encrypted"
  - Risk assessment: "Unencrypted databases expose X risk; encryption mitigates to Y"
  - Training: Staff trained on why encryption required
  - Monitoring: Regular verification encryption is enabled
  - Responsibility assignment: "DBA is accountable for key rotation"
  - Audit trail: "Documented KMS key rotation on [dates]"

**Scenario 2: Access Control (60% Administrative)**
- Technical solution: IAM roles and database views
- But HIPAA compliance requires:
  - Policy: "Researchers access only data for approved studies"
  - Justification process: "Each access requires IRB approval + compliance review"
  - Training: Staff understand minimum necessary principle
  - Role assignment: Documented approval chain (who approved what)
  - Periodic review: "Compliance officer reviewed researcher access on [date]"
  - Sanctions: "Policy: Researchers violating access policy face discipline"
  - Documentation: "Access request approval chain for every researcher"

**Scenario 3: Workforce Security (100% Administrative)**
- Technical solution: None—this is purely organizational
- But HIPAA requires:
  - Policy: "All staff handling PHI must complete HIPAA training"
  - Training records: Document who trained, when, what topics
  - Sanctions policy: "Consequences for HIPAA violations"
  - Termination procedures: "When employee leaves, how is access revoked?"
  - Background checks: "Policy requiring background checks for workforce"

### Compliance Evidence

What auditors look for:
- **Policies**: Written documentation of rules (100% of audit)
- **Training records**: Evidence staff understand policies (100% of audit)
- **Risk assessments**: Documentation of threats identified and mitigated (100% of audit)
- **Audit logs**: Evidence that policies are being enforced (100% of audit)
- **Incident reports**: Evidence of breaches, responses, remediation (100% of audit)
- **Approval chains**: Documentation of who approved what access (100% of audit)
- **Technical controls**: Encryption, firewalls, access controls (small portion of audit)

---

## Scope

This environment will encompass:

### Organizational/Administrative Components
- Defined roles and responsibilities (Security Officer, Data Custodian, System Administrator, etc.)
- Documented policies and procedures for PHI handling
- Risk assessment and management framework
- Incident response and breach notification procedures
- Workforce training materials
- Business Associate Agreement templates
- Access control justification and audit procedures
- Compliance monitoring and evidence collection mechanisms

### Technical Components
- Cloud infrastructure architecture for handling sensitive health data
- Data generation and management of synthetic PHI
- Identity and Access Management (IAM) with role-based controls
- Encryption (at rest and in transit)
- Network segmentation and security
- Audit logging and monitoring
- Data integrity controls
- Intrusion detection and prevention
- Compliance validation mechanisms

## Next Steps

1. **Define Organizational Structure** - Roles, responsibilities, governance model
2. **Map Compliance Requirements** - HIPAA Privacy Rule, Security Rule, NIST alignment
3. **Design AWS Technical Architecture** - Services, topology, security controls
4. **Create Policy Framework** - Access controls, data handling, incident response
5. **Implement Infrastructure** - Build AWS environment with documented controls
6. **Develop Audit & Monitoring** - Logging, alerting, compliance verification
7. **Create Training Materials** - Workforce education on HIPAA and procedures
8. **Document Everything** - Risk assessments, control mappings, compliance evidence
