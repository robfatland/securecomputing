\newpage

<!-- SOURCE: PHASE0_CHARTER.md -->

# Phase 0 Deliverable: Project Charter

> [!] **TEMPLATE:** This charter is a demonstrator example built for a synthetic PHI project. You are responsible for modifying this to be accurate to your program. Replace all bracketed placeholders with institution-specific details. Sections marked with [i] use generic language that must be replaced with verified, institution-specific content.

## Document Status

| Field | Value |
|-------|-------|
| **Document ID** | CHARTER-001 |
| **Version** | 1.0 (Draft) |
| **Date** | [Date of signing] |
| **Status** | Draft — pending sponsor signature |
| **Gate** | G1 — this document, when signed, satisfies Gate G1 |

---

## 1. Project Identification

| Field | Value |
|-------|-------|
| **Project Title** | Synthetic PHI Research Environment on AWS |
| **Sponsor / PI** | Dr. D.R. Smith, UW |
| **Co-PI** | [Co-PI Name], FH |
| **Funding Source** | NIH Award [Award Number] |
| **Period of Performance** | [Start Date] – [End Date] |
| **Department** | [Department], UW |

---

## 2. Purpose and Scope

### Purpose

Establish a HIPAA-compliant cloud-based research environment on AWS for conducting an EHR-based study involving 10,000 patients. The environment will serve as both a functional research platform and a demonstrator system — built to the highest compliance standard so that subsequent real-world projects can inherit the framework without discovering gaps.

### Scope

This project encompasses:

- **Organizational controls:** Policies, training, role definitions, risk assessment, incident response procedures, Business Associate oversight, AI use governance
- **Technical controls:** AWS infrastructure with encryption, access controls, network segmentation, audit logging, monitoring, and AI prompt gatekeeping
- **Data handling:** Receipt of raw PHI from UW clinical database, secure storage, controlled access, and eventual disposition
- **Research operations:** EHR data analysis using notebook environments and AI-augmented IDEs within the secured environment
- **Full lifecycle:** From authorization through active research to controlled decommission

### Out of Scope

