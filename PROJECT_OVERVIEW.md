# Synthetic PHI Environment on AWS for Clinical Research (SPEACR)

> **PDF generation:** `pandoc --toc --toc-depth=2 -V geometry:margin=1in --pdf-engine=xelatex PROJECT_OVERVIEW.md ARCHITECTURE.md GATES.md PHASE0_CHARTER.md RISK_ASSESSMENT.md POLICY_AI_ACCEPTABLE_USE.md POLICY_SUITE.md SYNTHETIC_DATA.md NISTDocs.md ORGANIZATIONAL_STRUCTURE.md KNOWLEDGE_CHECKS.md -o SecureComputing_Book.pdf` — see `README.md` for install instructions.

## Project Documents

| Document | Summary |
|----------|---------|
| `PROJECT_OVERVIEW.md` | Master document: objectives, glossary, HIPAA/NIST framework, project scenario, Day Framework phases, pre-existing conditions, and to-do list |
| `ARCHITECTURE.md` | Technical architecture: AWS services registry, researcher environment model, network design, upload path security, AI gatekeeper design |
| `GATES.md` | Gate registry: definitions, evidence requirements, sequencing, and enforcement for all six project gates |
| `PHASE0_CHARTER.md` | Phase 0 deliverable: project charter (scope, team, roles, governance, authorization signatures) |
| `RISK_ASSESSMENT.md` | Phase 1 deliverable: threat actors, scenarios, risk scoring, mitigations, residual risk acceptance |
| `POLICY_AI_ACCEPTABLE_USE.md` | Phase 1 deliverable: full AI use policy (permitted/prohibited services, gatekeeper, agentic AI, incidents, sanctions) |
| `POLICY_SUITE.md` | Phase 1 deliverable: template outlines for access control, data handling, incident response, sanctions, workforce security, media disposal policies |
| `NISTDocs.md` | Reference guide: NIST publications relevant to HIPAA and CUI compliance with canonical URLs |
| `SYNTHETIC_DATA.md` | Synthetic data overview: dataset descriptions (PD0–PD3), formats, examples, and visualizations |
| `DIAGRAMS.md` | System architecture diagrams (Mermaid): network, data flow, IAM, lifecycle |
| `COST.md` | AWS service cost estimates, spend tactics, hibernation/destroy cost comparison |
| `COMPLETION.md` | Demonstrator vs. production: what's built, what's missing, and what a real project must add |
| `ORGANIZATIONAL_STRUCTURE.md` | Organizational roles, responsibilities, and reporting relationships |
| `KNOWLEDGE_CHECKS.md` | Learning verification questions for team training |

### Constituent Repositories

| Repository | Purpose | Relationship |
|------------|---------|--------------|
| `securecomputing` (this repo) | System documentation, IaC, policies, analysis code | The research environment itself |
| `securecomputing-datagen` | Synthetic PHI generation tooling (Synthea config, custom generators, schema definitions) | Data factory — produces synthetic patient data loaded into the analysis environment via the standard upload path. Isolated from the analysis system by design: datagen has no access to the analysis environment and vice versa. |

---

## Project Overview

The purpose of this project is to document a functional synthetic research computing environment on the AWS cloud as a learning instance of PHI handling under NIST guidelines for HIPAA compliance.


*Disclaimer: This project presents a hypothetical scenario and computing system including learning materials. It is under development as of June 2026 and has not yet been officially reviewed or sanctioned by UW or UW Medicine information security offices.*

## Objectives

- **Establish a baseline understanding** of working with PHI data (clinical data, EHR systems, etc.)
- **Implement HIPAA-compliant** infrastructure and practices following NIST guidelines
- **Create a synthetic PHI environment** with realistic but entirely fabricated data
- **Enable safe exploration** of PHI handling, storage, transmission, and processing patterns
- **Understand HIPAA compliance** as a holistic framework combining organizational and technical controls

## Key Characteristics

- **Synthetic Data**: All content is made-up to resemble real PHI without using actual patient information
- **AWS-Native**: Computing infrastructure is deployed on the AWS cloud platform
- **NIST/HIPAA-Aligned**: Design and implementation follows NIST guidance for HIPAA compliance
- **Learning Resource**: The environment serves as a hands-on learning tool for the PI and team — building compliance understanding through the process of constructing the system, not just reading about it
- **Demonstration System**: The completed environment serves as a reusable template for real PHI research projects, built to the highest compliance standard so subsequent projects can inherit the framework
- **Question-based build narrative**: Steps through the phases of building a HIPAA-compliant system through a series of questions posed to a Principal Investigator
- **Blank Slate Rule**: All infrastructure is defined in CDK code and can be cleanly destroyed and verified empty — no zombie services, no orphaned spend. The same code that builds the system tears it down. See `ARCHITECTURE.md` for implementation details.

---

## Glossary

### General Terminology

