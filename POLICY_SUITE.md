\newpage

<!-- SOURCE: POLICY_SUITE.md -->

# Policy Suite: HIPAA Security Rule Compliance

> ⚠️ **TEMPLATE:** These policy outlines are demonstrator templates. Each policy below provides structure, required sections, and example language. You are responsible for modifying every policy to be accurate to your program. Your actual versions must be considerably more detailed and specific, reviewed by legal counsel, and approved by your designated Privacy/Security Officer.

> For a fully-realized example of what a complete policy looks like, see `POLICY_AI_ACCEPTABLE_USE.md` — that document demonstrates the level of specificity, detail, and operational guidance that each policy below should ultimately achieve.

---

## Policy Index

| Policy ID | Title | HIPAA Basis | Status |
|-----------|-------|-------------|--------|
| POL-AC-001 | Access Control | §164.312(a)(1) | Template |
| POL-DH-001 | Data Handling and Storage | §164.312(c)(1), §164.312(e)(1) | Template |
| POL-IR-001 | Incident Response and Breach Notification | §164.308(a)(6), §164.404 | Template |
| POL-SN-001 | Sanctions | §164.308(a)(1)(ii)(C) | Template |
| POL-WS-001 | Workforce Security | §164.308(a)(3) | Template |
| POL-MD-001 | Media Disposal and Data Disposition | §164.310(d)(2) | Template |
| POL-AI-001 | AI Acceptable Use | §164.308(a)(4), §164.312(a)(1) | **Complete** — see separate document |

---

## POL-AC-001: Access Control Policy

### Purpose
Define who may access PHI, under what conditions, through what mechanisms, and how access is granted, reviewed, and revoked.

### Required Sections

1. **Scope** — Who this policy applies to; what systems are covered
2. **Access Principles**
   - Minimum necessary: access limited to what is needed for assigned role
   - Role-based: access determined by project role, not individual identity
   - Time-limited: access granted for defined periods; reviewed periodically
3. **Access Request Process**
   - How to request access (form, approval chain)
   - Justification requirements (why this access, for what purpose, for how long)
   - Who approves (Privacy Officer / PI)
4. **Access Provisioning**
   - Technical implementation (IAM roles, database views, EFS permissions)
   - Documentation requirements (logged: who, what, why, when, approved-by)
5. **Access Review**
   - Frequency (monthly)
   - Process (PI reviews all active grants; verifies continued justification)
   - Action on unjustified access (immediate revocation)
6. **Access Revocation**
   - Triggers (departure, role change, project completion, violation)
   - Timeline (within 24 hours of trigger)
   - Process (IT staff executes; PI confirms; logged)
7. **Emergency Access**
   - Break-glass procedure for urgent situations
   - Post-hoc documentation and review requirements
8. **Audit**
   - All access grants/revocations logged
   - Access attempts (successful and failed) logged via CloudTrail
   - Monthly review of access logs for anomalies

> 📋 **GENERIC:** This outline must be populated with your specific role definitions, approval workflows, review schedules, and technical implementation details. Reference your IAM role mapping document and database view definitions.

---

## POL-DH-001: Data Handling and Storage Policy

### Purpose
Define how PHI is stored, transmitted, processed, and protected throughout its lifecycle in the research environment.

### Required Sections

1. **Data Classification**
   - Raw PHI (full identifiers) — highest sensitivity
   - Derived data (may contain PHI) — high sensitivity
   - De-identified data (Safe Harbor compliant) — standard sensitivity
   - Code and configuration (no PHI) — standard
2. **Storage Requirements**
   - Encryption at rest: all PHI encrypted with KMS (CMK per classification)
   - Storage locations: only approved services (S3, RDS, EFS)
   - No PHI on laptops, personal devices, external drives, or unapproved services
3. **Transmission Requirements**
   - Encryption in transit: TLS 1.2+ for all data movement
   - Approved transmission paths (UW IT → S3; internal service-to-service)
   - Prohibited paths (email, Slack, personal cloud storage, external AI)
4. **Processing Requirements**
   - PHI processed only within VPC (private subnets)
   - No PHI in container images, git repositories, or CI/CD artifacts
   - Notebook outputs containing PHI must not leave the environment