- Actual clinical care delivery
- Modification of source clinical systems at UW
- Infrastructure at FH (all work occurs in UW's AWS environment)
- Development of HIPAA training curriculum (purchased as a service)

---

## 3. Data Classification

| Attribute | Value |
|-----------|-------|
| **Data type** | Electronic Protected Health Information (ePHI) |
| **Sensitivity level** | Raw PHI — full identifiers (names, MRNs, DOBs, addresses, etc.) |
| **Source** | UW institutional clinical database |
| **Volume** | 10,000 patient records |
| **HIPAA applicability** | Full — Privacy Rule, Security Rule, Breach Notification Rule all apply |
| **Regulatory framework** | HIPAA + NIST SP 800-66 (implementation guidance) + NIST CSF 2.0 |

### HIPAA Identifiers Present

The raw PHI upload will contain some or all of the 18 HIPAA identifiers:

1. Names
2. Geographic data (address, city, state, zip)
3. Dates (birth, admission, discharge, death)
4. Phone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers (MRNs)
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers
13. Device identifiers
14. Web URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photographs
18. Any other unique identifying number

**Note:** Not all 18 will necessarily be present in every record, but the system is designed to handle the full set. Security controls assume worst-case (all identifiers present).

---

## 4. Team and Role Assignments

### Personnel

| Person | Institution | Project Role | HIPAA Role |
|--------|-------------|--------------|------------|
| PI | UW | Principal Investigator, sponsor | Privacy Officer, Security Officer (project-level), risk acceptor |
| Co-PI | FH | Co-Investigator, co-analyst | Authorized user; subject to UW project policies via sub-award |
| Student 1 | UW | Research analyst | Authorized user (minimum-necessary access) |
| Student 2 | UW | Research analyst | Authorized user (minimum-necessary access) |
| Student 3 | UW | Research analyst | Authorized user (minimum-necessary access) |
| Postdoc | UW | Senior research analyst | Authorized user; deputy for operational decisions |
| IT Staff | UW (dept.) | System administrator, data custodian | Technical safeguard implementer; data upload/extraction |

### HIPAA Role Definitions

| HIPAA Role | Responsibility | Held By |
|------------|---------------|---------|
| **Privacy Officer** | Oversees PHI use/disclosure decisions; enforces minimum-necessary; handles privacy complaints; manages breach notification | PI |
| **Security Officer (project-level)** | Ensures technical and administrative safeguards are implemented and maintained; conducts risk assessments; manages security incidents | PI (decisions) + IT Staff (implementation) |
| **Data Custodian** | Responsible for the physical/technical custody of PHI; manages storage, backups, encryption, access provisioning | IT Staff |
| **Authorized Users** | Access PHI only as approved, only for authorized purposes, only after training; report incidents | Co-PI, Students, Postdoc |

### Concentration of Authority

The PI holds multiple roles (sponsor, Privacy Officer, Security Officer). This is acceptable for a small research team but creates risk:
- **Mitigation 1:** Postdoc serves as deputy and operational check
- **Mitigation 2:** UW CISO provides institutional-level oversight and escalation path
- **Mitigation 3:** All decisions are documented (audit trail prevents unaccountable action)

---

## 5. Governance Model

### Decision Authority

| Decision Type | Authority | Process |
|---------------|-----------|---------|
| Risk acceptance | PI | PI evaluates risk; documents rationale; signs off |
| Access grant (new user) | PI (Privacy Officer) | User requests → PI verifies training + justification → IT provisions → logged |
| Access revocation | PI or IT Staff | PI decides or IT detects departure → IT revokes → logged |
| Policy creation/change | PI | PI drafts → team review → PI approves → version-controlled |
| Incident response | PI + IT Staff | IT detects → PI assesses severity → response per incident policy |
| Infrastructure changes | IT Staff + PI | IT proposes → PI approves → IT implements → change logged |
| Budget/procurement | PI | PI decides within NIH award scope |
| Escalation | UW CISO | PI escalates institutional-level security issues to CISO |

> [i] **GENERIC:** The incident response and escalation rows above use simplified language. Your version must specify: institutional SOC contact information, severity classification thresholds, CISO engagement criteria, and the legal/compliance office responsible for HHS breach notification. See External Questions in PROJECT_OVERVIEW.md.

### Approval Chain for PHI Access

```
1. Individual completes HIPAA training (documented)
2. Individual submits access request with justification (minimum-necessary basis)
3. PI (Privacy Officer) reviews and approves/denies
4. IT Staff provisions access per approved scope
5. Access grant logged with: who, what, why, when, approved-by
6. Periodic review: PI reviews all active grants monthly
```

---

## 6. Pre-Existing Conditions

The following institutional facts are established before this project begins and are not deliverables of this charter:

| Condition | Status | Implication |
|-----------|--------|-------------|
| UW–AWS BAA | Active | HIPAA-eligible AWS services are covered when correctly configured |
| NIH Award | Active | Funding and authority to proceed; Co-PI salary support included |
| Department Approval | Granted | Scope approved including cloud infrastructure and PHI handling |
| IRB Approval (UW–FH relationship) | Granted at proposal | Collaboration sanctioned; protocol approved for human subjects research |
| UW CISO | Exists | Institutional security oversight available; escalation path defined |
| UW IT AWS Account Management | Active | Project obtains AWS accounts from UW IT (external dependency) |
| UW Identity Infrastructure | Active | SSO and MFA available for federation into AWS |

---

## 7. AI Use Posture

This project treats AI as an essential research tool subject to full HIPAA governance.

### Permitted AI Use

| AI Service | Permitted? | Conditions |
|------------|-----------|------------|
| Kiro / VS Code Server (within VPC) | Yes | Comprehend Medical gatekeeper screens all outbound prompts |
| Amazon Bedrock (within AWS, BAA-covered) | Yes | No-training opt-out verified and documented; all prompts logged |
| Amazon Comprehend Medical | Yes | Used as PHI detection layer in gatekeeper service |
| Notebook AI features (within VPC) | Yes | Routed through gatekeeper; Bedrock backend only |
| External LLMs (ChatGPT, Claude web, etc.) | **No** | Prohibited for any PHI-related work; blocked at network level |

### AI Governance Commitments

1. All AI prompts from the research environment pass through the Comprehend Medical gatekeeper
2. AWS Bedrock no-training guarantee is verified and documented as compliance evidence
3. External AI services are blocked at the network level (not just by policy)
4. AI-related PHI incidents are classified and reported per incident response policy
5. Training includes AI-specific PHI awareness (error messages, variable names, query results)

---

## 8. Key Dependencies and Risks

| Dependency/Risk | Impact | Mitigation |
|-----------------|--------|------------|
| AWS account provisioning from UW IT | Blocks Phase 2 start | Request early; begin Phase 1 (organizational) in parallel |
| HIPAA training procurement | Blocks Gate G3 | Identify vendor (CITI) early; confirm UW subscription or budget |
| UW–FH sub-award data access terms | Blocks Co-PI access | Confirm sub-award language covers PHI access in UW environment |

> [!] **TEMPLATE:** The PI is responsible for spelling out the Co-Investigator relationship and establishing the PHI access agreement. This involves confirming that the sub-award (or a separate DUA/amendment) explicitly authorizes the Co-PI to access raw PHI within the UW AWS environment, and that FH's institutional obligations are documented. Contact your Office of Sponsored Programs or institutional legal counsel.
| Team changes during PoP | Onboarding/offboarding overhead | Documented procedures; training prerequisite enforced |
| AI service availability/changes | Gatekeeper design may need updates | Design for modularity; abstract AI backend |
| Comprehend Medical detection limits | May miss non-standard PHI patterns | Supplement with regex patterns for known formats (MRN patterns, etc.) |

---

## 9. Success Criteria

This project is successful when:

1. A fully functional, HIPAA-compliant research environment exists on AWS
2. All team members are trained and can access data appropriate to their role
3. The system demonstrably detects and prevents unauthorized access (Black Hat Test passes)
4. The AI gatekeeper prevents PHI leakage to AI services while enabling productive AI use
5. Complete compliance documentation exists (policies, training records, risk assessment, audit logs)
6. The framework is reusable — a subsequent real project can adopt it without discovering gaps
7. The system can be cleanly decommissioned with documented data disposition

---

## 10. Authorization

By signing below, the sponsor authorizes the project to proceed through the Day Framework lifecycle, committing to the governance model, role assignments, and compliance obligations described in this charter.

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Sponsor / PI** | Dr. D.R. Smith | _________________ | ________ |
| **Co-PI** | [Co-PI Name] | _________________ | ________ |
| **IT Staff** | [IT Staff Name] | _________________ | ________ |

**Upon signature, Gate G1 is satisfied and Phase 1 may begin.**

---

*End of PHASE0_CHARTER.md — Next: RISK_ASSESSMENT.md*
