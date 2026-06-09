\newpage

<!-- SOURCE: GATES.md -->

# Gate Registry

## What is a Gate?

A Gate is a mandatory checkpoint in the project lifecycle. It represents a point where specific deliverables must exist and be accepted before subsequent work can proceed. Gates enforce the principle that organizational authority precedes organizational controls, which precede technical implementation, which precedes data handling.

Each gate is expressed in terms of **what its completion enables** — the work that becomes possible once the gate is satisfied.

---

## Gate Summary

| Gate | Condition | Enables |
|------|-----------|---------|
| **G1** | Project charter signed; roles assigned and accepted | All project work (Phase 1 and beyond) |
| **G2** | Risk assessment documented and accepted by sponsor | Infrastructure provisioning (Phase 2); security controls are built to address identified risks |
| **G3** | All personnel HIPAA-trained with documented evidence | Access to PHI (even synthetic); use of the research environment |
| **G4** | BAAs/agreements executed with all third parties | Third-party integrations; Co-PI access from FH; use of any external service handling PHI |
| **G5** | Infrastructure security validated; audit logging confirmed | Data loading; access provisioning; any PHI entering the environment |
| **G6** | Compliance officer review complete; system authorized | Active research use; researchers working with PHI in the environment |

---

## Gate Details

### G1: Authorization to Proceed

**Phase:** Phase 0 (Authorization)

**Condition:** Project charter signed by sponsor (PI); all roles assigned to named individuals who have accepted their responsibilities.

**Evidence required:**
- Signed project charter (`PHASE0_CHARTER.md`)
- Role assignment matrix with named individuals
- Governance model documented (decision authority, escalation paths)

**Enables:**
- Phase 1 activities: policy development, risk assessment, training procurement, BAA negotiation
- Establishment of the compliance documentation repository
- Budget expenditure for training, infrastructure, and services
- Formal communication with UW IT regarding AWS account provisioning

**Rationale:** Without G1, no one has authority to make decisions, accept risk, or commit resources. All subsequent work requires someone accountable.

---

### G2: Risk Assessment Accepted

**Phase:** Phase 1 (Foundation)

**Condition:** Risk assessment is complete — assets inventoried, threats identified, risks scored, mitigations defined, residual risk documented — and the sponsor (PI) has formally accepted the residual risk.

**Evidence required:**
- Completed risk assessment document
- Asset inventory (systems, data stores, data flows)
- Threat model (threats, vulnerabilities, likelihood, impact)
- Risk scoring matrix
- Mitigation plan for each identified risk
- Sponsor signature accepting residual risk

**Enables:**
- Infrastructure provisioning (Phase 2) — because infrastructure is built to address the risks identified here
- Security control selection — controls are justified by risk findings ("we encrypt because Risk RA-12 identified unencrypted storage as high-impact")
- Compliance evidence — auditors require documented risk assessment as the foundation of all security decisions