| Term | Definition |
|------|------------|
| **HIPAA** | Health Insurance Portability and Accountability Act — the U.S. federal law (1996) that establishes national standards for protecting patient health information. Comprises three core rules: the Privacy Rule, the Security Rule, and the Breach Notification Rule. |
| **Privacy Rule** | The HIPAA rule governing how PHI may be used and disclosed. Establishes patient rights, the minimum necessary principle, and requirements for research use of PHI (IRB approval, patient authorization or waiver). |
| **Security Rule** | The HIPAA rule establishing standards for protecting electronic PHI (ePHI). Defines three categories of safeguards: Administrative (~60%), Physical (~20%), and Technical (~20%). Does not mandate specific technologies — requires that controls be appropriate to the organization's risk level. |
| **Breach Notification Rule** | The HIPAA rule requiring notification when unsecured PHI is accessed by unauthorized individuals. Requires notification to affected individuals (within 60 days), HHS, and media (if 500+ individuals affected). |
| **NIST** | National Institute of Standards and Technology — a U.S. government agency that publishes cybersecurity standards and guidance. Not legally required for HIPAA, but widely used to demonstrate compliance because NIST provides implementation details that HIPAA does not. |
| **NIH** | National Institutes of Health — the U.S. federal agency that funds biomedical research. The funding source for this project. NIH grants carry data management and sharing requirements. |
| **HHS** | U.S. Department of Health and Human Services — the federal agency that administers HIPAA. HHS Office for Civil Rights (OCR) enforces HIPAA and receives breach notifications. |
| **IRB** | Institutional Review Board — a committee that reviews and approves research involving human subjects. Required before any research use of PHI. Evaluates whether the research justifies PHI access and whether adequate protections are in place. |
| **CISO** | Chief Information Security Officer — the institutional executive responsible for information security strategy and oversight. At UW, provides institutional-level security governance and serves as an escalation path for project-level security issues. |
| **CI** | Computing Infrastructure — the collection of cloud services and ancillary systems that comprise the research computing environment for this project. Ancillary systems include laptop or desktop computers used to access the cloud environment and institutional repositories that provide project data. |
| **Gate** | A mandatory checkpoint where specific deliverables must be completed and signed off before subsequent work is permitted to begin. Gates enforce compliance sequencing — they prevent work from proceeding until its organizational or technical prerequisites are demonstrably satisfied. A gate is not a suggestion; it is a hard stop. If the gate condition is not met, the work it enables cannot proceed. Gates make the framework auditable: an auditor can ask "how do you know X was done before Y?" and the answer is the gate evidence. See `GATES.md` for the full gate registry. |
| **Phase** | A grouping of related activities within the project lifecycle. Phases are sequenced so that each builds on the outputs of the prior phase. Within a phase, individual days may be worked in parallel. |
| **Day** | An effort-unit representing a discrete work session or milestone. Days are numbered sequentially but need not be consecutive in calendar time. There may be hours, days, or weeks between numbered days. |
| **PHI** | Protected Health Information — individually identifiable health information held or transmitted by a covered entity or business associate. Includes any of the 18 HIPAA identifiers linked to health data. |
| **ePHI** | Electronic PHI — PHI in electronic form. Subject to the HIPAA Security Rule's technical safeguards. |
| **MRN** | Medical Record Number — the unique identifier a healthcare facility assigns to each patient. One of the 18 HIPAA identifiers. Particularly dangerous because it appears as an innocuous alphanumeric string that people may not recognize as PHI. |
| **BAA** | Business Associate Agreement — a contract between a covered entity and a third party (business associate) that handles PHI on its behalf. Required by HIPAA before any PHI disclosure to the associate. |
| **DUA** | Data Use Agreement — a contract governing the use of a Limited Data Set. Less restrictive than a BAA but still legally binding. |
| **Minimum Necessary** | The HIPAA principle requiring that access to PHI be limited to the minimum information needed to accomplish the intended purpose. |
| **Covered Entity** | An organization subject to HIPAA: health plans, healthcare clearinghouses, and healthcare providers who transmit health information electronically. |
| **Business Associate** | A person or entity that performs functions involving PHI on behalf of a covered entity (e.g., cloud providers, IT vendors, researchers receiving PHI). |
| **Compliance Perimeter** | The boundary within which PHI is permitted to exist. For this project: the AWS VPC and BAA-covered AWS services. Anything outside this boundary must not receive PHI. |
| **UW** | A nominal designator for the PI's university institution — data source, primary research site, holder of the AWS BAA. |
| **FH** | A nominal designator for a hypothetical collaborator's healthcare facility; a Co-PI institution. |
| **PI** | Principal Investigator — the lead researcher on the project; holds the NIH award; serves as project sponsor, Privacy Officer, and risk acceptor. |
| **SCP** | Service Control Policy — an AWS Organizations policy that sets permission guardrails on member accounts. SCPs define the *maximum* permissions available in an account; they cannot grant permissions, only restrict them. Applied by the Management account and inherited by all member accounts in the Organization. |
| **Key Policy** | A resource-based policy attached to a KMS encryption key that defines who can use the key for encryption, decryption, and administration. Key policies are *independent of* IAM policies — both must allow an action for it to succeed. This is how the project enforces separation of duties: even if an IAM policy grants broad S3 access, the key policy can deny decrypt permission, making the data unreadable. Key policies are the mechanism that prevents IT Staff from reading PHI despite having infrastructure admin access. |

### Technical Terms

