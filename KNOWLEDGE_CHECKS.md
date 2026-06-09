\newpage

<!-- SOURCE: KNOWLEDGE_CHECKS.md -->

# Knowledge Checks: HIPAA Compliance & AWS Architecture

This document contains a series of knowledge checks organized by topic. Some have been answered, others are pending your review and responses.

**Instructions**: Read the project architecture documents carefully (PROJECT_OVERVIEW.md, ORGANIZATIONAL_STRUCTURE.md, ARCHITECTURE.md) before answering the pending questions. This ensures you have context and understand the integrated design.

---

## Section 1: Audit & Accountability (ANSWERED [x])

### Question 1.1: Separate Audit Account
**Q: Why is the audit log stored in a separate AWS account, and what threat does that prevent?**

**A: (Your Answer - CORRECT)**
The audit log records API calls to the research account. A bad actor with research account access could delete this record; so this is security via isolation.

**Deeper Context:**
- If audit logs are stored in the same account, an attacker with compromised credentials can cover their tracks
- By storing in a separate AWS account with different access credentials, even if the production account is compromised, the audit trail remains safe
- This is part of the "Defense in Depth" principle and separation of duties
- HIPAA explicitly requires audit controls that are tamper-evident and immutable

---

## Section 2: Principle of Least Privilege (ANSWERED [x])

### Question 2.1: Developer KMS Key Access
**Q: Why would a Developer role NOT have access to KMS keys, even though they need to write code that processes encrypted data?**

**A: (Your Answer - CORRECT)**
The key use is automated and enabled by the Dev authenticating into the system. They do not actually need it for anything.

**Deeper Context:**
- Developers write code that runs under automated Lambda functions or EC2 instances
- These services assume IAM roles that already have KMS key access
- The developer's code runs *within* a role that has permissions; developers don't need to decrypt data themselves
- If developers had direct KMS access, they could:
  - Decrypt production data on their laptops
  - Export and copy keys
  - Impersonate production processes
- **Minimum Necessary**: Developers need to write code, not decrypt production data
- **Audit Trail**: When their code runs, the Lambda service (not the developer) calls KMS, creating a clear audit trail of what was decrypted and why

**Example:**
```
Developer Code:                Developer DOES NOT have KMS permission
    ↓
Lambda Service (running code)  Lambda DOES have KMS permission
    ↓
KMS Decrypt Call               Audit log: "Lambda service decrypted cohort-anesthesia-2024"
```

---

## Section 3: Access Control Patterns (PENDING - READ ARCHITECTURAL DOCS FIRST)

### Question 3.1: Database View Restriction
**Q: A Data Analyst tries to run: `SELECT * FROM patients WHERE cohort_id IS NULL`. Why does this fail, and what gets logged?**

**Status:** PENDING YOUR ANSWER

**Hints to consider:**
- The analyst has an IAM role and database permissions, but what database view were they granted?
- Refer to: ARCHITECTURE.md → IAM Architecture and Access Control sections
- What columns are included in the view? What rows can the view access?
- When a query fails, what systems log this attempt?

**Your Answer:**
[Submit your answer]

**Sample Answer (for reference after you attempt):**
This query fails at the database layer because:

1. **Database View Restriction**: The analyst's role only has SELECT permission on the view `anesthesia_cohort_2024_analysis`, not the raw `patients` table
2. **WHERE Clause Logic**: The view is defined as:
   ```sql
   CREATE VIEW anesthesia_cohort_2024_analysis AS
   SELECT age, surgery_type, mortality 
   FROM patients 
   WHERE cohort_id = 'anesthesia-2024'
   ```
   The analyst tries to query WHERE cohort_id IS NULL, which returns zero rows because the view filters to only `cohort_id = 'anesthesia-2024'`

3. **What Gets Logged**:
   - **CloudTrail**: "research-team-analyst assumed role at 2026-04-30 10:23:45"
   - **Database Slow Query Log**: The failing SQL query (if it took >1 second to determine it returned 0 rows)
   - **DynamoDB Audit Table**: 
     ```
     {
       "AccessEventID": "evt-def456",
       "Timestamp": "2026-04-30T10:23:47Z",
       "IAMRole": "research-team-analyst",
       "Action": "SELECT * FROM patients WHERE cohort_id IS NULL",
       "Result": "ZERO_ROWS",
       "RecordsAccessed": 0,
       "JustificationReference": "IRB-2024-001"
     }
     ```