5. **Data Retention**
   - Retention periods by classification
   - Backup schedules and retention
   - Relationship to research data management plan (NIH requirement)
6. **Data Disposition**
   - Destruction methods by storage type (S3 purge, RDS deletion, EFS wipe, KMS key destruction)
   - Certification of destruction (who, what, when, method)
   - Reference to Decommission phase (Phase 6)
7. **Data Integrity**
   - Checksums on upload (SHA-256)
   - S3 versioning for change tracking
   - Database transaction logging
   - Backup verification procedures

> 📋 **GENERIC:** Populate with your specific KMS key IDs, S3 bucket names, retention periods, and destruction certification templates.

---

## POL-IR-001: Incident Response and Breach Notification Policy

### Purpose
Define how security incidents are detected, reported, investigated, contained, and reported to authorities when required.

### Required Sections

1. **Incident Definition**
   - What constitutes a security incident (unauthorized access, PHI disclosure, system compromise, policy violation)
   - Severity classification (Low / Medium / High / Critical)
2. **Detection**
   - Automated detection (GuardDuty, Macie, Config, gatekeeper alerts, CloudWatch alarms)
   - Human detection (user reports, audit review findings)
   - Reporting channels (how to report; Wickr, direct to PI, IT staff)
3. **Response Team**
   - Roles during incident (Incident Commander = PI; Technical Lead = IT staff)
   - Contact information and escalation path
   - External contacts (UW CISO, legal/compliance office, HHS)
4. **Response Procedures by Severity**
   - Low: log, investigate, remediate, document
   - Medium: contain, investigate, remediate, report to PI, document
   - High: contain immediately, notify PI + CISO, investigate, breach assessment, document
   - Critical: emergency containment (system isolation), notify PI + CISO + legal, full investigation
5. **Breach Assessment**
   - Four-factor analysis per §164.402 (nature of PHI, who received it, acquired/viewed, mitigation)
   - Determination: breach vs. non-breach
   - Documentation of assessment and rationale
6. **Breach Notification**
   - Individual notification (within 60 days of discovery)
   - HHS notification (within 60 days; immediate if 500+ individuals)
   - Media notification (if 500+ individuals in a state)
   - Content requirements for notification letters
7. **Post-Incident**
   - Root cause analysis
   - Remediation plan
   - Policy/control updates
   - Lessons learned documentation
   - Risk assessment update

> 📋 **GENERIC:** This policy must include your specific escalation contacts, institutional reporting mechanisms, and legal counsel information. See External Questions in PROJECT_OVERVIEW.md for items requiring institutional input.

---

## POL-SN-001: Sanctions Policy

### Purpose
Define consequences for violations of HIPAA policies and project security requirements. Required by §164.308(a)(1)(ii)(C).

### Required Sections

1. **Purpose and Scope**
   - Applies to all project personnel regardless of role
   - Covers violations of any project HIPAA policy
2. **Progressive Discipline Framework**
   - Level 1: Verbal counseling and retraining (first minor violation)
   - Level 2: Written warning with documented remediation plan (repeated minor or first moderate violation)
   - Level 3: Access suspension pending investigation (serious violation)
   - Level 4: Removal from project (repeated serious or any egregious violation)
   - Level 5: Institutional referral (criminal or willful violations)
3. **Violation Categories**
   - Minor: accidental, self-reported, no PHI actually compromised
   - Moderate: accidental but PHI was disclosed; or failure to follow procedures
   - Serious: negligent disregard for policy; failure to report known violation
   - Egregious: deliberate circumvention; malicious intent; repeated serious violations
4. **Mitigating Factors**
   - Self-reporting (reduces severity)
   - Good faith effort to comply
   - System failure vs. human failure
   - Cooperation with investigation
5. **Aggravating Factors**
   - Prior violations
   - Attempt to conceal
   - Volume of PHI involved
   - Deliberate intent
6. **Documentation**
   - All sanctions documented (who, what, when, sanction applied)
   - Maintained in personnel file for duration of project
   - Referenced in periodic access reviews
7. **No Retaliation**
   - Good-faith reporting protected
   - Retaliation for reporting is itself a sanctionable offense