| Term | Definition |
|------|------------|
| **VPC** | Virtual Private Cloud — an isolated virtual network within AWS where project resources run. Resources in the VPC are not accessible from the public internet unless explicitly configured. The VPC is the primary network boundary of the compliance perimeter. |
| **VPC Endpoint** | A private connection between a VPC and an AWS service that keeps traffic within AWS's internal network (never traverses the public internet). Solves the problem: "my EC2 instance is in a private subnet with no internet — how does it reach S3, Bedrock, KMS?" Two types: Gateway Endpoints (free, S3 and DynamoDB only — adds a route table entry) and Interface Endpoints ($7.30/month each, all other services — creates a network interface with a private IP in your subnet). Without endpoints, resources in private subnets cannot reach AWS services at all. **How it works in practice:** application code is unchanged — `boto3.client('s3')` uses the same service URL as always. The endpoint hijacks DNS so that `s3.us-west-2.amazonaws.com` resolves to a private IP inside the VPC instead of a public IP. Traffic routes through the endpoint transparently. The researcher writing code never knows or cares whether an endpoint exists — it's invisible infrastructure plumbing. |
| **IAM** | Identity and Access Management — AWS service for controlling who can access what resources. Defines roles, policies, and permissions. Federated with UW SSO for this project. |
| **SSO** | Single Sign-On — an authentication mechanism allowing users to log in once (via their institutional identity) and gain access to multiple systems without re-authenticating. UW provides SSO that federates into AWS. |
| **MFA** | Multi-Factor Authentication — requiring two or more verification factors (something you know + something you have) to authenticate. Required for all access to the research environment. Mitigates credential theft. |
| **TLS** | Transport Layer Security — cryptographic protocol that provides encryption in transit. All data moving between systems (upload to S3, database connections, API calls) uses TLS 1.2 or higher. |
| **KMS** | Key Management Service — AWS service for creating and managing encryption keys. All PHI at rest is encrypted with KMS-managed keys. Key policies restrict which roles can encrypt/decrypt. |
| **S3** | Simple Storage Service — AWS object storage. Used for PHI landing zone, validated data, derived data, and audit logs. Encrypted, versioned, access-logged. |
| **RDS** | Relational Database Service — AWS managed database. Stores structured PHI (patient records). Encrypted at rest and in transit. |
| **EC2** | Elastic Compute Cloud — AWS virtual machines. Hosts the IDE server, notebook server, and processing workloads. Runs in private subnets within the VPC. |
| **EFS** | Elastic File System — AWS managed NFS-compatible shared filesystem. Mounted across researcher compute instances for shared working files, code, and intermediate results. Encrypted at rest and in transit. |
| **ECS / Fargate** | Elastic Container Service / Fargate — AWS container orchestration and serverless container execution. Runs Docker containers for processing pipelines. |
| **ECR** | Elastic Container Registry — AWS container image storage. Stores Docker images (code artifacts, no PHI). |
| **Bedrock** | AWS managed LLM inference service. Runs AWS-hosted copies of foundation models (Claude, Llama, etc.) within the AWS boundary. BAA-covered; customer data not used for model training. The project's internal AI backend. |
| **Comprehend Medical** | AWS NLP service specialized in detecting medical entities in text. Used as the PHI detection layer in the gatekeeper service. |
| **SageMaker** | AWS managed ML platform. Provides notebook environments, model training, and inference hosting. Runs in VPC-only mode for this project. |
| **CloudTrail** | AWS API call logging service. Records every API call made to AWS services — who did what, when, from where. The foundation of the audit trail. |
| **CloudWatch** | AWS monitoring and logging service. Aggregates logs, triggers alarms, provides dashboards. |
| **GuardDuty** | AWS threat detection service. Analyzes CloudTrail, VPC Flow Logs, and DNS logs for anomalous or malicious activity. |
| **Macie** | AWS sensitive data discovery service. Scans S3 buckets for exposed PHI or sensitive data. |
| **AWS Config** | AWS compliance monitoring service. Evaluates resource configurations against rules; detects drift from security baselines. |
| **Security Hub** | AWS aggregated security findings dashboard. Consolidates findings from GuardDuty, Macie, Config, and other sources. |
| **Wickr** | AWS end-to-end encrypted messaging service. Used for secure team communication within the project. HIPAA-eligible. |
| **Lambda** | AWS serverless compute. Runs code in response to events (e.g., gatekeeper logic, upload validation). |
| **SNS** | Simple Notification Service — AWS push notification service. Used for system alerts (upload confirmations, security events). |
| **NACLs** | Network Access Control Lists — stateless firewall rules applied at the subnet level within a VPC. Control inbound and outbound traffic by IP address and port. A layer of defense in addition to security groups. |
| **IaC** | Infrastructure as Code — the practice of defining cloud infrastructure in version-controlled template files (Terraform, CloudFormation) rather than configuring manually. Enables reproducibility, auditability, and drift detection. |
| **OIDC** | OpenID Connect — an identity layer built on OAuth 2.0. Used for GitHub Actions to authenticate to AWS without storing long-lived credentials (GitHub's OIDC provider issues short-lived tokens that AWS IAM trusts). |
| **DLP** | Data Loss Prevention — controls and monitoring designed to detect and prevent unauthorized data exfiltration. In this project: network egress restrictions, clipboard controls, and Macie scanning. |
| **Gatekeeper** | A technical control preventing inadvertent PHI disclosure to AI services. In this example system the component is based upon the AWS Comprehend Medical service used to scan AI prompts for PHI before forwarding them to the AWS Bedrock Foundation Model API service. Implemented as a Lambda function or sidecar process. |
| **GitHub** | External source code repository (not an AWS service). Used for version control of code, IaC, and documentation. Outside the compliance perimeter — no PHI permitted. |
| **CI/CD** | Continuous Integration / Continuous Deployment — automated pipelines that build, test, and deploy code. (CI/CD not to be confused with CI = Computing Infrastructure.) |
| **GitHub Actions** | CI/CD automation service within GitHub. Builds containers, runs tests, deploys to AWS. Uses OIDC federation for AWS credentials. |
| **Conformance Pack** | A pre-built collection of AWS Config rules bundled together for a specific compliance standard (e.g., "Operational Best Practices for HIPAA"). Deploying a conformance pack evaluates your environment against dozens of relevant rules at once rather than configuring each rule individually. |
| **EventBridge** | AWS event bus service. Routes events (from AWS services, custom applications, or schedules) to targets (Lambda, SNS, etc.). Used in this project for: scheduled EC2 start/stop, and routing Security Hub findings to alert channels. |
| **Object Lock** | S3 feature that prevents objects from being deleted or overwritten for a specified retention period. Used on audit logs to ensure immutability — even an administrator cannot destroy compliance evidence before the retention period expires. |
| **Presigned URL** | A time-limited, authenticated URL generated by AWS that grants temporary access to a specific resource without requiring the recipient to have AWS credentials. SageMaker uses presigned URLs to give researchers browser access to their notebook instances. |
| **Security Group** | A virtual firewall attached to AWS resources (EC2, RDS, etc.) that controls inbound and outbound traffic by protocol, port, and source/destination. Stateful — if inbound traffic is allowed, the response is automatically allowed. |
| **SSM (Systems Manager)** | AWS service for managing EC2 instances. Session Manager (a feature of SSM) provides browser-based or CLI shell access to instances without SSH, without public IPs, and without inbound firewall rules. The access path for researchers to reach their IDE instances. |
| **Finding** | A security observation generated by GuardDuty, Macie, Config, or Security Hub. Findings have a severity (CRITICAL, HIGH, MEDIUM, LOW) and describe what was detected, where, and recommended remediation. Findings are the input to the alert flow. |
| **Drift** | When a deployed resource's actual configuration diverges from its intended configuration. Example: a security group rule is manually added via the console that wasn't in the CDK definition. AWS Config detects drift; the remedy is to either update the CDK code to match or revert the resource to match the code. |
| **Data Events (CloudTrail)** | Detailed logging of data-plane operations (e.g., S3 GetObject, PutObject; Lambda Invoke). More granular than management events (which log control-plane operations like CreateBucket). Data events are essential for PHI audit trails because they record *who accessed which specific object and when*. |
| **Organization Trail** | A CloudTrail trail configured at the AWS Organizations level that automatically logs API calls across all member accounts. Ensures no account can opt out of logging. Logs are delivered to a central bucket (in the Audit account). |
| **CDK** | Cloud Development Kit — AWS tool for defining cloud infrastructure in a general-purpose programming language (Python, TypeScript, etc.) rather than YAML/JSON templates. CDK code compiles to CloudFormation templates for deployment. The IaC tool used in this project. |
| **CloudFormation** | AWS native infrastructure-as-code service. Deploys and manages resources from declarative JSON/YAML templates. CDK compiles to CloudFormation under the hood. Provides stack-based resource management: create, update, and delete resources as a unit. |
| **DocumentDB** | AWS managed document database (MongoDB-compatible). Stores data as JSON-like documents rather than relational rows. Used in this project for per-patient "chart view" documents that aggregate data across all datasets. HIPAA-eligible. |
| **Athena** | AWS serverless SQL query engine that runs queries directly against data in S3 (no database to manage). Pay per query. Useful for ad-hoc analysis of PD3 lab data or forensic queries against archived audit logs. |
| **OMOP CDM** | Observational Medical Outcomes Partnership Common Data Model — a standardized data model for observational health research. Defines tables (PERSON, CONDITION_OCCURRENCE, MEASUREMENT, etc.) with standardized vocabularies (SNOMED, ICD-10, LOINC, RxNorm). Used by the OHDSI network across hundreds of institutions. The format for PD0 in this project. |
| **Synthea** | Open-source synthetic patient generator (Java). Produces realistic but fabricated patient records including demographics, conditions, medications, procedures, and lab results. Output is converted to OMOP format via ETL-Synthea. |
| **Blank Slate Rule** | A design principle requiring that the CDK infrastructure code can cleanly delete and verify deletion of all provisioned AWS resources — returning the accounts to a blank state with no zombie services incurring cost. The same resource definitions used for build-up are used for tear-down. See ARCHITECTURE.md. |

### Template Markers

This project produces documents intended as guidance for real projects. The following visual flags indicate sections that require customization:

> ⚠️ **TEMPLATE:** This section is a demonstrator example. You are responsible for modifying this to be accurate to your program. Replace placeholder content with institution-specific details, verified procedures, and legally reviewed language.

> 📋 **GENERIC:** This content uses generic language (e.g., "sanctions range from retraining to removal"). Your actual version must be considerably more detailed and specific to your institutional policies and applicable regulations.

These markers appear throughout project documents wherever content is intentionally left at template level rather than fully specified.

---

## Critical Insight: HIPAA as Organizational + Technical Framework

**Common Misunderstanding**: HIPAA compliance is ~80% technical engineering (encryption, firewalls, access controls).

**Reality**: HIPAA compliance is ~80% organizational/social engineering and ~20% technical engineering.

### The HIPAA Structure

The Security Rule breaks down as:
- **Administrative Safeguards** (~60%): Policies, procedures, role definitions, training, risk management, accountability
- **Physical Safeguards** (~20%): Facility access controls, workstation security, equipment management
- **Technical Safeguards** (~20%): Encryption, access controls, audit logging, intrusion detection

### Why This Matters for This Project

Real-world breaches are more often caused by:
- Missing or inadequate policies and procedures
- Insufficient workforce training
- Lack of Business Associate Agreements
- Undocumented access justifications
- Missing risk assessments and audit trails
- Unclear roles and responsibilities

than by technical vulnerabilities.

**This project's approach integrates both**:
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

### Key NIST Principles Reflected in the Architecture

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

---

## Day Framework: Project Lifecycle from Approval to Decommission

### Purpose

This framework tracks the wall-clock progression of a PHI-focused research project from initial approval through active research to eventual shutdown. Days are numbered starting from Day 0 and need not be consecutive — they represent discrete work sessions or milestones, not calendar days.

### Design Principles

- **Days are effort-units, not calendar-units.** Day 5 does not mean "the fifth calendar day." There may be hours, days, or weeks of elapsed time between numbered days (waiting on approvals, scheduling, procurement, etc.).
- **Days are grouped into Phases.** Within a phase, some days may be worked in parallel. The day numbers represent the critical-path ordering.
- **Gate Checkpoints** mark points where work cannot proceed until a prior deliverable is signed off. These enforce compliance sequencing (e.g., no PHI access before training is documented).
- **The framework covers the full lifecycle**: build-up, steady-state operations, and controlled shutdown.

### Phases

| Phase | Days | Focus | Gate to Exit |
|-------|------|-------|--------------|
| **Phase 0: Authorization** | 0–2 | Project approval, role assignment, governance setup | Signed project charter; roles documented |
| **Phase 1: Foundation** | 3–8 | Policies, risk assessment, training, BAAs | Risk assessment complete; all personnel trained; BAAs executed |
| **Phase 2: Infrastructure** | 9–15 | AWS environment build, security controls, encryption, networking | Infrastructure passes security validation; audit logging confirmed |
| **Phase 3: Data & Access** | 16–20 | Synthetic PHI generation, access provisioning, testing | Access controls verified; minimum-necessary demonstrated |
| **Phase 4: Validation** | 21–24 | End-to-end compliance testing, penetration testing, audit dry-run | Compliance officer sign-off; system authorized for use |
| **Phase 5: Operations** | 25+ | Active research, ongoing monitoring, periodic reviews | Continuous — triggered reviews on schedule or by incident |
| **Phase 6: Decommission** | TBD | Access revocation, data disposition, key destruction, final audit | Final audit report; all PHI confirmed destroyed or returned |

---

### Phase Definitions

#### Phase 0: Authorization (Days 0–2)

**Purpose:** Establish that the project has legitimate sponsorship, a defined scope, and accountable people before any work begins.

**Rationale:** HIPAA requires that PHI-handling activities be formally authorized and that responsible individuals are identified. Without this phase, there is no governance — no one is accountable, no one can sign off on risk acceptance, and no audit trail has a starting point. This phase is the legal and organizational foundation everything else rests on.

**Scope:**
- Identify the project sponsor (the person with authority to accept risk)
- Draft the project charter: purpose, scope, data types, expected duration, personnel
- Assign roles per the organizational structure (Security Officer, Data Custodian, System Administrator, Researcher, Compliance Officer)
- Confirm the governance model: who approves what, escalation paths, decision authority
- Establish the compliance documentation repository (where policies, evidence, and audit artifacts will live)

**Key Activities:**
- Sponsor meeting: align on objectives, constraints, budget, timeline
- Role assignment: match people to defined roles; document in charter
- Charter review and signature: formal authorization to proceed

**Deliverables:**
- Signed project charter
- Role assignment matrix (person → role → responsibilities)
- Governance model document (approval chains, escalation paths)
- Compliance documentation repository initialized

**Exit Gate (G1):** Charter signed by sponsor; all roles assigned and accepted by named individuals.

---

#### Phase 1: Foundation (Days 3–8)

**Purpose:** Build the organizational and policy infrastructure that governs all subsequent technical work. This is where the "80% organizational" reality of HIPAA compliance lives.

**Rationale:** Technical controls are meaningless without the policies that define them, the training that ensures people follow them, and the risk assessment that justifies them. An encrypted database with no access policy, no trained users, and no documented risk acceptance is not compliant — it's just encrypted. This phase ensures that when infrastructure is built, it's built *to a defined standard* with *trained people* operating under *documented rules*.

**Scope:**
- Risk assessment: identify assets, threats, vulnerabilities, and risk levels
- Policy development: access control, data handling, incident response, sanctions, media disposal
- Workforce training: HIPAA awareness, role-specific responsibilities, sanctions awareness
- Business Associate Agreements: identify third parties, draft and execute BAAs
- Compliance evidence framework: define what evidence will be collected and how

**Key Activities:**
- Asset inventory: enumerate systems, data stores, and data flows that will handle PHI
- Threat modeling: identify realistic threats (insider misuse, external breach, accidental disclosure)
- Risk scoring: likelihood × impact for each threat; document risk acceptance or mitigation plans
- Policy drafting: write policies covering each HIPAA Security Rule safeguard area
- Training delivery: conduct HIPAA training; collect acknowledgment signatures
- BAA negotiation: identify all third parties (AWS is one); execute agreements
- Evidence plan: define audit artifacts, storage location, retention periods

**Deliverables:**
- Completed risk assessment document (threats, scores, mitigations, residual risk acceptance)
- Policy suite: access control, data handling, incident response, sanctions, media disposal, workforce security
- Training records: attendance, completion certificates, signed acknowledgments
- Executed Business Associate Agreements
- Evidence collection plan (what, where, how long, who reviews)

**Exit Gates:**
- G2: Risk assessment documented and accepted by sponsor
- G3: All personnel HIPAA-trained with documented evidence
- G4: BAAs executed with all identified third parties

**Parallelism note:** Risk assessment (Days 3, 8) and policy drafting (Day 4) inform each other iteratively. Training (Days 5–6) can proceed once policies are in draft form. BAAs (Day 7) can be negotiated concurrently with other activities.

---

#### Phase 2: Infrastructure (Days 9–15)

**Purpose:** Build the AWS technical environment that will host PHI, implementing the security controls defined by Phase 1 policies and justified by the Phase 1 risk assessment.

**Rationale:** Infrastructure is built *to specification* — the specification being the policies and risk mitigations from Phase 1. Every technical control should trace back to a policy requirement and a risk assessment finding. This traceability is what auditors look for: "Why is this encrypted?" → "Because Policy AC-7 requires encryption of PHI at rest, based on Risk Assessment finding RA-12."

**Scope:**
- AWS account structure and organizational boundaries
- Network architecture: VPC topology, segmentation, traffic controls
- Identity and access management: IAM roles, federation, MFA, least-privilege enforcement
- Encryption: KMS key hierarchy, key policies, rotation, data-at-rest and in-transit encryption
- Compute and storage: provisioning databases, object storage, compute with security baselines
- Monitoring and audit: logging infrastructure, alerting, compliance drift detection
- Security validation: verify controls match policy requirements

**Key Activities:**
- AWS Organization and account setup (separate accounts for production, audit, management)
- VPC design: public/private subnets, NAT gateways, security groups, NACLs, flow logs
- IAM architecture: role definitions mapped to organizational roles; policy documents; MFA enforcement
- KMS setup: CMKs for each data classification; key policies restricting usage by role; automatic rotation
- Database provisioning: RDS with encryption, automated backups, parameter groups for security
- S3 configuration: bucket policies, encryption defaults, versioning, access logging
- Monitoring stack: CloudTrail (all regions), CloudWatch alarms, GuardDuty, Macie, AWS Config rules
- Security validation: run AWS Config conformance packs; review Security Hub findings; remediate

**Deliverables:**
- Deployed AWS infrastructure (IaC templates — CloudFormation or Terraform)
- Network diagram with security boundaries documented
- IAM role-to-organizational-role mapping document
- KMS key inventory with policies and rotation schedule
- Monitoring and alerting configuration (what triggers alerts, who receives them)
- Security validation report (findings, remediations, residual items)

**Exit Gate (G5):** Infrastructure passes security validation; all critical/high findings remediated; audit logging confirmed operational across all services.

**Dependency:** Cannot begin until G1 (authorization) is complete. Can begin before G2/G3/G4 are fully closed *for infrastructure build only* — but no PHI (even synthetic) can be loaded until all Phase 1 gates are passed.

---

#### Phase 3: Data & Access (Days 16–20)

**Purpose:** Populate the environment with synthetic PHI and provision access according to the minimum-necessary principle, then verify that access controls work as designed.

**Rationale:** This phase is where organizational controls (who should access what, and why) meet technical controls (database views, row-level security, IAM policies). The goal is to demonstrate that the system enforces minimum-necessary access — a core HIPAA requirement — and that access decisions are documented and auditable.

**Scope:**
- Synthetic PHI data generation (realistic but entirely fabricated)
- Data loading into secured infrastructure
- Access control implementation: database views, row-level security, application-layer controls
- Access provisioning: grant access per approved roles and documented justifications
- Access testing: verify both positive cases (authorized users can access) and negative cases (unauthorized users cannot)

**Key Activities:**
- Design synthetic data schema: patient demographics, clinical records, lab results, medications
- Generate synthetic PHI using tooling (Synthea, Faker, custom generators)
- Load data into RDS/S3 with encryption verified
- Implement database views scoped to each role (PI sees study patients only; analyst sees de-identified subset)
- Provision access: create user accounts, assign roles, document justification for each grant
- Positive testing: each role accesses data they should see; verify correct results
- Negative testing: each role attempts access beyond their scope; verify denial and audit log capture
- Access audit: review logs to confirm all access attempts (granted and denied) are recorded

**Deliverables:**
- Synthetic PHI dataset (documented schema, generation method, volume)
- Database view definitions and row-level security policies
- Access provisioning records (who, what role, what justification, who approved)
- Test results: positive and negative access control verification
- Audit log samples demonstrating access tracking

**Exit Gate (G5 continued):** Access controls verified through testing; minimum-necessary principle demonstrated; all access grants documented with justification.

**Dependency:** All Phase 1 gates (G2, G3, G4) must be closed before synthetic PHI is loaded. Phase 2 gate (G5 — infrastructure validated) must be closed before data loading.

---

#### Phase 4: Validation (Days 21–24)

**Purpose:** Confirm that the complete system — organizational controls, technical controls, and operational procedures — works end-to-end and is ready for authorized use.

**Rationale:** Individual components may pass unit testing but fail in combination. This phase tests the system as a whole: can a researcher actually do their work within the compliance boundaries? Do alerts fire when they should? Would an auditor find the evidence they need? This is the "dress rehearsal" before going live.

**Scope:**
- End-to-end workflow testing: simulate real research scenarios from access request through data analysis
- Security testing: vulnerability scanning, penetration testing, misconfiguration detection
- Compliance audit simulation: walk through an audit checklist as if an external auditor were reviewing
- Incident response drill: simulate a breach scenario and execute the response plan
- Final review and authorization: compliance officer evaluates all evidence and authorizes the system

**Key Activities:**
- Researcher workflow test: submit access request → approval → provisioning → data query → results → audit trail
- Vulnerability scan: automated scanning of infrastructure for known vulnerabilities
- Penetration test: attempt to escalate privileges, access unauthorized data, exfiltrate information
- Audit simulation: compliance officer reviews policies, training records, risk assessment, technical controls, audit logs
- Incident response drill: simulate unauthorized access detection → alert → investigation → containment → notification
- Gap remediation: address any findings from testing or audit simulation
- Authorization decision: compliance officer signs off that system meets HIPAA requirements

**Deliverables:**
- End-to-end test results and scenario documentation
- Vulnerability scan report (findings and remediations)
- Penetration test report (findings and remediations)
- Audit simulation findings and gap analysis
- Incident response drill after-action report
- System authorization memo (signed by compliance officer)

**Exit Gate (G6):** Compliance officer reviews all evidence and formally authorizes the system for use with PHI (synthetic in this case). All critical findings from testing remediated.

---

#### Phase 5: Operations (Day 25+)

**Purpose:** Conduct active research while maintaining continuous compliance through monitoring, periodic reviews, and incident response readiness.

**Rationale:** Compliance is not a point-in-time achievement — it's a continuous state. Systems drift, people change roles, new threats emerge, and policies need updating. This phase defines the ongoing activities that keep the environment compliant throughout its operational life.

**Scope:**
- Active research use of the environment
- Continuous monitoring and alerting
- Periodic compliance reviews (access reviews, risk reassessment, training renewal)
- Change management (new users, new data, infrastructure changes)
- Incident detection and response

**Key Activities:**
- **Daily:** Automated monitoring (GuardDuty, Macie, Config) with alert triage
- **Monthly:** Access review — verify all active access grants are still justified; revoke stale access
- **Quarterly:** Risk reassessment — review threat landscape, new vulnerabilities, control effectiveness
- **Annually:** Training renewal — all personnel re-complete HIPAA training; update training materials
- **As-needed:** Incident response — investigate alerts, contain breaches, notify per policy
- **As-needed:** Change management — new personnel onboarding (training, access request, approval), departures (access revocation), infrastructure changes (security review)

**Deliverables (ongoing):**
- Monthly access review reports
- Quarterly risk reassessment updates
- Annual training renewal records
- Incident reports (if any)
- Change management records (onboarding/offboarding, infrastructure changes)
- Continuous compliance dashboard (Config rules, Security Hub score)

**Exit Gate:** None — this phase continues until a decommission decision is made. Triggered reviews occur on schedule or in response to incidents.

---

#### Phase 6: Decommission (Days D+0 through D+5)

**Purpose:** Shut down the environment in a controlled, compliant manner — ensuring all PHI is destroyed or returned, all access is revoked, and a final audit trail documents the closure.

**Rationale:** HIPAA requires that PHI be properly disposed of when no longer needed. Simply deleting an AWS account is not sufficient — there must be documented evidence of data disposition, key destruction, and access revocation. The decommission phase is as much a compliance event as the build-up.

**Scope:**
- Formal decommission decision and stakeholder notification
- Access revocation for all users and service accounts
- Data disposition: destruction or return of all PHI per retention policy and BAA terms
- Encryption key destruction: schedule KMS CMK deletion (with mandatory waiting period)
- Infrastructure teardown: delete all resources, accounts, and configurations
- Final audit: export all logs, produce closure report, archive compliance evidence

**Key Activities:**
- Decommission decision: sponsor formally decides to end the project; document rationale
- Notification: inform all users, business associates, and stakeholders of shutdown timeline
- Access revocation: disable all user accounts; revoke all IAM roles; disable API keys
- System freeze: set environment to read-only; prevent new data creation
- Data inventory: confirm all locations where PHI resides (databases, S3, backups, logs)
- Data destruction: delete PHI from all locations; for S3, ensure versioned objects and delete markers are purged
- Destruction certification: document what was destroyed, when, by whom, method used
- Key destruction: schedule KMS CMK deletion (7–30 day waiting period); document key IDs and schedule
- Log export: export CloudTrail, CloudWatch, application logs to long-term archive (separate from destroyed environment)
- Infrastructure teardown: delete CloudFormation stacks / Terraform destroy; verify no orphaned resources
- Final compliance report: summarize project lifecycle, compliance posture, any incidents, lessons learned
- Archive: store all compliance documentation per retention policy (typically 6–7 years for HIPAA)

**Deliverables:**
- Decommission decision memo (signed by sponsor)
- Access revocation confirmation (all accounts disabled/deleted)
- Data destruction certification (inventory of destroyed data, methods, dates, responsible party)
- KMS key deletion schedule confirmation
- Final audit log archive (stored in separate, retained location)
- Final compliance/closure report
- Archived documentation package (retained per policy)

**Exit Gate:** Final compliance report accepted by sponsor; all PHI confirmed destroyed or returned; audit archive secured for retention period.

**Timing note:** The "D+" numbering is independent of the build-up day sequence. Decommission occurs whenever the project ends — could be months or years after Day 25. The D+0 through D+5 sequence represents approximately one week of focused shutdown activity, though the KMS key deletion waiting period extends the true completion by 7–30 additional calendar days.

### Gate Checkpoints

Gates enforce that organizational prerequisites are met before technical work proceeds. See `GATES.md` for full gate definitions, evidence requirements, and sequencing.

### Day Sequence (to be elaborated)

Each day will be documented with:
- **Day number and title**
- **Phase membership**
- **Objective**: What is accomplished
- **Deliverables**: Tangible outputs (documents, configurations, sign-offs)
- **Dependencies**: What must be complete before this day can start
- **Estimated effort**: Approximate hours of active work
- **Roles involved**: Who participates

#### Phase 0: Authorization
- **Day 0** — Project kickoff: charter drafted, sponsor identified
- **Day 1** — Roles and responsibilities assigned; governance model confirmed
- **Day 2** — Charter signed; project formally authorized *(Gate G1)*

#### Phase 1: Foundation
- **Day 3** — Risk assessment initiated (asset inventory, threat modeling)
- **Day 4** — Policies drafted (access control, data handling, incident response, sanctions)
- **Day 5** — HIPAA training delivered to all project personnel
- **Day 6** — Training completion documented *(Gate G3)*
- **Day 7** — Business Associate Agreements drafted and executed *(Gate G4)*
- **Day 8** — Risk assessment finalized and accepted *(Gate G2)*

#### Phase 2: Infrastructure
- **Day 9** — AWS account structure and Organization setup
- **Day 10** — Networking: VPC, subnets, security groups, NACLs
- **Day 11** — Identity: IAM roles, SSO federation, MFA enforcement
- **Day 12** — Encryption: KMS keys, key policies, rotation schedules
- **Day 13** — Compute and storage: RDS, S3, EC2 with encryption at rest
- **Day 14** — Monitoring: CloudTrail, CloudWatch, GuardDuty, Macie, Config
- **Day 15** — Security validation and remediation *(Gate G5)*

#### Phase 3: Data & Access
- **Day 16** — Synthetic PHI data generation and loading
- **Day 17** — Database views and row-level security for minimum-necessary
- **Day 18** — Access provisioning per approved roles
- **Day 19** — Access control testing (positive and negative cases)
- **Day 20** — Access audit review and documentation

#### Phase 4: Validation
- **Day 21** — End-to-end workflow testing (researcher data access scenarios)
- **Day 22** — Penetration testing / vulnerability scanning
- **Day 23** — Audit dry-run: simulate compliance review
- **Day 24** — Compliance officer review and system authorization *(Gate G6)*

#### Phase 5: Operations
- **Day 25+** — Active research begins
- Ongoing: Monthly access reviews, quarterly risk reassessment, annual training renewal
- Incident response as needed

#### Phase 6: Decommission
- **Day D+0** — Decommission decision and notification
- **Day D+1** — Access revocation for all users; system set to read-only
- **Day D+2** — Data disposition: PHI destroyed per retention policy; destruction certified
- **Day D+3** — Encryption key destruction (KMS key scheduling)
- **Day D+4** — Infrastructure teardown; final audit log export
- **Day D+5** — Final compliance report; project closure documentation archived

### Notes

- The day count (~25 days to active research) reflects a **well-prepared, small-team project**. Real-world timelines for larger organizations or multi-site studies can be 3–6 months of calendar time.
- Phase 1 (Foundation) deliberately precedes Phase 2 (Infrastructure) to reinforce that organizational controls come first. This is intentional and reflects the 80/20 organizational-to-technical ratio.
- The Decommission phase uses a separate "D+" numbering to indicate it occurs at project end, independent of the build-up sequence.

---

## Pre-Existing Conditions (Day 0 Assumptions)

The following are established institutional facts that exist before the project begins. They are not deliverables of this project — they are preconditions that enable it.

| Condition | Detail |
|-----------|--------|
| **UW–AWS BAA** | A Business Associate Agreement exists between UW and AWS. This BAA covers HIPAA-eligible AWS services (S3, RDS, EC2, KMS, CloudTrail, Bedrock, SageMaker, Comprehend Medical, etc.) when configured per AWS HIPAA guidance. This is an institutional agreement, not project-specific. |
| **NIH Funding** | The project has an active NIH award. The PI (sponsor) has authority to expend funds and accept risk within the scope of the award. Co-PI at FH receives salary support from the award. |
| **Department Approval** | The PI's department has approved the project scope, including cloud infrastructure and PHI handling. |
| **IRB Approval of UW–FH Relationship** | UW IRB reviewed and approved the collaboration with FH as part of the proposal submission process. The Co-PI's involvement is sanctioned. |
| **UW CISO** | UW has a Chief Information Security Officer who provides institutional-level security oversight. No dedicated HIPAA Privacy Officer exists at the institutional level — the project designates the PI for this role. |
| **UW IT AWS Account Management** | UW IT manages the organizational AWS infrastructure under which the BAA operates. This project obtains all AWS accounts from UW IT — accounts are not self-provisioned. This is an external dependency for Phase 2. |
| **Institutional Identity Infrastructure** | UW provides identity services (SSO, MFA) that can be federated into AWS. |

### Implications of the UW–AWS BAA

The BAA does not make AWS services automatically compliant. It means:
- AWS *agrees* to handle PHI according to HIPAA requirements on covered services
- The *customer* (UW/this project) is responsible for configuring services correctly
- Only services explicitly listed in the BAA are covered (see [AWS HIPAA Eligible Services](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/))
- The project must verify that every service used is on the eligible list and configured per AWS security best practices
- AWS will not use customer data (including Bedrock inputs/outputs) for model training — this must be documented as verified

---

## Technical Architecture

> The full technical architecture (AWS services registry, researcher environment model, network design, AI gatekeeper, upload path security) has been moved to `ARCHITECTURE.md` to keep this document focused on project governance, phases, and compliance framework.

---

## Project Scenario Summary

| Element | Detail |
|---------|--------|
| **PI / Sponsor / Privacy Officer** | Single individual at UW; holds NIH funding; accepts risk; designated HIPAA Privacy Officer for the project |
| **Institution (data source)** | UW — provides EHR data from institutional clinical database |
| **Collaborator institution** | FH (healthcare facility) — Co-PI, named on NIH award, receives salary support |
| **Data flow** | UW IT extracts raw PHI from clinical DB → uploads to AWS S3 (landing zone) → processed/derived data stored on AWS |
| **Data classification** | Raw PHI — full HIPAA identifiers present; highest sensitivity; full Security Rule applies |
| **Patient cohort** | N = 10,000 patients |
| **Research type** | EHR-based study; details TBD (kept abstract/synthetic) |
| **Access model** | All work performed within AWS environment; no data download to local systems |
| **Compute environment** | Cloud-hosted IDE (Kiro or equivalent VS Code Server-based environment) + Jupyter/notebook environment, running on EC2 within VPC |
| **AI tooling** | AI-augmented IDE + Bedrock for LLM capabilities; Comprehend Medical as PHI gatekeeper |
| **Collaborator access** | FH Co-PI connects remotely to the AWS environment; no PHI egress to FH systems |
| **HIPAA training** | Purchased as a service (CITI Program or equivalent); supplemented with project-specific AI/PHI briefing |

### Team Composition (at project start)

| Person | Institution | Project Role | HIPAA Role |
|--------|-------------|--------------|------------|
| PI | UW | Principal Investigator, project sponsor | Privacy Officer, Security Officer (project-level), risk acceptor |
| Co-PI | FH | Co-Investigator, co-analyst | Authorized user; subject to UW policies via sub-award |
| Student 1 | UW | Research analyst | Authorized user (minimum-necessary access) |
| Student 2 | UW | Research analyst | Authorized user (minimum-necessary access) |
| Student 3 | UW | Research analyst | Authorized user (minimum-necessary access) |
| Postdoc | UW | Senior research analyst | Authorized user; may serve as deputy for operational decisions |
| IT Staff | UW (departmental) | System administrator, data custodian | Technical safeguard implementer; data upload/extraction |

**Total: 7 people.** Team may change during the Period of Performance — onboarding/offboarding procedures (training, access provisioning/revocation) apply.

### Role Assignment Notes

- **PI as Privacy Officer:** The PI wears multiple hats. In a small research lab this is common and acceptable, but creates a concentration of authority. Mitigation: the postdoc or a student can serve as a check on access decisions; UW CISO provides institutional oversight.
- **No dedicated Security Officer at project level:** The UW CISO fills this role at the institutional level. The PI + IT staff share project-level security responsibilities. The IT staff person is the hands-on implementer; the PI is the decision-maker.
- **Co-PI at FH:** Governed by the sub-award agreement between UW and FH. The sub-award must include data access provisions equivalent to a BAA (or reference the IRB-approved protocol). FH Co-PI is subject to UW's project policies while working in the environment.
- **Students:** Require HIPAA training before any access. If students rotate in/out during the PoP, each new student must complete training and have access formally provisioned (documented justification, PI approval) before touching the environment.
- **IT Staff:** Has elevated technical access (admin-level) but should *not* have routine access to PHI content. Their role is infrastructure, not research. Access controls should reflect this separation.

### Governance Model

| Decision | Authority | Approval Chain |
|----------|-----------|----------------|
| Risk acceptance | PI (sponsor) | PI decides; documents rationale |
| Access grant (new user) | PI (Privacy Officer) | User requests → PI approves → IT provisions → logged |
| Access revocation | PI or IT Staff | PI decides or IT detects departure → IT revokes → logged |
| Policy changes | PI | PI drafts → team review → PI approves → documented |
| Incident response | PI + IT Staff | IT detects → PI decides severity → response per policy |
| Infrastructure changes | IT Staff | IT proposes → PI approves → IT implements → logged |
| Budget/procurement | PI | PI decides within NIH award scope |
| Escalation (institutional) | UW CISO | PI escalates to CISO for institutional-level issues |

### HIPAA Training Approach

> **Cost Management:** See the dedicated Cost Management section below and `ARCHITECTURE.md` for detailed service-level cost estimates. Key principle: cloud infrastructure can be stopped when not in use. Unlike on-premises hardware, you pay only for what's running. The project uses auto-start/stop scheduling, idle timeouts, and the ability to fully hibernate the environment during extended periods of inactivity (conferences, breaks, between grant periods).

| Component | Source | Covers |
|-----------|--------|--------|
| **Core HIPAA training** | Purchased service (CITI Program or equivalent) | Privacy Rule, Security Rule, Breach Notification, researcher responsibilities, minimum necessary principle |
| **Project-specific supplement** | Developed internally (PI + this documentation) | AI use policies, prompt hygiene, environment-specific procedures, gatekeeper workflow, PHI-in-code awareness |
| **Tracking** | Completion certificates from training provider + signed acknowledgment of project supplement | Gate G3 evidence |
| **Renewal** | Annual re-completion of core training; project supplement updated as policies evolve |
| **New personnel** | Must complete both components before any environment access is provisioned |


---

## To Do List

### Immediate (Phase 0 Completion)
- [x] **Q4:** FH collaborator relationship — Co-PI on NIH award, salary support, IRB-approved. ✓
- [x] **Q5:** Team composition — PI, Co-PI (FH), 3 students, 1 postdoc, 1 IT staff (7 total). ✓
- [x] **Q6:** Institutional infrastructure — CISO (no Privacy Officer), UW IT manages AWS accounts under BAA. ✓
- [x] **Q11:** HIPAA training — purchase as service (CITI or equivalent); supplement with project-specific AI/PHI briefing. ✓
- [x] **Q8:** Data preparation level — raw PHI (full identifiers). ✓
- [x] Draft Phase 0 project charter document → See `PHASE0_CHARTER.md`
- [x] Document raw PHI upload path security design → See `ARCHITECTURE.md`
- [x] **Risk assessment accepted by Dr. D.R. Smith (PI)** — Gate G2 satisfied.
- [ ] Determine agreement type between UW and FH for data access → See **External Questions** below.

### External Questions
- [ ] UW SOC / incident response team?
- [ ] UW IT / UW Med ITS health IT security function?
- [ ] Severity levels and escalation thresholds?
- [ ] CISO engagement threshold?
- [ ] Legal/compliance office for HHS breach notification?
- [ ] Institutional incident reporting mechanism?
- [ ] Student conduct / research integrity process for HIPAA violations?
- [ ] UW–FH sub-award status and PHI access language?
- [ ] CITI Program institutional subscription? **Unclosed — required for Gate G3.**

### Design & Architecture
- [x] AWS Services Registry → `ARCHITECTURE.md` ✓
- [x] Researcher Environment Model → `ARCHITECTURE.md` ✓
- [ ] Comprehend Medical gatekeeper detailed design
- [ ] Research environment compute architecture (EC2 sizing, IDE deployment)
- [ ] AWS account request process (UW IT dependency)
- [ ] EFS access control design (POSIX mapping)

### Black Hat Test (Phase 4)
- [ ] Design breach simulation: (a) trusted insider permitted access, (b) unauthorized access attempt
- [ ] Demonstrate detection, logging, alerting, and incident response workflow

### Future Items
- [ ] Phase 2 IaC skeleton (Terraform/CloudFormation)
- [ ] Synthetic PHI data generation strategy (10,000 patients)
- [ ] Decommission procedures (KMS key deletion, S3 purge)
- [ ] HIPAA training vendor procurement
- [ ] GitHub repo structure design
- [ ] Container CI/CD pipeline (GitHub Actions → ECR → ECS)
- [ ] Verify Kiro AI backend and BAA coverage
- [ ] Agent audit layer design
- [ ] Agent IAM role scoping
- [ ] **IaC: Zero-console infrastructure build** (OpenTofu/Terraform) → `ARCHITECTURE.md`
- [ ] **Synthetic PHI isolation** (separate repo; dogfood upload path)
- [ ] **End-to-end Docker container pipeline demo:** Fully functional proof-of-concept. `Dockerfile` + `app.py` + `requirements.txt` in `securecomputing-datagen` → GitHub Actions builds image → pushes to ECR → ECS/Fargate runs container in the project environment. Demonstrates full CI/CD path from code to running container within the compliant infrastructure.
- [ ] **SageMaker lifecycle configuration:** Build the shell script (in `securecomputing` repo) that installs project libraries (NetworkX, pandas, scikit-learn, etc.) at notebook instance creation. Store in repo, reference in CDK stack. Test that a fresh SageMaker instance comes up with the full research environment ready.
- [ ] **Book assembly:** Evaluate tooling for stapling project Markdown files into a single document (PDF or HTML book). See note in PO.md.
- [x] **Split PO.md** → `ARCHITECTURE.md` created ✓
- [ ] **Reproducibility / "How to Construct":** AI-guided build from this repo's documentation
- [ ] **Synthea Docker image:** Build a Synthea CSV-export Docker image (Java 17 + Synthea + CSV-configured properties) and push to Docker Hub with discoverable tags. Eliminates the Java/Gradle/WSL installation challenges for future users. Should also include the ETL-Synthea-Python tool with pandas 2.x compatibility patches pre-applied (the upstream repo uses deprecated `DataFrame.append()` which fails on modern pandas).
- [ ] **Validation meta-task:** The synthetic system has an "answer key" (`patient_stones.csv`) that a real research program would not have. Design a validation exercise where derived results (from analyzing PD1 PXRD/FTIR data, PD2 genomics, PD3 lab correlations) are checked against the answer key. This tests the analysis pipeline's correctness — but note that this luxury does not exist in real research. Document this distinction as a teaching point about the difference between synthetic system validation and real-world discovery.