4. **Compliance Value**: 
   - Demonstrates that the analyst tried to access outside their approved scope
   - Compliance Officer reviews logs and finds this (benign in this case)
   - If pattern repeats, raises concern about researcher conduct

---

### Question 3.2: De-identification & MRN Risk
**Q: The Medical IT Admin wants to create a de-identified dataset for an external collaborator, but wants to include the patient's Medical Record Number (MRN) as a "code". Why is this a HIPAA violation, and what should they do instead?**

**Status:** PENDING YOUR ANSWER

**Hints to consider:**
- What is HIPAA's definition of "de-identified" data?
- Refer to: ARCHITECTURE.md → "Raw PHI Upload Path Security" and Data Storage Architecture
- What is an MRN, and why can it be used to re-identify patients?
- What's the difference between de-identification and pseudonymization/coding?
- Review: ORGANIZATIONAL_STRUCTURE.md → "Minimum Necessary Principle"

**Your Answer:**
[Submit your answer]

**Sample Answer (for reference after you attempt):**
Including MRN as a "code" is a HIPAA violation because:

1. **MRN is a Direct Identifier**: HIPAA considers MRN one of 18 direct identifiers that must be removed or encrypted in de-identified data:
   - Names, SSN, MRN, medical record numbers, account numbers, etc.
   - Presence of ANY direct identifier means data is NOT de-identified

2. **Re-identification Risk**: 
   - MRN is unique to a patient within a medical system
   - If an attacker knows a patient's MRN, they can link data back to the patient
   - Even without names, MRN alone constitutes an identifier
   - "Coding" (replacing with a code) doesn't remove the identifier if the code is derivable from the MRN

3. **What They Should Do Instead** (Three options per HIPAA):

   **Option A: Safe Harbor De-identification**
   - Remove ALL 18 direct identifiers, plus:
     - Dates (generalize to year only)
     - Age (generalize to ranges if >89)
     - Zip codes (keep only first 3 digits)
   - No code linking available; truly de-identified
   - **For external collaborator**: This is preferred—no risk of re-identification

   **Option B: Expert Determination**
   - Employ a de-identification expert who certifies that re-identification is very unlikely
   - Can include MRN if expert determines re-identification risk <0.04%
   - Requires documentation of expert's analysis
   - Less preferred for external sharing (higher risk)

   **Option C: Limited Dataset + Data Use Agreement**
   - Include MRN but sign a Business Associate Agreement with external collaborator
   - Collaborator legally bound not to attempt re-identification
   - Still risky if collaborator's institution is breached
   - Not recommended for this architecture

4. **For This Project**: Use Option A for external collaborators
   - Remove MRN entirely
   - Use a random code (e.g., "COHORT-001", "COHORT-002") that cannot be reversed
   - External collaborator cannot determine original patient identity
   - If data is leaked, harm is minimized

5. **Audit Trail**:
   - Medical IT logs: "De-identification job removed MRN, generalized dates to year, removed names"
   - Compliance Officer verifies: Checklist confirms all 18 identifiers removed
   - Approval chain: "Approved for external sharing - safe harbor de-identified"

---

### Question 3.3: Access Expiration & Renewal
**Q: The PI's access expires after 90 days. What happens if they need to continue accessing the same study data? Walk through the process.**

**Status:** PENDING YOUR ANSWER

**Hints to consider:**
- Refer to: ARCHITECTURE.md → IAM Architecture → "Access Provisioning Workflow"
- Why does access expire at all? What's the compliance reason?
- Who approves the renewal request?
- What checks are performed during renewal?
- Why is this different from a new access request?

**Your Answer:**
[Submit your answer]

**Sample Answer (for reference after you attempt):**
When the PI's access expires after 90 days:

1. **Automatic Expiration Trigger**:
   - IAM role session expires at 90-day mark
   - KMS key policy denies decrypt to expired session
   - RDS database connections are terminated
   - PI receives notification: "Your access to anesthesia-cohort-2024 expires on 2026-07-30"

2. **Why Expiration Exists**:
   - Forces re-justification of access (security principle: periodic review)
   - Ensures access is still needed (researcher may have finished analysis)
   - Reduces long-term risk of compromised credentials
   - Compliance requirement: Regular re-certification of access