> 📋 **GENERIC:** Replace with your institution's specific disciplinary procedures. Reference student conduct codes, employment policies, and any collective bargaining agreements that may apply. Consult HR and legal counsel.

---

## POL-WS-001: Workforce Security Policy

### Purpose
Ensure that all personnel with access to PHI are appropriate, trained, supervised, and managed throughout their involvement with the project.

### Required Sections

1. **Personnel Screening**
   - Background check requirements (if applicable per institutional policy)
   - Verification of role appropriateness
   - Conflict of interest disclosure
2. **Onboarding**
   - HIPAA training completion (Gate G3 prerequisite)
   - Policy acknowledgment signatures
   - Access request and provisioning process
   - Orientation to environment and tools
3. **Ongoing Supervision**
   - PI oversight of research activities
   - Monthly access reviews
   - Annual training renewal
   - Performance of duties consistent with role
4. **Role Changes**
   - Access adjustment when responsibilities change
   - Re-evaluation of minimum necessary
   - Documentation of role change and access modification
5. **Offboarding / Termination**
   - Immediate access revocation (within 24 hours)
   - Return/destruction of any project materials
   - Exit reminder of ongoing confidentiality obligations
   - Documentation of departure and access revocation
6. **Temporary Personnel**
   - Same requirements as permanent team members
   - Time-limited access with explicit expiration
   - Sponsor (PI) responsible for oversight

> 📋 **GENERIC:** Populate with your specific onboarding checklist, training requirements, background check policies, and offboarding procedures. Reference your institution's HR policies.

---

## POL-MD-001: Media Disposal and Data Disposition Policy

### Purpose
Define how storage media and data are securely disposed of when no longer needed, ensuring PHI cannot be recovered from decommissioned resources.

### Required Sections

1. **Scope**
   - Digital media: S3 objects, RDS databases, EFS files, EBS volumes, backups
   - Physical media: N/A for cloud-only environment (but note if any physical media exists)
   - Derived artifacts: container images, log files, temporary files
2. **Disposal Methods by Media Type**
   - S3: delete all objects + versions + delete markers; verify bucket empty; delete bucket
   - RDS: delete instance + automated backups; verify no snapshots remain
   - EFS: delete all files; delete filesystem
   - EBS: delete volumes; verify no snapshots
   - KMS: schedule key deletion (7-30 day waiting period); document key IDs
   - CloudWatch Logs: set retention policy; verify expiration
   - Backups: delete per retention schedule; verify no orphaned copies
3. **Verification**
   - Post-deletion verification (attempt to access; confirm failure)
   - Inventory reconciliation (all known PHI locations accounted for)
   - Certification document (who verified, when, what was checked)
4. **Certification of Destruction**
   - Template for destruction certification
   - Required fields: data description, location, method, date, responsible party, verifier
   - Retained as compliance evidence (7 years per HIPAA)
5. **Exceptions**
   - Audit logs: retained per retention policy even after data destruction
   - Research outputs (de-identified): may be retained per data management plan
   - Legal hold: if litigation or investigation pending, do not destroy
6. **Reference Standards**
   - NIST SP 800-88 (Guidelines for Media Sanitization)
   - AWS-specific guidance for cloud resource deletion

> 📋 **GENERIC:** Populate with your specific retention periods, destruction certification templates, and any institutional records management requirements. Coordinate with your institution's records office and legal counsel.

---

## Implementation Notes

### Policy Development Process

For each policy above:
1. Draft using this outline as structure
2. Populate with project-specific details (names, systems, procedures)
3. Review with team (all personnel should understand policies that apply to them)
4. Approve (PI signs as Privacy Officer)
5. Distribute and acknowledge (all personnel sign acknowledgment)
6. Store in compliance documentation repository
7. Review annually and after incidents

### Relationship to Risk Assessment

Each policy should trace to risk assessment findings:
- "This policy mitigates risks TA1-1, TA2-3, TA5-5 identified in RISK_ASSESSMENT.md"
- This traceability demonstrates to auditors that controls are risk-based, not arbitrary

### Relationship to Technical Controls

Each policy should reference the technical controls that enforce it:
- "This policy is enforced by IAM role [X], database view [Y], and monitored by CloudWatch alarm [Z]"
- Policies without technical enforcement rely solely on human compliance — identify these as higher risk
