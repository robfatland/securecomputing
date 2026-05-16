# Policy: AI Acceptable Use in PHI Environments

## Document Status

| Field | Value |
|-------|-------|
| **Policy ID** | POL-AI-001 |
| **Version** | 1.0 |
| **Effective Date** | [Date of approval] |
| **Review Date** | [Effective Date + 12 months] |
| **Owner** | PI (Privacy Officer) |
| **Applies to** | All project personnel with access to the research environment |
| **HIPAA Basis** | Administrative Safeguard: Information Access Management (§164.308(a)(4)); Technical Safeguard: Access Control (§164.312(a)(1)); Technical Safeguard: Audit Controls (§164.312(b)) |

---

## 1. Purpose

This policy governs the use of artificial intelligence tools and services within the PHI research environment. It defines which AI services are permitted, how they may be used, what technical controls are in place, and what actions constitute policy violations.

AI is an essential research tool in this project. This policy does not prohibit AI use — it channels AI use through compliant pathways that protect PHI while enabling productive research.

---

## 2. Scope

This policy applies to:
- All personnel listed in the project charter (PI, Co-PI, students, postdoc, IT staff)
- All AI interactions originating from or related to the research environment
- All AI interactions that involve, reference, or could inadvertently contain PHI
- AI use on personal devices when the work relates to this project's PHI

This policy does NOT apply to:
- AI use for non-project work that has no connection to PHI (e.g., coursework, personal projects)
- AI services used by AWS internally to operate infrastructure (covered by the BAA)

---

## 3. Definitions

| Term | Definition |
|------|------------|
| **AI Service** | Any system that uses machine learning, large language models, or natural language processing to generate, analyze, or transform content based on user input |
| **Prompt** | Any text, code, or data sent to an AI service as input (including code context sent automatically by IDE features) |
| **PHI** | Protected Health Information — any individually identifiable health information (see HIPAA 18 identifiers) |
| **Internal AI** | AI services running within the project's AWS environment (VPC or AWS service endpoints), covered by the UW–AWS BAA, where data remains within the AWS boundary and is not used for model training. Examples: Amazon Bedrock (which runs AWS-hosted copies of foundation models such as Claude, Llama, etc.), Comprehend Medical, SageMaker inference, self-hosted models on EC2/ECS. |
| **External AI** | AI services where user input leaves the AWS boundary and is transmitted to a third party's infrastructure without a BAA. The defining characteristic is: the prompt crosses the compliance perimeter. Examples: ChatGPT (openai.com), Claude web (claude.ai), Google Gemini, GitHub Copilot (cloud-hosted), any browser-based AI tool accessed from within the research environment. |
| **Gatekeeper** | The Comprehend Medical-based service that scans prompts for PHI before forwarding to Bedrock |
| **PHI Leakage** | Any transmission of PHI to a service or system not authorized to receive it |
| **Research Environment** | The cloud-hosted compute instances (IDE hosts, notebook servers) running within the VPC where PHI is accessible. The laptop is the *means of access* to this environment but is not itself part of it. |
| **Compliance Perimeter** | The boundary within which PHI is permitted to exist. For this project: the AWS VPC and BAA-covered AWS services. Anything outside this boundary must not receive PHI. |

---

## 4. Permitted AI Services

### 4.1 Approved for PHI-Adjacent Work

The following AI services are approved for use within the research environment, including work that involves or references PHI:

| Service | Use Cases | Conditions |
|---------|-----------|------------|
| **Amazon Bedrock** (via gatekeeper) | Code generation, data analysis assistance, research Q&A, summarization, debugging | All prompts pass through Comprehend Medical gatekeeper; all interactions logged |
| **Kiro / VS Code Server AI features** (within VPC) | Code completion, refactoring, explanation | IDE runs within VPC; AI features route through gatekeeper to Bedrock |
| **SageMaker built-in algorithms** | ML model training, inference | Runs within VPC; no external data transmission; model artifacts access-controlled |
| **Amazon Comprehend Medical** | Entity detection (used by gatekeeper) | PHI scanning is its designed purpose; BAA-covered |

### 4.2 Prohibited for PHI-Related Work

The following AI services are **prohibited** for any work that involves, references, or could inadvertently contain PHI:

| Service | Why Prohibited |
|---------|---------------|
| **ChatGPT** (OpenAI web/app) | No BAA; data may be used for training; no audit trail |
| **Claude** (Anthropic web/app) | No BAA; no institutional agreement; no audit trail |
| **Google Gemini** (web/app) | No BAA; data retention policies incompatible with HIPAA |
| **GitHub Copilot** (cloud-hosted) | No BAA for PHI; code context transmitted to GitHub servers |
| **Any other external LLM** | Unless specifically approved via the process in Section 8 |

### 4.3 Permitted for Non-PHI Work (Laptop Only)

External AI services MAY be used on the researcher's **laptop** for work that has **no connection to PHI**:
- General programming questions unrelated to project data
- Literature review and writing (no patient information)
- Research discovery tools (e.g., AI2 Asta "Find Papers", semantic search)
- Learning and skill development

**Critical distinction:** The laptop is the means of access to the PHI environment, but it contains no PHI itself. External AI use on the laptop is permitted because there is no PHI there to leak.

**The research environment (remote desktop / cloud IDE) does NOT have general internet access.** Researchers cannot open a browser on the remote desktop and navigate to ChatGPT, Asta, or other external AI services. This is enforced by network controls (no general egress from research compute instances). If you need to search the web, read papers, or use external AI tools — do it from your laptop, where no PHI is present.

**Rationale:** The remote desktop has PHI visible (notebook outputs, query results, IDE context). Allowing browser access to external services from that environment creates clipboard-proximity risk — a researcher could accidentally paste PHI-containing content into an external service. Eliminating general internet access from research compute removes this vector entirely.

**However:** Personnel must exercise judgment about what constitutes "no connection to PHI." When in doubt, use internal AI services. See Section 6 for guidance.

---

## 5. Technical Controls

The following technical controls enforce this policy. They are not optional — they operate regardless of user intent.

### 5.1 Comprehend Medical Gatekeeper

All AI prompts originating from the research environment pass through the gatekeeper service before reaching Bedrock.

**Gatekeeper behavior:**

| Detection | Action | User Experience |
|-----------|--------|-----------------|
| No PHI detected | Prompt forwarded to Bedrock; response returned normally | Transparent — user sees no delay beyond normal latency |
| PHI detected (high confidence ≥0.9) | Prompt **blocked**; user notified with explanation | User sees: "⚠️ PHI detected in prompt: [entity type] found. Prompt not sent. Please remove PHI and retry." |
| PHI detected (medium confidence 0.7–0.9) | Prompt **held**; user warned; may override with acknowledgment | User sees: "⚠️ Possible PHI detected: [entity type]. Send anyway? (Your override will be logged.)" |
| PHI detected (low confidence <0.7) | Prompt forwarded with flag | Transparent; logged for periodic review |

**Entity types detected:**
- Personal names (PROTECTED_HEALTH_INFORMATION)
- Medical record numbers
- Dates (when combined with health context)
- Addresses and geographic identifiers
- Phone/fax numbers, email addresses
- Social Security numbers
- Medical conditions, diagnoses, medications (when linked to identifiers)

### 5.2 Network Controls

| Control | Implementation |
|---------|---------------|
| External AI services blocked | VPC security groups and NACLs block outbound traffic to known AI service endpoints (api.openai.com, api.anthropic.com, etc.) |
| DNS filtering | Route 53 resolver rules block resolution of external AI domains from research VPC |
| Egress monitoring | VPC Flow Logs + GuardDuty detect attempts to reach blocked services |
| No general internet | Research compute instances have no general internet access; only approved AWS service endpoints (via VPC endpoints) and GitHub (for git operations) |

### 5.3 Audit Logging

All AI interactions are logged:

| What is Logged | Where | Retention |
|----------------|-------|-----------|
| Every prompt submitted (hash, not full text for privacy) | CloudWatch Logs | 7 years |
| Gatekeeper decisions (allow/block/warn) | DynamoDB | 7 years |
| PHI entities detected (type, confidence, position) | DynamoDB | 7 years |
| User overrides of medium-confidence warnings | DynamoDB | 7 years |
| Bedrock invocation metadata (model, tokens, timestamp) | CloudTrail | 7 years |
| Blocked external AI access attempts | VPC Flow Logs | 7 years |