3. **Renewal Request Process**:
   - **Day 89**: PI receives reminder "Access expires in 1 day"
   - **Day 90**: PI submits renewal request to Compliance Officer:
     ```
     Renewal Request:
     - Study: anesthesia-cohort-2024
     - Current Access Duration: 90 days (Jan 1 - Mar 31, 2026)
     - Renewal Duration Requested: 90 days (Apr 1 - Jun 30, 2026)
     - Justification: "Ongoing analysis of cardiac surgery outcomes; manuscript in preparation"
     - Current Status: IRB-2024-001 still active? YES
     - Team Members Still Needing Access: PI, Co-I, Data Analyst
     - Any Incidents/Violations: NO
     ```

4. **Compliance Review** (Shorter than initial approval):
   - Compliance Officer checks:
     - [x] IRB protocol still active?
     - [x] No access violations during past 90 days?
     - [x] PI still listed on protocol?
     - [x] Study objectives still align with approved scope?
   - **Difference from new request**: No need for full risk assessment; just verify ongoing compliance

5. **Approval & Provisioning**:
   - Compliance Officer approves renewal (usually faster, 1-2 days vs. 5-7 for new request)
   - Medical IT extends IAM role and KMS key access for another 90 days
   - Update DynamoDB audit table:
     ```
     {
       "EventType": "AccessRenewal",
       "StudyID": "cohort-anesthesia-2024",
       "IAMRole": "research-team-pi",
       "PriorExpirationDate": "2026-07-30",
       "NewExpirationDate": "2026-10-30",
       "ApprovedBy": "compliance-officer-jane-doe",
       "RenewalJustification": "Ongoing analysis, IRB active"
     }
     ```

6. **If Renewal is Denied**:
   - PI did not resubmit before expiration → access automatically revoked
   - PI must submit **new** access request (full process, longer approval)
   - If urgent need: PI can request expedited review with special justification
   - Compliance Officer investigates: Why was renewal request not submitted?

7. **Compliance Benefit**:
   - Every 90 days: Forced verification that access is still necessary
   - Prevents "zombie access" (people with permissions they no longer need)
   - Annual cycle creates paper trail for auditors: "This team needed access for 12 months; re-approved quarterly"
   - Guards against: Researcher finishing study but keeping access indefinitely

---

## Section 4: Regulatory & Compliance (REFERENCE)

### HIPAA Overview

**HIPAA (Health Insurance Portability and Accountability Act)**
- Federal law protecting patient health information
- Applies to: Covered entities (hospitals, doctors, health plans) and Business Associates

**HIPAA Components**:

1. **Privacy Rule**
   - Controls how PHI can be used and disclosed
   - Requires: Minimum necessary, patient authorization, notice of privacy practices
   - Example: Researcher can only access data for IRB-approved study
   - Mostly procedural/organizational (not technical)

2. **Security Rule** 
   - Protects electronic PHI (ePHI)
   - Requires three types of safeguards:
     - **Administrative Safeguards** (~60%): Policies, training, access controls, risk assessment
     - **Physical Safeguards** (~20%): Facility access, workstation security, equipment management
     - **Technical Safeguards** (~20%): Encryption, audit logs, access controls, integrity controls
   - HIPAA does NOT prescribe HOW, just WHAT must be protected

3. **Breach Notification Rule**
   - If unsecured PHI is exposed: Must notify affected individuals within 60 days
   - Must notify HHS (Department of Health & Human Services)
   - If >500 residents: Must notify media
   - Breaches >500 records result in HHS enforcement action and civil penalties

**Penalties for Violations**:
- Per violation: $100 - $50,000
- Annual violations: Up to $1.5 million per category
- Criminal penalties for intentional disclosure: Up to $250,000 and 10 years prison

---

### NIST Framework

**NIST (National Institute of Standards and Technology)**
- U.S. government agency providing cybersecurity guidance
- Frequently referenced to demonstrate HIPAA compliance (not required, but recommended)

**Key NIST Guidance for HIPAA**:

1. **NIST Cybersecurity Framework (CSF)**
   - Five core functions:
     - **Identify**: Understand assets and risks
     - **Protect**: Implement safeguards
     - **Detect**: Monitor for incidents
     - **Respond**: Take action on incidents
     - **Recover**: Restore from incidents
   