**Rationale:** Building infrastructure without a risk assessment means building without a specification. You cannot demonstrate that controls are "appropriate" (HIPAA's standard) without first documenting what they're appropriate *for*.

---

### G3: Workforce Trained

**Phase:** Phase 1 (Foundation)

**Condition:** All project personnel have completed HIPAA training and the project-specific AI/PHI supplement. Completion is documented with certificates and signed acknowledgments.

**Evidence required:**
- Training completion certificates (from CITI Program or equivalent) for each team member
- Signed acknowledgment of project-specific policies (AI use, prompt hygiene, incident reporting)
- Training roster: who, what, when, certificate ID
- Documentation that training covers: Privacy Rule, Security Rule, Breach Notification, minimum necessary, sanctions

**Enables:**
- Access to PHI (even synthetic) — no untrained person may interact with the research environment
- Use of AI tools within the environment (training covers AI-specific PHI risks)
- Onboarding of the team into the operational environment (Phase 3+)

**Rationale:** HIPAA requires documented workforce training before PHI access. An untrained researcher accessing PHI — even accidentally, even synthetic — is a compliance failure. The training also establishes that personnel understand the sanctions for non-compliance.

---

### G4: Agreements Executed

**Phase:** Phase 1 (Foundation)

**Condition:** All required agreements with third parties are drafted, negotiated, and executed (signed by authorized representatives on both sides).

**Evidence required:**
- UW–FH sub-award or data access agreement (covering Co-PI's access to PHI in UW's environment)
- Verification that UW–AWS BAA covers all services the project will use (documented checklist)
- Any additional vendor agreements if applicable (training provider, etc.)
- Signed copies of all agreements on file

**Enables:**
- Co-PI (FH) access to the research environment
- Use of AWS services for PHI processing (BAA coverage confirmed)
- Integration with any third-party services
- Compliance evidence that all PHI disclosures are governed by written agreements

**Rationale:** HIPAA prohibits disclosing PHI to a third party without a BAA or equivalent agreement. The Co-PI at FH accessing PHI in UW's environment constitutes a disclosure that must be governed by written terms.

---

### G5: Infrastructure Validated

**Phase:** Phase 2 (Infrastructure)

**Condition:** AWS infrastructure is deployed, security controls are implemented, and validation confirms that controls work as designed. All critical and high-severity findings from security validation are remediated. Audit logging is confirmed operational.

**Evidence required:**
- Deployed infrastructure (IaC templates versioned in repository)
- Security validation report (AWS Config conformance, Security Hub findings, manual review)
- Remediation log (findings identified, actions taken, residual items accepted)
- Audit logging confirmation: CloudTrail active (all regions), S3 access logging active, VPC Flow Logs active
- Network diagram with security boundaries
- IAM role mapping to organizational roles
- KMS key inventory with rotation schedule
- Gatekeeper service deployed and tested (Comprehend Medical integration)

**Enables:**
- Data loading (Phase 3) — PHI can now enter the environment because the environment is proven secure
- Access provisioning — user accounts can be created and roles assigned
- Research compute availability — IDE and notebook environments are ready for use
- AI tooling activation — gatekeeper is operational, Bedrock is accessible

**Rationale:** Loading PHI into an unvalidated environment is reckless. G5 ensures that every technical control is in place and working before any sensitive data enters the system. This is the "is the vault locked before we put valuables in it?" check.

---

### G6: System Authorized for Use

**Phase:** Phase 4 (Validation)

**Condition:** End-to-end testing is complete, security testing passes, the audit dry-run finds no critical gaps, and the compliance officer (PI, in this project) formally authorizes the system for research use.

**Evidence required:**
- End-to-end workflow test results (researcher scenarios executed successfully)
- Vulnerability scan report (no critical/high findings unresolved)
- Penetration test report (no exploitable vulnerabilities)
  - *Note: AWS Security Agent (preview 2025) may satisfy this requirement via automated, AI-driven pen testing with verified exploit paths. Evaluate availability and maturity when G6 is approached.*
- Black Hat Test results (breach detection demonstrated for both scenarios)
- Audit simulation findings (gaps identified and remediated)
- Incident response drill after-action report
- System authorization memo signed by PI (compliance officer role)

**Enables:**
- Active research (Phase 5) — researchers can begin their actual study work
- Full operational use of the environment with real (synthetic) PHI
- The system is "live" — monitoring, alerting, and incident response are in active mode

**Rationale:** G6 is the "dress rehearsal passed" gate. Individual components may work in isolation, but the system must work as a whole — including the human processes (incident response, access review) — before it's trusted with ongoing research use. This is analogous to a system Authority to Operate (ATO) in federal contexts.

---

## Gate Sequencing

```
G1 (Authorization)
 │
 ├── Enables: Phase 1 (Foundation)
 │
 ├── G2 (Risk Assessment) ──────┐
 ├── G3 (Training) ─────────────┤
 ├── G4 (Agreements) ───────────┤
 │                               │
 │                               ▼
 │                    G5 (Infrastructure Validated)
 │                               │
 │                               ▼
 │                    G6 (System Authorized)
 │                               │
 │                               ▼
 │                    Phase 5: Operations
 │
 └── All gates must be satisfied before Phase 5 begins
```

**Key dependency:** G2, G3, and G4 are all Phase 1 gates that can be worked in parallel. However, *all three* must be satisfied before G5 can be achieved (you need the risk assessment to validate infrastructure against, trained people to operate it, and agreements in place for third-party access).

---

## Gate Enforcement

Gates are enforced through:

1. **Documentation:** Each gate has defined evidence requirements. If the evidence doesn't exist, the gate isn't passed.
2. **Sign-off:** Gates requiring sponsor acceptance need a dated signature (physical or electronic).
3. **Technical controls:** Some gates have technical enforcement (e.g., IAM policies that prevent access provisioning until training records exist in the system — though this is aspirational for a small team).
4. **Audit trail:** Gate passage is logged: date satisfied, evidence location, who verified.

In practice for a small research team, gate enforcement is primarily documentation-based. The PI (wearing the compliance officer hat) verifies that evidence exists and records the gate passage date. For a larger organization, gates might be enforced by workflow systems or separate compliance staff.

---

*End of GATES.md — Next: PHASE0_CHARTER.md*