### 5.4 Fail-Closed Design

If the gatekeeper service is unavailable (error, timeout, maintenance):
- **Bedrock access is blocked** — prompts are not forwarded
- Users see: "AI service temporarily unavailable (gatekeeper offline). Please try again later."
- Alert fires to IT staff for immediate investigation
- This is a fail-closed design: failure blocks access rather than bypassing controls

---

## 6. User Responsibilities

### 6.1 General Obligations

All personnel must:

1. **Use only approved AI services** for PHI-related work (Section 4.1)
2. **Never paste PHI into external AI services** — even if you believe the data is de-identified
3. **Minimize PHI in prompts** — ask questions about code logic, not about specific patients
4. **Respond appropriately to gatekeeper warnings** — if PHI is detected, remove it and rephrase
5. **Report incidents** — if you believe PHI was sent to an unauthorized service, report immediately (Section 9)
6. **Complete training** — including the AI-specific supplement, before using any AI tools in the environment

### 6.2 Prompt Hygiene Guidelines

**Do:**
- Ask about code patterns: "How do I join these two tables efficiently?"
- Ask about methods: "What's the best way to handle missing values in a time series?"
- Reference data by structure: "I have a column called 'diagnosis_code' — how do I map ICD-10 codes?"
- Use synthetic examples: "If a patient has values [A, B, C], how would I calculate X?"

**Don't:**
- Include actual patient identifiers: "Patient MRN A12345678 has conflicting records..."
- Paste raw query results: "Here's the output: Name: John Smith, DOB: 1955-03-12..."
- Include error messages with PHI: "Error on row with mrn=A12345678..."
- Reference specific patients: "The patient in row 4523 who has diabetes..."

**When in doubt:** Remove all identifiers, dates, and specific values. Replace with placeholders: "Patient [X] with condition [Y] on date [Z]."

### 6.3 Override Responsibility

When the gatekeeper flags a medium-confidence detection and offers an override:
- **Review the flagged content carefully** — is there actually PHI present?
- **If no PHI is present** (false positive): override is acceptable; your override is logged
- **If PHI might be present**: do NOT override; rephrase the prompt
- **Overrides are audited** — patterns of overrides will be reviewed monthly

---

## 7. Incident Classification

### 7.1 AI-PHI Incident Types

| Type | Severity | Definition | Example |
|------|----------|------------|---------|
| **Near-miss** | Low | Gatekeeper blocked PHI before it reached any AI service | Researcher typed MRN in prompt; gatekeeper caught it; prompt never sent |
| **Contained disclosure** | Medium | PHI reached an internal AI service (Bedrock) unnecessarily | Gatekeeper missed a low-confidence entity; PHI in prompt processed by Bedrock (BAA-covered, so contained) |
| **External disclosure** | High | PHI sent to an external AI service not covered by BAA | Researcher used personal laptop to paste PHI into ChatGPT for debugging |
| **Systematic failure** | Critical | Gatekeeper failed and multiple prompts with PHI reached services without scanning | Gatekeeper outage not detected; fail-closed mechanism failed |

### 7.2 Response by Severity

| Severity | Immediate Action | Reporting | Follow-up |
|----------|-----------------|-----------|-----------|
| **Low (near-miss)** | None required beyond gatekeeper notification | Logged automatically; reviewed monthly in aggregate | Training reinforcement if pattern detected |
| **Medium (contained)** | Review prompt content; assess if PHI was material | Report to PI within 24 hours; document in incident log | Gatekeeper tuning; consider adding detection pattern |
| **High (external disclosure)** | Determine what PHI was disclosed; assess breach scope | Report to PI immediately; PI assesses breach notification obligation | Breach risk assessment per §164.402; potential HHS notification; sanctions consideration |
| **Critical (systematic)** | Shut down AI access until gatekeeper restored | Report to PI and CISO immediately | Root cause analysis; system not re-enabled until fix verified |

### 7.3 Breach Determination for AI-PHI Events

Not every PHI disclosure to an AI service constitutes a HIPAA breach requiring notification. Per 45 CFR §164.402, a breach is presumed unless the covered entity demonstrates low probability of compromise based on:

1. **Nature and extent of PHI involved** — Was it a single MRN, or a full patient record?
2. **Who received the PHI** — A BAA-covered service (Bedrock) vs. an uncovered service (ChatGPT)
3. **Whether PHI was actually acquired or viewed** — Did the AI service store/retain the data?
4. **Extent of mitigation** — Can the disclosure be contained (e.g., request data deletion from provider)?

**For this project:**
- PHI reaching Bedrock (BAA-covered) = NOT a breach (disclosure to a Business Associate under agreement)
- PHI reaching an external AI without BAA = PRESUMED breach unless the four-factor analysis demonstrates low probability of compromise

---

## 8. Adding New AI Services

No AI service may be used for PHI-related work unless it has been through this approval process:

### 8.1 Approval Process

1. **Request:** Team member identifies a new AI service they want to use; submits request to PI with:
   - Service name and provider
   - Intended use case
   - Whether PHI could be in prompts/inputs
   - Provider's data handling policies

2. **Review:** PI evaluates:
   - Is the service HIPAA-eligible? (On AWS BAA services list, or separate BAA available?)
   - Does the provider offer a BAA or data processing agreement?
   - Does the provider guarantee no training on customer data?
   - Can the service be accessed within the VPC (or does it require internet egress)?
   - Can interactions be logged and audited?

3. **Decision:**
   - If BAA-covered + within VPC + auditable → may be approved
   - If no BAA available → prohibited for PHI-related work (may be approved for non-PHI use)
   - If approved → added to Section 4.1; gatekeeper configured to route to new service

4. **Documentation:** Approval decision documented with rationale; added to compliance evidence

### 8.2 Annual Review

All approved AI services are reviewed annually:
- Is the BAA still in effect?
- Has the provider changed their data handling policies?
- Is the no-training guarantee still valid?
- Are there new services that better meet our needs?

---

## 9. Reporting Obligations

### 9.1 How to Report

| Situation | Action | Timeline |
|-----------|--------|----------|
| Gatekeeper blocked your prompt | No action needed — system handled it | Automatic |
| You accidentally sent PHI to an external AI | Report to PI immediately via Wickr or in person | Within 1 hour of discovery |
| You suspect someone else sent PHI externally | Report to PI via Wickr | Within 24 hours |
| You notice the gatekeeper is not working | Report to IT staff immediately | Within 1 hour |
| You're unsure if something was a violation | Ask PI — no penalty for asking | As soon as practical |

### 9.2 No Retaliation

Good-faith reporting of potential violations — including self-reporting — will not result in sanctions. The purpose of reporting is to contain and remediate, not to punish. Sanctions apply to:
- Deliberate circumvention of controls
- Repeated violations after training/warning
- Failure to report a known violation

---

## 10. Sanctions

> 📋 **GENERIC:** The following sanctions framework uses generic language appropriate for a template. Your version must reference your institution's specific disciplinary procedures, student conduct codes, and employment policies.

Violations of this policy are subject to progressive sanctions:

| Violation | First Occurrence | Repeated | Deliberate/Egregious |
|-----------|-----------------|----------|---------------------|
| Accidental PHI in prompt (caught by gatekeeper) | No sanction — system worked as designed | Training refresher if pattern detected | N/A |
| Accidental PHI sent to external AI (self-reported) | Documented counseling; retraining | Written warning; access review | N/A |
| Accidental PHI sent to external AI (discovered by audit) | Written warning; retraining | Access suspension pending review | Referral to institutional process |
| Deliberate circumvention of controls | Access suspension; investigation | Removal from project; institutional referral | Institutional disciplinary action; potential legal referral |
| Failure to report known violation | Written warning | Access suspension | Removal from project |

---

## 11. Training Requirements

### 11.1 Initial Training

Before receiving access to the research environment, all personnel must complete:

1. **Core HIPAA training** (CITI Program or equivalent) — covers Privacy Rule, Security Rule, Breach Notification
2. **Project AI supplement** — covers this policy, including:
   - What constitutes PHI in code/prompts (with examples)
   - How the gatekeeper works
   - Approved vs. prohibited services
   - Prompt hygiene practices
   - How to report incidents
   - Sanctions for violations