2. **NIST SP 800-66 Rev. 2: "Implementing the HIPAA Security Rule: A Cybersecurity Resource Guide"**
   - Directly maps NIST guidance to HIPAA Security Rule requirements
   - Provides implementation guidance for:
     - Administrative Safeguards
     - Physical Safeguards
     - Technical Safeguards

3. **NIST SP 800-53 "Security and Privacy Controls"**
   - Comprehensive list of security controls
   - Used to build compliance frameworks
   - Many controls map directly to HIPAA requirements

4. **Key NIST Principles Aligned with the Architecture**:
   - **Defense in Depth**: Multiple layers of security (network, application, database, encryption)
   - **Least Privilege**: Users have minimum necessary access
   - **Separation of Duties**: Checks and balances prevent single person from compromising system
   - **Audit Trail**: All activities logged and monitored
   - **Continuous Monitoring**: Real-time detection of threats and policy violations

---

## Section 5: Study Notes & Key Concepts

### From the Architecture Documents

**Critical Concepts to Review**:

1. **Organizational Structure** (ORGANIZATIONAL_STRUCTURE.md)
   - Access control matrix shows who accesses what
   - Minimum necessary principle applied to each role
   - Accountability and audit requirements

2. **AWS Technical Architecture** (AWS_TECHNICAL_ARCHITECTURE.md)
   - Multi-account strategy isolates audit logs
   - Encryption strategy (at-rest and in-transit)
   - Logging & audit trail (4 layers: CloudTrail, DynamoDB, CloudWatch, VPC Flow Logs)
   - Access request workflow (5 steps: request → PI approval → Compliance review → IT provisioning → access granted)

3. **Technical Implementation Patterns**:
   - Database views restrict data at source (not just IAM)
   - KMS key access separate from data access (developer can write code but not decrypt)
   - External collaborators get de-identified data via push (not persistent IAM roles)
   - Audit logs in separate account (immutable)

---

## Next Steps When You Return

1. **Read** all three architecture documents carefully
2. **Answer** the three pending questions (3.1, 3.2, 3.3)
3. **Discuss** your answers—we'll validate your understanding
4. **Proceed** to Infrastructure-as-Code or IAM Policies (to be decided)

---

## Document References

- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - Project goals, glossary, HIPAA/NIST framework, phases
- [ORGANIZATIONAL_STRUCTURE.md](ORGANIZATIONAL_STRUCTURE.md) - Roles, responsibilities, access control matrix
- [ARCHITECTURE.md](ARCHITECTURE.md) - AWS services, IAM roles, encryption, network, audit trails

---

## Section 6: Comprehension Check — System Design and Compliance

### Easy (Recall)

#### Question 6.1: Blank Slate Rule
**Q: What does the Blank Slate Rule guarantee about the CDK infrastructure?**

**A:** The same CDK code that deploys the infrastructure must also be able to cleanly destroy it — returning the AWS accounts to an empty state with no orphaned resources and no zombie spend. `cdk destroy` uses the same stack definitions as `cdk deploy`. If CDK didn't create it, it shouldn't exist. This is verified by a post-destroy script that enumerates remaining resources. The only exception is the 7-day mandatory KMS key deletion waiting period (AWS-enforced, cannot be overridden).

---

#### Question 6.2: Three Operational Modes
**Q: Name the three operational modes for managing the CI lifecycle and describe when each is used.**

**A:**
- **HIBERNATE** — pause compute to reduce cost when the team isn't actively using the environment (conferences, breaks). Storage persists; restart is fast (minutes). Residual cost: ~$50/month.
- **DECOMMISSION** — controlled HIPAA-compliant shutdown at end of Period of Performance. PHI destroyed per policy; audit logs retained for 6–7 years; KMS keys scheduled for 30-day deletion. Used when real PHI is involved and retention obligations apply.
- **DESTROY** — total purge for development/synthetic environments. Everything deleted including audit logs. Nothing remains. Used when there are no compliance retention obligations (synthetic data only). Residual cost: $0 after 7-day KMS wait.

---

#### Question 6.3: IT Staff and PHI Separation
**Q: Why can't IT Staff decrypt PHI data even though they have admin access to the infrastructure?**

**A:** The KMS key policy on `phi-data-key` explicitly denies the `InfraAdmin` role decrypt permission. This is enforced at the key level, not the IAM level — even if an IAM policy granted broad S3 access, the key policy blocks decryption. This is separation of duties: IT Staff builds and maintains the system but cannot read patient data. If they need to troubleshoot a data issue, they escalate to the PI who has decrypt permission. A compromised IT credential therefore cannot exfiltrate PHI — it can only affect infrastructure.

Note: This is a *key policy* enforcement, not an SCP. SCPs are institutional guardrails from UW IT applied at the Organization level. Key policies are project-level controls on individual encryption keys.

---

### Medium (Understanding)

#### Question 6.4: Gatekeeper Blind Spot
**Q: A researcher on their laptop pastes a code error containing an MRN into ChatGPT. Why doesn't the gatekeeper catch this?**

**A:** The gatekeeper only intercepts prompts originating *from within the research environment* (EC2/SageMaker → gatekeeper → Bedrock). A copy-paste from the researcher's laptop browser to an external AI service is entirely outside the compliance perimeter — it never touches AWS infrastructure, so there's nothing for the gatekeeper to intercept.

This is why the architecture uses multiple layers of defense for this scenario:
1. **No general internet from research compute** — the researcher can't paste into ChatGPT from the remote desktop because external AI services are network-blocked
2. **No PHI on the laptop** — by policy, PHI doesn't exist on the laptop, so there should be nothing to paste
3. **Training** — researchers are taught that error messages can contain PHI (MRNs, patient names) and that pasting them externally is a breach

The gap: if a researcher is viewing PHI on the remote desktop and manually transcribes or memorizes an MRN, then types it into their laptop browser — no technical control can prevent this. This is why training and sanctions exist alongside technical controls.

---

#### Question 6.5: VPC Endpoints vs. NAT Gateway
**Q: The project uses VPC Endpoints for most AWS services but a NAT Gateway for GitHub. Why the difference?**

**A:** VPC Endpoints create private connections between the VPC and AWS services — they work because AWS controls both ends (your VPC and the service endpoint). Traffic stays entirely within AWS's internal network and never touches the public internet.

GitHub is not an AWS service. There is no VPC Endpoint for it. The only way to reach GitHub from a private subnet (which has no internet gateway) is through a NAT Gateway, which provides controlled outbound internet access. The NAT Gateway's security group and NACL rules restrict outbound traffic to GitHub's published IP ranges on port 443 only — so it's not general internet access, just a narrow, auditable hole for git operations.

Alternative: AWS CodeCommit (AWS-native git) would eliminate the need for any NAT Gateway entirely, but GitHub's collaboration ecosystem is more practical for a multi-institution team.

---

#### Question 6.6: Fail-Closed Design
**Q: What happens if the Comprehend Medical gatekeeper service crashes — can researchers still use Bedrock?**

**A:** No. The system uses fail-closed design: if the gatekeeper is unavailable (crash, timeout, maintenance), Bedrock access is *blocked*, not bypassed. Researchers see "AI service temporarily unavailable (gatekeeper offline)." An alert fires to IT Staff for immediate investigation.