3. **Signed acknowledgment** — "I have read and understand Policy POL-AI-001 and agree to comply with its requirements."

### 11.2 Ongoing Training

- **Annual renewal:** All personnel re-complete the AI supplement annually
- **Incident-triggered:** After any medium or high severity incident, affected personnel complete targeted retraining
- **Policy update:** When this policy is revised, all personnel are notified and must acknowledge the changes

---

## 12. Policy Review and Updates

| Trigger | Action |
|---------|--------|
| Annual (scheduled) | Full policy review; update for new AI services, new threats, lessons learned |
| New AI service approved | Update Section 4; notify all personnel |
| After any high/critical incident | Review whether policy changes could prevent recurrence |
| Significant change in AI landscape | Assess whether new services or capabilities require policy updates |
| Change in BAA terms | Verify all approved services still covered |

---

## 13. AI-Generated Output as Derived PHI

When internal AI (Bedrock) processes prompts that contain or reference PHI, the AI's output may constitute **derived PHI**. Examples:
- A patient summary generated by Bedrock from clinical records
- Pattern analysis results that could identify individuals
- Code generated by AI that embeds patient-specific logic or values

**Rule:** AI-generated output that is derived from PHI is itself PHI. It must:
- Remain within the compliance perimeter (no export, no download)
- Be access-controlled at the same level as the source data
- Be subject to the same retention and disposition policies
- Be included in the data inventory for decommission purposes

> 🔄 **REVISIT:** As AI capabilities evolve and researchers develop more sophisticated AI-on-PHI workflows (e.g., "summarize all records for patients with condition X"), this section may need expansion to address: output classification criteria, de-identification of AI outputs, and whether AI-generated summaries can be treated as a Limited Data Set.

---

## 14. Agentic AI and Autonomous Data Access

### 14.1 The Problem

AI agents (such as Kiro operating in agentic mode) can autonomously execute multi-step workflows: writing code, querying databases, reading files, and producing results — all in response to a single researcher request. This creates a compliance challenge:

- The agent operates under the researcher's credentials (IAM role)
- CloudTrail logs the API calls but cannot inherently distinguish human-initiated from agent-initiated actions
- An auditor reviewing access logs sees bulk data access patterns that look identical to insider threat activity
- The minimum-necessary principle is harder to evaluate when an agent decides what to access

### 14.2 Accountability Principle

> The researcher is accountable for all actions taken by an AI agent operating under their credentials, just as they are accountable for actions taken by a script they wrote and executed. The agent acts *on behalf of* the researcher.

However: agent-initiated actions must be **distinguishable** from human-initiated actions in the audit trail to enable meaningful access review.

### 14.3 Agent Audit Requirements

All agentic AI operations that access PHI must produce an audit trail containing:

| Field | Purpose | Example |
|-------|---------|---------|
| **Researcher identity** | Who initiated the request | jane.doe@uw.edu |
| **Original request** | What the researcher asked for | "Calculate mean HbA1c for the study cohort" |
| **Agent session ID** | Links all sub-actions to one request | sess-abc123 |
| **Actions taken** | Each data access the agent performed | Query: `SELECT hba1c FROM patient_labs WHERE cohort_id = 'STUDY01'` |
| **Data accessed** | What was read/written | patient_labs table, 10,000 rows, columns: patient_id, hba1c |
| **Timestamp** | When each action occurred | 2026-05-14T14:47:03Z |
| **User-agent tag** | Identifies the action as agent-initiated | `kiro-agent/1.0` (or equivalent) |
| **Result summary** | What was returned to the researcher | "Mean HbA1c: 7.2 (n=9,847 non-null values)" |

### 14.4 Implementation

**CloudTrail level:** The AI agent should use a distinctive user-agent string in all AWS API calls. This allows filtering agent-initiated calls from human-initiated calls during audit review.

**Application level:** An agent audit layer (logging service) records:
1. The researcher's original natural-language request
2. The agent's plan (what it intends to do)
3. Each action executed (with data access details)
4. The final result returned to the researcher
5. A session ID linking all of the above