The alternative (fail-open: bypass the gatekeeper when it's down) would mean that any gatekeeper outage creates a window where PHI could flow to Bedrock unscanned. Fail-closed is the conservative choice — it prioritizes PHI protection over AI availability. A researcher who needs AI assistance during a gatekeeper outage must wait for the fix or work without AI temporarily.

---

### Hard (Synthesis)

#### Question 6.7: PI Departure
**Q: The PI leaves the project mid-PoP. Identify the distinct compliance problems this creates.**

**A:** The PI's departure creates at least six compliance problems beyond "someone else needs to do the work":

1. **Privacy Officer vacancy** — HIPAA requires a designated Privacy Officer at all times. Someone must be named immediately (likely the Postdoc as deputy, or a new PI must be appointed).

2. **Risk acceptance authority gone** — the PI is the only person authorized to accept residual risk. The risk assessment (Gate G2) was signed by this PI. A new sponsor must be designated and must review and re-sign the risk acceptance.

3. **Access approval chain broken** — all new access grants require PI (Privacy Officer) approval. No one can be onboarded, and no access changes can be made, until a new approver is designated.

4. **Breach notification authority** — if a breach occurs, who decides whether to notify HHS? That decision authority was the PI's. Without a designated decision-maker, the project cannot execute its incident response plan.

5. **Budget authority** — the NIH award names a specific PI. Changing the PI requires NIH approval (a formal process that can take months). During the gap, budget decisions are in limbo.

6. **Gate G1 potentially invalidated** — the charter was signed by this PI accepting specific responsibilities. A new PI may need to re-sign or amend the charter, effectively re-satisfying G1.

**Mitigation:** The project designates the Postdoc as deputy for operational decisions (documented in the charter). This provides continuity for items 1, 3, and 4 in the short term. Items 2, 5, and 6 require institutional action (new PI appointment, NIH notification).

---

#### Question 6.8: Agentic AI and Minimum Necessary
**Q: A student runs an AI agent (Kiro in agentic mode) that autonomously queries all 10,000 patient records to answer a simple question about average age. Is this a compliance violation? Why or why not, and what evidence would an auditor examine?**

**A:** This is **not** a compliance violation — but it raises a minimum-necessary question worth examining.

**Why it's not a violation:**
- The student's IAM role (`Researcher`) permits querying the full study cohort (all 10,000 patients)
- The database view grants SELECT on the cohort — no access boundary was crossed
- Computing average age requires all records (you need every age value to calculate the mean)
- The agent operates under the student's credentials, within the student's approved scope

**What an auditor would examine:**
1. CloudTrail logs showing the query (what was accessed, when, from where)
2. The user-agent tag identifying the action as agent-initiated (`kiro-agent/1.0`)
3. The agent session log showing the original request ("what's the average age of the cohort?")
4. The result returned (a single number — not a data dump)
5. Whether the data accessed was within the student's approved scope (it is)

**The minimum-necessary nuance:** Did the agent need to SELECT all columns, or just the age column? If the agent ran `SELECT * FROM cohort_view` when `SELECT age FROM cohort_view` would suffice, that's an over-fetch. It's not a *violation* (the student has access to all columns in the view), but it's a minimum-necessary concern flagged during monthly access review. The agent's behavior should be corrected to query only needed columns.

**Key principle:** The researcher is accountable for agent actions. The agent audit trail is what makes compliance *demonstrable* — without it, the bulk query looks identical to insider threat activity.

---

#### Question 6.9: Adding a New AWS Service
**Q: You want to add Amazon HealthLake to the project. Walk through the sequence of checks and approvals needed before it can touch PHI.**

**A:** Adding a new service that will handle PHI requires checks across multiple layers. The sequence:

1. **BAA coverage check** — Is HealthLake on the [AWS HIPAA Eligible Services](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/) list? If not, it cannot touch PHI regardless of other controls. (HealthLake is HIPAA-eligible.)

2. **SCP compatibility** — Does UW IT's region restriction SCP allow HealthLake? Is it available in us-west-2? If region-restricted, request SCP amendment from UW IT.

3. **Risk assessment update** — New asset in scope. What threats does it introduce? Update `RISK_ASSESSMENT.md` with new scenarios (e.g., "HealthLake misconfigured, exposes FHIR data"). Score likelihood and impact; define mitigations.

4. **Policy review** — Does the Data Handling policy (POL-DH-001) cover this storage type? Does the Access Control policy cover who can access it? Update policies if needed.

5. **KMS integration** — Which key encrypts HealthLake data? Likely `phi-data-key`. Update key policy to allow HealthLake service role to encrypt/decrypt.

6. **IAM update** — Which human roles can access HealthLake? Add permissions to appropriate roles (`SeniorResearcher`, `Researcher`). Ensure `InfraAdmin` has admin but no data-plane access (separation of duties).

7. **VPC Endpoint** — Does HealthLake have a VPC Interface Endpoint? If yes, add it. If no, determine how it's accessed (may require NAT or may be account-level like Config).

8. **CDK implementation** — Add HealthLake resource to the appropriate CDK stack. Deploy.

9. **Config rules** — Add compliance rules for the new service (encryption enabled, access logging, etc.).

10. **Security validation** — Re-run the relevant portions of the Gate G5 checklist for the new resource (encryption verified, access control tested, logging confirmed).

11. **If it involves AI processing** — Run through the AI service approval process (POLICY_AI_ACCEPTABLE_USE.md Section 8).

**Note:** This does NOT require re-walking Gates G1–G4. Those are already satisfied. It triggers a *partial G5 re-validation* for the new component only. The system is already authorized (G6); adding a service is a change-management event during Phase 5 operations.

---

*End of KNOWLEDGE_CHECKS.md — Next: APPENDICES.md*