**Audit review:** Monthly access reviews (Phase 5) must include review of agent-initiated access patterns:
- Is the agent accessing more data than the researcher's role permits? (Should not be possible if IAM is correct, but verify)
- Is the agent accessing data beyond what the request requires? (Minimum-necessary evaluation)
- Are there unusual patterns (bulk access, off-hours, unexpected tables)?

### 14.5 Minimum Necessary for Agents

The minimum-necessary principle applies to agent actions:
- The agent should query only the columns needed (not `SELECT *`)
- The agent should filter to the approved cohort (not all patients)
- If the agent over-fetches, this should be flagged in audit review and the agent's behavior corrected

**Technical enforcement:** The agent operates under the same IAM role and database views as the researcher. It *cannot* access data the researcher cannot access. But it *can* access more data than a specific request requires — this is a minimum-necessary concern, not an access-control concern.

> 🔄 **REVISIT:** As agentic AI matures, consider whether agents should have their own IAM roles (more restrictive than the researcher's) or whether per-request scoping is feasible. Also consider whether agent "reasoning traces" should be retained as compliance evidence.

---

## 15. Open Verification Items

| Item | Status | Impact |
|------|--------|--------|
| Confirm Kiro's AI backend (Bedrock? Other?) | Unverified | If not Bedrock, must verify BAA coverage and no-training guarantee before use in PHI environment |
| Confirm Kiro supports distinctive user-agent tagging for agent actions | Unverified | Required for agent audit trail (Section 14) |
| Confirm network architecture supports GitHub egress without general internet | Design phase | Required for git operations from research environment |

---

## 16. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| **Policy Owner (PI)** | Dr. D.R. Smith | _________________ | ________ |
| **Acknowledged (IT Staff)** | [IT Staff Name] | _________________ | ________ |

---

## Appendix A: Known PHI Patterns in Code Context

The following patterns commonly appear in code and may contain PHI. The gatekeeper scans for these, but researchers should also be aware:

| Pattern | Example | Why It's PHI |
|---------|---------|--------------|
| MRN in error message | `Key (mrn)=(A12345678) already exists` | Medical Record Number = HIPAA identifier |
| Name in variable | `patient_john_doe = query(...)` | Patient name = HIPAA identifier |
| Date + condition | `patients_diagnosed_diabetes_2024_03_15` | Date + diagnosis could identify individual |
| Address in test data | `address = "123 Main St, Seattle 98195"` | Geographic data = HIPAA identifier |
| SSN in log output | `Validation failed for SSN: 123-45-6789` | Social Security Number = HIPAA identifier |
| Phone in config | `emergency_contact: 206-555-0123` | Phone number = HIPAA identifier |
| Query with identifiers | `SELECT * FROM patients WHERE name LIKE 'Sm%'` | Name fragment in query = potential PHI |
| Notebook output | Cell displays: `| MRN | Name | DOB | Diagnosis |` | Full PHI record in visible output |

## Appendix B: Gatekeeper Entity Detection Reference

Amazon Comprehend Medical detects the following entity categories:

| Category | Entities | Relevance |
|----------|----------|-----------|
| **PROTECTED_HEALTH_INFORMATION** | Names, ages, dates, addresses, phone/fax, email, SSN, MRN, account numbers, URLs, IPs | Direct HIPAA identifiers — always blocked at high confidence |
| **MEDICAL_CONDITION** | Diagnoses, symptoms, signs | PHI only when linked to an identifier; flagged at medium confidence |
| **MEDICATION** | Drug names, dosages, routes | PHI only when linked to an identifier; flagged at medium confidence |
| **TEST_TREATMENT_PROCEDURE** | Lab tests, procedures, results | PHI only when linked to an identifier; flagged at medium confidence |
| **ANATOMY** | Body parts, organ systems | Rarely PHI alone; low confidence flag |

**Supplemental regex patterns** (project-specific, added to gatekeeper):
- UW MRN format: `[A-Z]\d{8}` (letter + 8 digits)
- SSN format: `\d{3}-\d{2}-\d{4}`
- Phone format: `\d{3}[-.]?\d{3}[-.]?\d{4}`
- Date formats: `\d{4}-\d{2}-\d{2}`, `\d{2}/\d{2}/\d{4}`
