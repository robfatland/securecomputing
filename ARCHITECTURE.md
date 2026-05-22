\newpage

<!-- SOURCE: ARCHITECTURE.md -->

# Technical Architecture

This document describes the technical architecture of the Synthetic PHI Research Environment on AWS: services used, network design, compute model, data flows, AI integration, and security controls.

> For project governance, phases, roles, and policies see `PROJECT_OVERVIEW.md`. For gate definitions see `GATES.md`.

---

## AWS Services Registry

All AWS services used in this project must be HIPAA-eligible (listed on the [AWS HIPAA Eligible Services Reference](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/)) and covered under the UW–AWS BAA. This registry documents each service, its role in the project, and its PHI exposure.

| Service | Role in Project | PHI Exposure | Notes |
|---------|----------------|--------------|-------|
| **S3** | Object storage: PHI landing zone, validated data, derived data, audit logs | Direct — stores raw PHI | Encrypted (SSE-KMS); versioned; access-logged; zone-separated |
| **RDS** | Relational database for structured PHI (patient records, clinical data) | Direct — stores raw PHI | Encrypted at rest (KMS) and in transit (TLS); automated backups |
| **EC2** | Compute hosts: IDE server, notebook server, processing pipelines | Indirect — processes PHI in memory | Private subnets only; no public IPs; security groups restrict access |
| **EFS** | Shared filesystem (NFS-compatible) mounted across researcher EC2 instances | Direct — researchers store working files, code, intermediate results | Encrypted at rest (KMS) and in transit; mount targets in private subnets; POSIX permissions + IAM authorization |
| **SageMaker** | Managed notebook environment; ML model training and inference | Direct — notebooks query and display PHI | VPC-only mode (no internet); encrypted storage; IAM role-scoped |
| **Bedrock** | LLM inference for code assistance, analysis, research Q&A | Indirect — prompts may contain PHI (gatekeeper mitigates) | BAA-covered; no model training on inputs; all invocations logged |
| **Comprehend Medical** | PHI entity detection in AI prompts (gatekeeper service) | Indirect — scans text that may contain PHI | BAA-covered; used as a control, not a data store |
| **KMS** | Encryption key management for all data-at-rest encryption | None directly — manages keys that protect PHI | Key policies restrict usage by role; automatic rotation; deletion scheduling |
| **IAM + SSO** | Identity, authentication, authorization, role-based access control | None directly — controls who can reach PHI | Federated via UW SSO; MFA enforced; least-privilege policies |
| **CloudTrail** | API call logging across all services | Indirect — logs contain metadata about PHI access (who accessed what, when) | All-region; immutable; stored in separate audit bucket |
| **CloudWatch** | Monitoring, alerting, log aggregation | Indirect — may contain operational data referencing PHI access | Alarms for security events; log retention per policy |
| **GuardDuty** | Threat detection (anomalous API calls, network behavior) | None — analyzes metadata patterns | Alerts on suspicious activity; feeds incident response |
| **Macie** | Sensitive data discovery (scans S3 for exposed PHI) | Indirect — identifies PHI locations | Validates that PHI is where it should be and not where it shouldn't |
| **AWS Config** | Compliance drift detection (are resources configured correctly?) | None — evaluates configuration state | Conformance packs for HIPAA; alerts on non-compliant changes |
| **Security Hub** | Aggregated security findings dashboard | None — aggregates findings from other services | Single-pane compliance view |
| **VPC + Security Groups + NACLs** | Network segmentation and traffic control | None — controls network paths | Private subnets; no direct internet; egress restricted |
| **VPC Flow Logs** | Network traffic metadata logging | Indirect — records connection metadata | Feeds anomaly detection; stored in CloudWatch/S3 |
| **Lambda** | Serverless compute: gatekeeper logic, upload validation, automation | Indirect — processes prompts and data events | VPC-attached where PHI access needed; IAM-scoped |
| **SNS** | Notifications and alerts (system → human) | None — carries alert messages | Upload confirmations, security alerts, incident notifications |
| **AWS Wickr** | Secure team communication (messaging, file sharing, screen sharing) | Potential — team discussions may reference PHI | End-to-end encrypted; HIPAA-eligible; message retention policies; admin audit controls; ephemeral message option |
| **AWS Transfer Family** | SFTP endpoint for PHI upload (alternative to CLI) | Direct — PHI transits through this service | Optional; provides familiar SFTP interface for UW IT upload |
| **ECR** | Container image registry (Docker images) | None — images contain code, not PHI | Images must not contain PHI, credentials, or test data; scanned for vulnerabilities |
| **ECS / Fargate** | Container orchestration and execution | Indirect — containers process PHI at runtime | VPC-only; IAM task roles scoped per container; encrypted storage |

### Services Under Consideration (not yet committed)

| Service | Potential Role | Decision Point |
|---------|---------------|----------------|
| **Amazon Athena** | SQL queries directly against S3 data (serverless) | Phase 2 — depends on data format and query patterns |
| **AWS Glue** | ETL pipelines for data transformation | Phase 3 — depends on processing complexity |
| **Amazon QuickSight** | Visualization/dashboards for research results | Phase 5 — depends on reporting needs |
| **EKS (Kubernetes)** | Container orchestration (if ECS is insufficient) | Phase 2 — depends on workload complexity |

### External Services (outside AWS, outside compliance boundary)

| Service | Role | PHI Exposure | Controls |
|---------|------|--------------|----------|
| **GitHub** | Source code repository, IaC templates, Dockerfiles, CI/CD pipeline definitions, documentation | **None permitted** — code only, never data | Private repos; .gitignore excludes data; pre-commit hooks scan for PHI patterns; nbstripout for notebooks; GitHub secret scanning enabled |
| **GitHub Actions** | CI/CD: build containers, run tests, deploy to AWS | **None** — builds code, does not process PHI | OIDC federation for AWS credentials (no stored secrets); runners never pull PHI; deployment targets AWS environment |

---

## Researcher Environment Model

### Endpoint Architecture

```
┌─────────────────────────┐          ┌─────────────────────────────────────┐
│  Researcher Laptop      │          │  AWS VPC (private subnets)          │
│  (outside compliance    │          │                                     │
│   boundary)             │   SSO    │  ┌─────────────────────────────┐    │
│                         │   +MFA   │  │  EC2: IDE Host              │    │
│  - Browser / SSH client ├─────────►│  │  (Kiro or VS Code Server)   │    │
│  - No PHI stored        │          │  │                             │    │
│  - Code development     │          │  └──────────────┬──────────────┘    │
│    (non-PHI)            │          │                 │                    │
│                         │          │  ┌──────────────┴──────────────┐    │
└─────────────────────────┘          │  │  Amazon EFS (shared)        │    │
                                     │  │  - Working files             │    │
                                     │  │  - Code repositories         │    │
                                     │  │  - Intermediate results      │    │
                                     │  │  Mounted on all compute      │    │
                                     │  └──────────────┬──────────────┘    │
                                     │                 │                    │
                                     │  ┌──────────────┴──────────────┐    │
                                     │  │  SageMaker / Notebook Host  │    │
                                     │  │  - Jupyter notebooks         │    │
                                     │  │  - ML training               │    │
                                     │  │  - Data exploration          │    │
                                     │  └─────────────────────────────┘    │
                                     │                                     │
                                     └─────────────────────────────────────┘
```

### Laptop Role and Boundaries

| Aspect | Policy |
|--------|--------|
| **PHI on laptop** | Prohibited — no PHI is downloaded, cached, or stored locally |
| **Code on laptop** | Permitted — researchers may develop code locally that does not contain PHI |
| **Code import to cloud** | Permitted — via git push or file upload to EFS; code reviewed for inadvertent PHI |
| **Authentication** | UW SSO + MFA required for all cloud access; session timeouts enforced |
| **Laptop security** | Institutional baseline (disk encryption, OS updates, screen lock) — outside project scope but assumed |
| **External AI on laptop** | Policy: prohibited for PHI-related work; permitted for non-PHI coding tasks (but training emphasizes awareness) |

### Processing Pipeline Categories

| Category | Where Developed | Where Runs | PHI Exposure | Example |
|----------|----------------|------------|--------------|---------|
| **Pre-existing libraries** | External (open source, vendor) | Cloud CI | Indirect — processes PHI at runtime | pandas, scikit-learn, clinical NLP packages |
| **Code developed on localhost** | Researcher laptops | Imported to cloud CI; runs there | None during development; indirect at runtime | Analysis scripts, custom utilities |
| **Code developed on cloud CI** | Cloud IDE (Kiro/VS Code Server) | Cloud CI | Potential — developed in PHI-adjacent environment | Queries, data transformations, study-specific logic |

**Pipeline update process:**
- Pre-existing libraries: updated periodically via package manager (pip/conda) on cloud CI; updates reviewed for compatibility
- Localhost code: pushed via git to GitHub (private repo); CI/CD pipeline (GitHub Actions) builds containers and deploys to AWS environment
- Cloud-developed code: version-controlled in cloud git repository (may mirror to GitHub if non-PHI); no export of PHI-containing artifacts

### Containerization (Docker)

**Purpose:** Package research code and dependencies into reproducible, versioned container images. Containers provide isolation, immutability, and consistent environments across development and production.

**Workflow:**
```
Researcher laptop                GitHub                    AWS
──────────────────              ──────────                ─────────────
1. Write Dockerfile             3. GitHub Actions         5. ECS/Fargate
   + application code              builds image              runs container
2. git push                     4. Push image to ECR         in VPC
                                                          6. Container accesses
                                                             PHI via IAM role
```

**Compliance boundaries:**
- **Dockerfiles and code** → GitHub (no PHI)
- **Built images** → ECR (no PHI in images; images are code artifacts)
- **Running containers** → ECS/Fargate in VPC (PHI accessed at runtime via IAM roles, encrypted connections)
- **Container logs** → CloudWatch (may contain PHI references; treated as audit data)

**Rules:**
- Images must not contain PHI, credentials, secrets, or test data with real identifiers
- Runtime secrets injected via AWS Secrets Manager or environment variables from Parameter Store
- Base images pinned to specific versions (no `latest` tags in production)
- Images scanned for vulnerabilities (ECR image scanning enabled)
- Container task roles follow least-privilege (each container gets only the IAM permissions it needs)

### Source Control (GitHub)

**Purpose:** Version control for all code, infrastructure-as-code, documentation, and CI/CD pipeline definitions. Enables collaboration between UW and FH team members.

**What goes to GitHub:**
- Application source code (Python, R, SQL, etc.)
- Dockerfiles and container build configurations
- Terraform / CloudFormation templates
- CI/CD pipeline definitions (GitHub Actions workflows)
- Project documentation (non-PHI)
- Configuration files (with secrets replaced by references)

**What NEVER goes to GitHub:**
- PHI in any form (data files, database dumps, CSV exports)
- Notebook output cells (may contain query results with PHI)
- Credentials, API keys, encryption keys
- Audit logs or access logs
- Any file from the S3 PHI zones

**Technical controls preventing PHI leakage:**
1. `.gitignore`: excludes `data/`, `output/`, `*.csv`, `*.parquet`, `*.json` (data formats), `*.ipynb_checkpoints`
2. **Pre-commit hooks**: regex scanning for PHI patterns (MRN format, SSN format, date-name combinations)
3. **nbstripout**: automatically strips notebook output cells before commit
4. **GitHub secret scanning**: alerts on detected credentials or keys
5. **Branch protection**: require PR review before merge to main (second pair of eyes)
6. **GitHub Actions**: OIDC federation to AWS (no long-lived credentials stored in GitHub)

### Shared Filesystem (Amazon EFS)

**Purpose:** Provide a shared POSIX-compatible filesystem accessible to all researcher compute instances (IDE hosts, notebook servers, processing nodes). Replaces the need for researchers to manage individual file copies or use S3 for working files.

**Use cases:**
- Shared code repositories (git working directories)
- Intermediate analysis results accessible to all team members
- Shared configuration files and environment settings
- Collaborative working space (researcher A's output is researcher B's input)

**Security controls:**
- Encrypted at rest (KMS — same key hierarchy as other PHI stores)
- Encrypted in transit (TLS mount)
- Mount targets in private subnets only
- IAM authorization for mount access
- POSIX permissions for file-level access control (user/group)
- Access logging via CloudTrail (EFS API calls) and VPC Flow Logs (NFS traffic)
- No public accessibility; no internet-facing mount points

**What EFS is NOT used for:**
- Long-term PHI storage (that's S3 and RDS)
- Audit logs (separate S3 bucket, immutable)
- Backups (managed separately with retention policies)

EFS is the *working surface* — where active research happens. PHI may transit through EFS during analysis, so it's treated as a PHI-containing system with full encryption and access controls.

### Team Communication (AWS Wickr)

**Purpose:** Secure, HIPAA-compliant team messaging within the project. Replaces the need for Slack, Teams, or email for project-internal communication.

**Configuration:**
- Wickr network restricted to project team members (7 people)
- Message retention policy: 90 days (configurable; aligns with project needs)
- Admin controls: PI (Dr. D.R. Smith) has admin role; can manage users, set retention, review compliance logs
- End-to-end encryption: messages encrypted client-to-client; AWS cannot read content
- Ephemeral messages: available for sensitive discussions that should not persist
- File sharing: permitted within Wickr (files encrypted in transit and at rest)
- Audit: message metadata logged (who, when, to whom — not content) for compliance

**Policy:**
- Prefer referencing data by study ID or record pointer rather than pasting raw PHI values
- PHI in messages is permitted (channel is secure and BAA-covered) but minimized per minimum-necessary principle
- Wickr is the *only* approved channel for project communication that may reference PHI
- External channels (personal email, Slack, SMS) are prohibited for PHI-related discussion

---

## AI Use in PHI Environments

### Guiding Principle

AI is an essential research tool in this project. Its use must be governed with the same rigor as any other PHI access — with policies, technical controls, training, and audit trails. AI is not an exception to HIPAA; it is a new surface that HIPAA applies to.

### AI Use Taxonomy

| AI Type | Mode of Use | PHI Exposure Risk | Mitigation |
|---------|-------------|-------------------|------------|
| **IDE assistant (Kiro)** | Code completion, code explanation, refactoring | Medium — code context may contain PHI in variable names, queries, comments, error messages | Runs within VPC; Comprehend Medical gatekeeper scans outbound prompts |
| **LLM via Bedrock** | Data analysis, summarization, code generation, research Q&A | High — prompts may contain PHI directly | Bedrock within AWS (BAA-covered); no-training verified; all prompts logged; gatekeeper pre-screens |
| **External LLM (ChatGPT, Claude web, etc.)** | Ad-hoc questions, debugging, writing | High — copy-paste of errors, data snippets, queries containing MRNs or other identifiers | **Policy: prohibited for PHI-related work**; network controls block access from research environment; training emphasizes why |
| **Notebook AI features** | Inline suggestions, cell completion | Medium — notebook cells contain query results with PHI | Notebook environment runs within VPC; AI features route through Bedrock + gatekeeper |
| **Custom/fine-tuned models** | Study-specific analysis pipelines | Contained if within VPC | Model artifacts treated as derived PHI; access-controlled; no export without review |

### The PHI Leakage Problem

PHI can leak to AI services in non-obvious ways:

- **Error messages**: `ERROR: duplicate key violates constraint "patient_pkey" - Key (mrn)=(A12345678) already exists` — pasting this into an external AI discloses an MRN
- **Code comments**: `# Filter patients over 65 from the Smith family in zip 98195` — age + surname + zip may constitute PHI
- **Variable names**: `patient_john_doe_labs = query(...)` — a name embedded in code
- **Query results in notebooks**: Cell output containing patient demographics visible in IDE context
- **Log files**: Application logs with patient identifiers referenced in debugging sessions

**Training must address these scenarios explicitly.** Researchers habituated to pasting errors into ChatGPT must understand that this workflow is incompatible with PHI handling.

### Comprehend Medical as Prompt Gatekeeper

**Architecture:**

```
Researcher action (code completion, AI query, paste)
        │
        ▼
┌─────────────────────────┐
│   Gatekeeper Service    │
│   (Lambda / sidecar)    │
│                         │
│  1. Intercept prompt    │
│  2. Send to Comprehend  │
│     Medical for entity  │
│     detection           │
│  3. Decision:           │
│     - No PHI → forward  │
│       to Bedrock        │
│     - PHI detected →    │
│       block + notify    │
│       researcher +      │
│       log event         │
└─────────────────────────┘
        │
        ▼ (if clean)
┌─────────────────────────┐
│   AWS Bedrock           │
│   (BAA-covered LLM)     │
│                         │
│   Process prompt;       │
│   return response       │
└─────────────────────────┘
        │
        ▼
   Response to researcher
```

**Components:**

| Component | Role | AWS Service |
|-----------|------|-------------|
| PHI detection | Scan outbound prompts for clinical entities (MRNs, names, dates, diagnoses, medications) | Amazon Comprehend Medical |
| AI inference | Code completion, analysis, research Q&A | Amazon Bedrock |
| Gatekeeper logic | Intercept, scan, allow/block/redact, route | AWS Lambda or sidecar process on IDE host |
| Audit logging | Record all gatekeeper decisions (allowed, blocked, what was detected) | CloudWatch Logs / DynamoDB |
| Researcher feedback | Real-time notification when PHI is detected in a prompt | IDE notification / terminal alert |

**Gatekeeper behaviors:**

| Detection Result | Action | Audit |
|-----------------|--------|-------|
| No PHI entities detected | Forward prompt to Bedrock | Log: allowed, timestamp, user, prompt hash |
| PHI detected (high confidence ≥0.9) | Block prompt; notify researcher with explanation of what was found | Log: blocked, timestamp, user, entities detected, prompt hash |
| PHI detected (medium confidence 0.7–0.9) | Warn researcher; allow override with acknowledgment | Log: warned, timestamp, user, entities flagged, override decision |
| PHI detected (low confidence <0.7) | Forward prompt with flag for periodic review | Log: flagged, timestamp, user, entities suspected |

**Training integration:** The gatekeeper serves double duty — it's a technical control *and* a training tool. Every time a researcher sees "PHI detected in your prompt: MRN found," they learn to recognize PHI in contexts they hadn't considered.

### Research Environment Architecture

```
┌─────────────────────────────────────────────────────┐
│  AWS VPC (private subnets)                          │
│                                                     │
│  ┌───────────────────┐    ┌──────────────────────┐  │
│  │  EC2: IDE Host    │    │  EC2: Notebook Host  │  │
│  │  (Kiro or equiv   │    │  (JupyterHub /       │  │
│  │   VS Code Server) │    │   SageMaker)         │  │
│  │                   │    │                      │  │
│  │  Researchers      │    │  Researchers         │  │
│  │  connect via SSO  │    │  connect via SSO     │  │
│  └────────┬──────────┘    └──────────┬───────────┘  │
│           │                          │              │
│           ▼                          ▼              │
│  ┌─────────────────────────────────────────────┐    │
│  │  Gatekeeper Service (Lambda / sidecar)      │    │
│  │  Comprehend Medical PHI scanning            │    │
│  └────────────────────┬────────────────────────┘    │
│                       │                             │
│                       ▼                             │
│  ┌─────────────────────────────────────────────┐    │
│  │  Amazon Bedrock (BAA-covered)               │    │
│  │  LLM inference — no training on inputs      │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  RDS (PHI)   │  │  S3 (PHI │  │  CloudWatch  │  │
│  │  encrypted   │  │  landing │  │  + CloudTrail│  │
│  │              │  │  zone)   │  │  (audit)     │  │
│  └──────────────┘  └──────────┘  └──────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘

External access:
  - Researchers (UW, FH) connect via SSO + MFA
  - No data egress; no download capability
  - External AI services (ChatGPT, etc.) blocked at network level
```

**Key design decisions:**
- All compute runs within the VPC — PHI never leaves the AWS boundary
- Researchers connect remotely (browser-based IDE/notebook); no local data
- AI services are internal (Bedrock) with gatekeeper; external AI blocked
- The collaborator (FH) accesses the same environment as UW researchers, under the same controls
- Network egress rules prevent data exfiltration (no arbitrary outbound internet from research hosts)
- GitHub is accessible from research compute (for git push/pull of code only); enforced via VPC endpoint or security group allowlist
- **No general browser access from research environment** (conservative choice — eliminates clipboard-proximity risk between PHI and external services). Researchers use their laptops for web browsing, literature search, and external AI tools. See note below.

> [i] **DESIGN CHOICE:** No general internet from research compute is the conservative option presented here. An alternative is "policy-only" (allow browser access, rely on training and policy to prevent PHI leakage to external services). Policy-only is simpler to implement but carries greater risk — it depends entirely on human discipline and cannot be technically audited. The conservative choice simplifies network architecture and eliminates an entire class of accidental disclosure.

---

## Raw PHI Upload Path Security

### Context

UW IT extracts raw PHI (full identifiers for 10,000 patients) from the institutional clinical database and uploads it to the project's AWS S3 landing zone. This is the highest-risk data movement in the project lifecycle — raw PHI traversing from an on-premises system to cloud storage.

### Upload Path Requirements

| Requirement | Implementation | HIPAA Basis |
|-------------|----------------|-------------|
| **Encryption in transit** | TLS 1.2+ enforced on S3 endpoint; bucket policy denies non-HTTPS requests | Technical Safeguard: Transmission Security |
| **Encryption at rest** | S3 bucket uses SSE-KMS with project-specific CMK; key policy restricts decrypt to authorized roles only | Technical Safeguard: Encryption |
| **Access control (upload)** | Dedicated IAM role for UW IT upload; scoped to PutObject on landing zone prefix only; no read/list/delete permissions | Technical Safeguard: Access Control |
| **Access control (read)** | Separate IAM roles for researchers; cannot access landing zone directly (data moves to processed zone after validation) | Administrative Safeguard: Minimum Necessary |
| **Integrity verification** | S3 checksums (SHA-256) computed at upload; verified after transfer; manifest file lists expected objects and checksums | Technical Safeguard: Integrity Controls |
| **Audit logging** | S3 access logging + CloudTrail data events on the bucket; every PutObject recorded with source IP, IAM identity, timestamp | Technical Safeguard: Audit Controls |
| **Versioning** | S3 versioning enabled; prevents accidental overwrite or deletion; supports recovery | Technical Safeguard: Integrity Controls |
| **Lifecycle** | Landing zone objects move to processed zone after validation; originals retained per retention policy then expired | Administrative Safeguard: Data Retention |

### Upload Workflow

```
UW IT (on-premises)                         AWS (project environment)
─────────────────────                       ─────────────────────────
1. Extract data from clinical DB
2. Generate manifest (file list + SHA-256 checksums)
3. Assume dedicated upload IAM role (via SSO/federation)
4. Upload files to s3://[bucket]/landing/ via TLS
   - AWS CLI with --checksum-algorithm SHA256
   - Or AWS Transfer Family (SFTP endpoint) if preferred
5. Upload manifest file
                                            6. S3 event triggers validation Lambda
                                            7. Lambda verifies:
                                               - All expected files present (per manifest)
                                               - Checksums match
                                               - File sizes within expected range
                                            8. If valid:
                                               - Move to s3://[bucket]/validated/
                                               - Notify PI + IT Staff (SNS)
                                               - Log: upload complete, verified
                                            9. If invalid:
                                               - Quarantine files
                                               - Alert IT Staff
                                               - Log: validation failure, details
```

### Separation of Zones

| S3 Prefix | Purpose | Who Can Access | Permissions |
|-----------|---------|----------------|-------------|
| `/landing/` | Raw upload target | UW IT (write only); validation Lambda (read) | PutObject (IT); GetObject (Lambda) |
| `/validated/` | Verified raw PHI | IT Staff, PI (admin); researchers (via processed views) | Restricted; not directly queried by researchers |
| `/processed/` | Transformed/analysis-ready data | Researchers (read); processing pipelines (write) | GetObject scoped by role |
| `/derived/` | Research outputs, intermediate results | Researchers (read/write within scope) | Scoped by project/study |
| `/audit/` | Upload manifests, validation logs | PI, compliance review | Read-only; append-only for new logs |

### Handoff Protocol

The upload is not a "fire and forget" operation. It requires a documented handoff:

1. **UW IT confirms upload:** "N files uploaded, manifest attached, checksums computed"
2. **Validation service confirms integrity:** Automated verification; notification sent
3. **Dr. D.R. Smith (PI) acknowledges receipt:** "Data received, validated, ready for processing"
4. **Audit record created:** Timestamp, parties, file count, validation status

This three-party confirmation (uploader → system → recipient) creates the audit trail needed to demonstrate chain of custody for the PHI.

---

## Infrastructure as Code (IaC) Considerations

**Build tool:** AWS CDK (Cloud Development Kit) in Python. CDK allows the team to define all infrastructure programmatically in a language they already use for research. Under the hood, CDK compiles to CloudFormation templates — giving 100% AWS service coverage and AWS-managed state tracking. The zero-console philosophy is enforced: infrastructure is defined in code, version-controlled in GitHub, and deployed via CI/CD. No one logs into the AWS portal to create or modify resources.

**Maintain tool:** AWS Config. Once infrastructure is built, Config continuously evaluates resources against compliance rules (encryption enabled? security groups locked down? CloudTrail active?). The HIPAA conformance pack provides ~70 pre-built rules. Config detects drift — if a resource is changed outside of CDK (which shouldn't happen, but Config catches it if it does) — and alerts via Security Hub.

**Relationship:** CDK = "build it right." Config = "verify it stays right."

**Alternative:** OpenTofu (open-source Terraform fork) is a viable alternative with multi-cloud capability and a large module ecosystem. It uses HCL (a declarative language) rather than Python, and requires self-managed state (S3 + DynamoDB). Appropriate if the team prefers declarative infrastructure or needs portability beyond AWS. For this AWS-only, Python-native project, CDK is the better fit.

**Why not Terraform:** HashiCorp changed Terraform's license to BSL (Business Source License) in 2023. OpenTofu is the community fork that remains open-source. We avoid Terraform for licensing reasons.

---

## AWS Account Structure

### Design Choice: Three Accounts (no Dev/Test)

| Account | Owner/Operator | Purpose |
|---------|---------------|---------|
| **Management** | UW IT (shared across projects) | AWS Organizations root, billing, Service Control Policies, account provisioning |
| **Production** | Project team (Dr. D.R. Smith, IT Staff) | PHI data, research compute, Bedrock, EFS, all research workloads |
| **Audit** | Project team (Dr. D.R. Smith, IT Staff) | CloudTrail logs, Config history, compliance evidence, gatekeeper logs |

> [i] **TEACHING NOTE:** A Dev/Test account is omitted here as a conscious choice. In this project, synthetic data is treated as real PHI from day one — there is no "safe" environment where you can experiment without compliance controls. This is intentional: it forces the team to learn compliant workflows from the start rather than developing habits in a permissive environment that must later be unlearned. A real project with budget and timeline pressure might add a Dev/Test account for infrastructure experimentation (testing CDK stacks, trying new services) before deploying to Production. The tradeoff is complexity vs. safety margin.

### Management Account: Shared, Not Project-Owned

The Management account is operated by UW IT and shared across all projects within the university's AWS Organization. This is a pre-existing institutional resource (like the BAA itself), not a project deliverable.

**What UW IT provides via the Management account:**
- AWS Organizations membership (the project's accounts are member accounts)
- Service Control Policies (institutional guardrails applied to all member accounts)
- Account provisioning (the project requests accounts; UW IT creates them)
- Billing consolidation
- Institutional-level security baselines (e.g., "no resources outside us-west-2")

**What the project does NOT control:**
- The Management account itself
- SCPs that apply organization-wide
- Billing and cost allocation at the organizational level

**Risk assessment of shared Management:**
- A compromised Management account could weaken SCPs protecting this project — but this is UW IT's responsibility to protect, and it's the same trust model as the BAA relationship
- The Management account cannot access data in member accounts unless explicitly granted (which it should not be)
- This is the standard university model: institutional IT provides the organizational shell; projects operate within it

### Production Account: Project-Owned

All PHI and research workloads live here. The project team (PI + IT Staff) has full administrative control within the boundaries set by UW IT's SCPs.

**Contains:**
- VPC and all networking (subnets, security groups, NACLs, flow logs)
- S3 buckets (landing zone, validated, processed, derived)
- RDS database (structured PHI)
- EC2 instances (IDE hosts, notebook servers, processing)
- EFS (shared filesystem)
- KMS keys (encryption for all data at rest)
- Bedrock access (AI inference)
- Comprehend Medical (gatekeeper)
- Lambda functions (gatekeeper logic, upload validation)
- ECS/Fargate (container workloads)
- Wickr (team communication)
- GuardDuty, Macie, Security Hub (threat detection, data discovery)

### Audit Account: Project-Owned, Isolated from Production

The Audit account stores all compliance evidence. It is deliberately separated from Production so that administrators and researchers in the Production account cannot tamper with audit logs — even accidentally.

**Contains:**
- CloudTrail logs (copied from Production via Organization trail or cross-account delivery)
- AWS Config history and compliance snapshots
- Gatekeeper decision logs (replicated from Production)
- VPC Flow Logs (archived)
- Access review records
- Incident reports

**Access model:**
- Production account roles **cannot** write to or delete from the Audit account
- Audit account has read-only access to Production (for Config evaluation)
- PI and compliance reviewers can read Audit account contents
- IT Staff administers the Audit account infrastructure but does not routinely access log content
- Logs are immutable: S3 Object Lock or versioning with MFA Delete enabled

**Why separate:** If a Production admin account is compromised, the attacker cannot destroy the evidence of their actions. The audit trail survives independently.

---

## Service Control Policies (SCPs)

SCPs are guardrails applied by the Management account (UW IT) to all member accounts in the AWS Organization. They define the *ceiling* of what is permitted — even a full administrator in the Production account cannot exceed what the SCP allows.

**How SCPs work:**
- SCPs are attached to the Organization root, organizational units (OUs), or individual accounts
- They are *inherited* downward: a policy on the root applies to all accounts; a policy on an OU applies to all accounts in that OU
- SCPs restrict but never grant — they narrow the effective permissions of IAM policies within the account
- If an SCP denies an action, no IAM policy in the member account can override it

**Expected SCPs for this project (to be confirmed with UW IT):**

> [i] **GENERIC:** The specific SCPs applied depend on UW IT's organizational policies. The following are representative guardrails typical for a HIPAA-aligned AWS Organization. The project team should request the actual SCP manifest from UW IT and document it here.

| SCP | Purpose | Effect |
|-----|---------|--------|
| **Region restriction** | Limit resource creation to approved regions (us-west-2, possibly us-east-1 for global services) | Prevents data from being created in unapproved geographic locations |
| **Deny public S3** | Prevent any S3 bucket from being made publicly accessible | Eliminates accidental public exposure of PHI |
| **Require encryption** | Deny creation of unencrypted storage (S3, EBS, RDS) | Enforces encryption at rest universally |
| **Deny CloudTrail disable** | Prevent member accounts from stopping or deleting CloudTrail trails | Protects audit integrity |
| **Deny leaving Organization** | Prevent member accounts from removing themselves from the Organization | Maintains institutional governance |
| **Deny root user actions** | Restrict or alert on root user activity in member accounts | Root credentials should never be used operationally |
| **Require MFA** | Deny sensitive actions without MFA | Enforces multi-factor authentication for critical operations |

**Project responsibility:** The project team does not create or manage SCPs — that's UW IT's domain. The project team's responsibility is to:
1. Request the SCP manifest from UW IT (know what guardrails are in place)
2. Verify that project infrastructure operates within SCP boundaries (CDK deployments won't fail due to SCP denials)
3. Document the SCPs as compliance evidence ("these institutional guardrails protect the project environment")

---

## VPC and Network Architecture

### Region

**Primary region:** `us-west-2` (Oregon) — closest to UW, well-supported, all required services available, HIPAA-eligible.

> [i] **NOTE:** If a required service proves to be unavailable in us-west-2 (rare but possible for newer services), the project may need to enable a secondary region. This would require: SCP amendment from UW IT, cross-region encryption key replication, and documentation of why the additional region is necessary. Treat as an exception requiring PI approval.

### Subnet Layout

| Subnet Type | Used? | Contains | Internet Access |
|-------------|-------|----------|-----------------|
| **Private subnets** | [x] Yes | All resources: EC2, RDS, EFS, Lambda, ECS, VPC Endpoints | Outbound via NAT Gateway (restricted to GitHub IPs and AWS service endpoints only) |
| **Isolated subnets** | [ ] No | — | — |
| **Public subnets** | [ ] No | — | — |

> [i] **TEACHING NOTE — Design choices:**
> - **No isolated subnets:** Isolated subnets (no NAT, no internet at all) would prevent resources from reaching *any* external endpoint, including AWS services without VPC Endpoints. Since we need connectivity to Bedrock, Comprehend Medical, GitHub, and other services, private subnets with controlled egress are sufficient. The VPC Endpoints provide private paths to AWS services; the NAT Gateway (with restrictive rules) handles GitHub. If a future requirement demands a resource with *zero* outbound connectivity, an isolated subnet can be added.
> - **No public subnets:** No resource in this environment needs to be directly reachable from the internet. Researchers connect via AWS SSO + Session Manager (or a browser-based IDE), which does not require inbound internet access to the VPC. There are no load balancers, no public APIs, no bastion hosts. This eliminates an entire attack surface.
> - **Potential issue:** If a service requires inbound internet connectivity in the future (e.g., a webhook receiver, a public-facing API for collaboration), a public subnet would need to be added. For now, there is no such requirement.

### VPC Endpoints (Private AWS Service Access)

**Concept:** A VPC Endpoint creates a private connection between the VPC and an AWS service. Traffic between the VPC and the service stays within the AWS network — it does not traverse the public internet. This is how compute instances in private subnets (with no internet gateway) reach AWS services.

**Clarification on "doesn't traverse the internet":** When an EC2 instance (or a container on ECS) makes a Bedrock API call, that call travels through the VPC Endpoint directly to the Bedrock service within AWS's internal network. It never touches the public internet. This is separate from the researcher's laptop-to-EC2 connection (which goes over the internet via SSO/Session Manager, encrypted). The VPC Endpoint concern is about *service-to-service* traffic within AWS, not *user-to-service* access.

**Required VPC Endpoints:**

| Service | Endpoint Type | Why Needed |
|---------|--------------|------------|
| **S3** | Gateway | PHI storage access (landing zone, validated, processed, derived, audit) |
| **RDS** | Not needed (RDS is deployed *within* the VPC) | Database is a VPC resource, not an external service |
| **Bedrock** | Interface | LLM inference from compute instances; prompts stay within AWS network |
| **Comprehend Medical** | Interface | PHI detection (gatekeeper) from Lambda/compute |
| **SageMaker** (API + Runtime) | Interface | Notebook access, model training, inference |
| **KMS** | Interface | Encryption/decryption operations from all services |
| **CloudTrail** | Interface | Log delivery (though typically configured at account level) |
| **CloudWatch Logs** | Interface | Log shipping from compute instances and Lambda |
| **ECR** | Interface (ecr.api + ecr.dkr) | Container image pull from ECS/Fargate tasks |
| **ECS** | Interface | Task management, service discovery |
| **Lambda** | Interface | Invocation and management (if invoking cross-service) |
| **SNS** | Interface | Notification delivery from within VPC |
| **Secrets Manager** | Interface | Runtime secret injection into containers/compute |
| **SSM (Systems Manager)** | Interface | Session Manager access (how researchers connect to EC2 without SSH/bastion) |
| **STS** | Interface | IAM role assumption, temporary credential generation |

**Services that do NOT need VPC Endpoints:**
- **EFS** — deployed within the VPC; mount targets are VPC resources
- **RDS** — deployed within the VPC; accessed via private IP
- **GuardDuty, Macie, Config, Security Hub** — these are account-level services that operate on metadata; they don't need to be "reached" from compute instances

### GitHub Access (NAT Gateway with Restrictions)

GitHub is the one external service that compute instances need to reach (for `git push/pull`). Since GitHub is not an AWS service, it cannot be accessed via a VPC Endpoint.

**Solution:** A NAT Gateway in the private subnet provides outbound internet access, but security group and NACL rules restrict outbound traffic to:
- GitHub IP ranges (published by GitHub: `api.github.com`, `github.com`, `*.githubusercontent.com`)
- HTTPS only (port 443)
- All other outbound traffic denied

This gives git operations a path out while blocking general internet browsing, external AI services, and arbitrary data exfiltration.

> [i] **ALTERNATIVE:** AWS CodeCommit (AWS-native git) could replace GitHub entirely, eliminating the need for any NAT Gateway. The tradeoff: CodeCommit has a smaller ecosystem and less collaboration tooling than GitHub. For a team already using GitHub, the NAT-with-restrictions approach is more practical.

### Researcher Access Path (Laptop → EC2)

```
Researcher laptop (browser)
        │
        ▼ (HTTPS, internet)
AWS SSO login portal
        │
        ▼ (authenticated, MFA verified)
AWS Systems Manager Session Manager
        │
        ▼ (SSM endpoint within VPC — no inbound ports needed)
EC2 instance (IDE host / notebook)
        │
        ▼ (private network, within VPC)
All services (RDS, S3, Bedrock, EFS, etc.)
```

**Key point:** The researcher's connection enters AWS via SSO (authentication) and reaches the EC2 instance via Session Manager. The EC2 instance has *no public IP* and *no inbound security group rules*. Session Manager uses the SSM VPC Endpoint — the connection is brokered by AWS, not by opening a port. This eliminates SSH key management, bastion hosts, and inbound firewall rules entirely.

---

## IAM Architecture

### Design Principles

- **Least privilege:** Each role gets the minimum permissions needed for its function
- **Separation of duties:** Infrastructure administration is separated from research data access; no single role can both modify the system and access PHI
- **Role-based, not person-based:** Permissions are attached to roles; people assume roles. When a person leaves, their role assignment is revoked — the role definition doesn't change
- **Federation:** All human access is via UW SSO (or FH identity federation for Co-PI). No long-lived AWS credentials. MFA required for all sessions.

### Role Mapping

| Person(s) | IAM Role | Purpose |
|-----------|----------|---------|
| Dr. D.R. Smith (PI) | `ProjectAdmin` | Full project governance: manage IAM, approve access, review audit, administer both Production and Audit accounts |
| IT Staff | `InfraAdmin` | Infrastructure deployment and maintenance: CDK, networking, compute, storage, monitoring. No PHI data access. |
| Postdoc | `SeniorResearcher` | Full research access: query data, use notebooks, use Bedrock, read/write EFS |
| Co-PI (FH) | `SeniorResearcher` | Identical to Postdoc; federated from FH identity provider; enhanced session logging |
| Students (1–3) | `Researcher` | Research access: query data (study cohort), use notebooks, use Bedrock, read/write EFS |

### Role Permissions Detail

#### `ProjectAdmin`

| Permission Area | Access | Rationale |
|-----------------|--------|-----------|
| IAM management | Full (create/modify roles, policies, users) | PI provisions and revokes access |
| S3 (all zones) | Full (read/write/delete/admin) | PI oversees all data lifecycle |
| RDS | Full (admin + query) | PI can access data and manage database |
| EC2 / ECS | Full (start/stop/terminate/configure) | PI can manage compute resources |
| KMS | Full (create keys, manage policies, encrypt/decrypt) | PI manages encryption lifecycle |
| CloudTrail / CloudWatch | Full read (Production + Audit accounts) | PI reviews audit logs |
| Bedrock | Invoke (via gatekeeper) | PI can use AI tools for research |
| Audit account | Full admin | PI manages compliance evidence |
| Cost/billing | Read (within project scope) | PI monitors budget |

#### `InfraAdmin`

| Permission Area | Access | Rationale |
|-----------------|--------|-----------|
| IAM management | Limited (execute provisioning per PI approval; cannot self-escalate) | IT provisions access but PI approves |
| S3 (landing zone) | Write (upload) | IT uploads PHI from clinical DB |
| S3 (other zones) | Admin (create/configure buckets, policies) but **no GetObject on PHI data** | IT manages storage infrastructure but doesn't read patient data |
| RDS | Admin (create/configure/backup) but **no SELECT on PHI tables** | IT manages database infrastructure but doesn't query patient records |
| EC2 / ECS | Full (deploy, configure, patch, terminate) | IT manages compute |
| EFS | Admin (create/configure filesystem) but **no read of researcher files** | IT manages filesystem infrastructure |
| KMS | Admin (create keys, set rotation) but **cannot decrypt PHI data keys** | IT manages key infrastructure; decryption restricted to research roles |
| VPC / networking | Full | IT manages network architecture |
| CloudTrail / CloudWatch | Read (operational logs for troubleshooting) | IT monitors system health |
| Bedrock | No access | IT does not do research |
| CDK deployment | Full (CloudFormation create/update/delete) | IT deploys infrastructure |

> [i] **TEACHING NOTE — Separation of duties:** The `InfraAdmin` role is deliberately designed so that IT Staff can build and maintain the entire system without ever seeing patient data. This is enforced technically (IAM policies deny data-plane access) not just by policy. If IT Staff needs to troubleshoot a data issue, they escalate to the PI who can query the data. This separation means a compromised IT credential cannot exfiltrate PHI — it can only affect infrastructure.

#### `SeniorResearcher` (Postdoc + Co-PI)

| Permission Area | Access | Rationale |
|-----------------|--------|-----------|
| S3 (processed + derived) | Read + write (within project scope) | Access analysis-ready data and store results |
| S3 (landing + validated) | No access | Raw upload zone is IT/PI only |
| RDS | SELECT on study cohort views only | Query patient data through minimum-necessary views |
| EC2 (IDE + notebook) | Connect via Session Manager; no admin | Use compute but cannot modify infrastructure |
| EFS | Read/write (shared research directories) | Collaborative working space |
| Bedrock | Invoke (via gatekeeper only) | AI-assisted research |
| SageMaker | Full notebook use; model training within VPC | ML workflows |
| KMS | Decrypt (data keys only, via service roles) | Transparent — decryption happens automatically when accessing encrypted data |
| IAM | No access | Cannot modify permissions |
| Infrastructure | No access | Cannot modify VPC, security groups, etc. |
| Audit account | No access | Cannot view or tamper with audit logs |

#### `Researcher` (Students)

| Permission Area | Access | Rationale |
|-----------------|--------|-----------|
| Same as `SeniorResearcher` | Same | Students see the same study cohort data |
| Difference | None currently | All students have identical access to the full study cohort |

> [i] **NOTE:** `Researcher` and `SeniorResearcher` currently have identical data access. The distinction exists for: (a) future scoping if students are assigned to subsets, (b) governance clarity (the Postdoc can serve as deputy for operational decisions), and (c) audit trail differentiation (actions by students vs. senior researchers are distinguishable in logs).

### Federation and Authentication

| Person | Identity Source | Authentication Path |
|--------|----------------|---------------------|
| PI, Postdoc, Students, IT Staff | UW SSO (SAML/OIDC federation to AWS IAM Identity Center) | UW login → MFA → AWS session → assume role |
| Co-PI (FH) | FH identity provider (federated via AWS IAM Identity Center as external IdP) | FH login → MFA → AWS session → assume `SeniorResearcher` role |

**Session controls:**
- Maximum session duration: 8 hours (re-authentication required daily)
- MFA required for every new session
- Session logging: all Session Manager connections logged to CloudTrail
- IP restrictions: optional — can restrict to UW/FH campus IP ranges if desired (tradeoff: breaks remote work)

### Service Roles (non-human)

In addition to human roles, AWS services need IAM roles to operate:

| Service Role | Attached To | Permissions |
|--------------|-------------|-------------|
| `GatekeeperLambdaRole` | Gatekeeper Lambda function | Invoke Comprehend Medical; invoke Bedrock; write to CloudWatch Logs; write to DynamoDB (gatekeeper decisions) |
| `ValidationLambdaRole` | Upload validation Lambda | Read S3 landing zone; write S3 validated zone; publish to SNS; write CloudWatch Logs |
| `ECSTaskRole` | Container tasks (processing pipelines) | Read S3 processed; write S3 derived; query RDS (via study views); write CloudWatch Logs |
| `ConfigRole` | AWS Config | Read-only access to all resources (for compliance evaluation) |
| `CloudTrailRole` | CloudTrail | Write to Audit account S3 bucket (log delivery) |

### Access Provisioning Workflow

```
1. PI approves access (documented: who, what role, justification)
2. IT Staff creates IAM Identity Center assignment (person → role)
3. Assignment logged in CloudTrail
4. Person receives notification (Wickr): "Your access is provisioned"
5. Person authenticates via SSO + MFA → assumes assigned role
6. Monthly review: PI verifies all active assignments still justified
```

### Access Revocation

| Trigger | Action | Timeline |
|---------|--------|----------|
| Person leaves project | IT Staff removes Identity Center assignment | Within 24 hours of notification |
| Role change | IT Staff modifies assignment; PI approves | Same day |
| Policy violation | PI directs IT Staff to suspend assignment | Immediate |
| Monthly review finds unjustified access | PI directs revocation | Within 48 hours of review |

---

## KMS Encryption Architecture

### Design Principles

- **Encrypt everything at rest** — all PHI storage (S3, RDS, EFS, EBS) uses KMS-managed encryption. No unencrypted PHI exists anywhere in the environment.
- **Separate keys by function** — different keys for different data classifications. A compromised key exposes only the data it protects, not everything.
- **Key policies enforce access control** — even if an IAM policy grants broad S3 access, the user cannot read encrypted data unless the KMS key policy also grants them decrypt permission. This is defense in depth.
- **Automatic rotation** — keys rotate annually (AWS manages the rotation; old ciphertext remains decryptable with previous key material).
- **Deletion is irreversible** — scheduling a key for deletion (Phase 6: Decommission) permanently destroys access to all data encrypted with that key. This is the ultimate data disposition mechanism.

### Key Hierarchy

| Key Alias | Protects | Who Can Encrypt | Who Can Decrypt | Rotation |
|-----------|----------|-----------------|-----------------|----------|
| `phi-data-key` | S3 (validated, processed, derived zones), RDS, EFS | `InfraAdmin` (initial setup), service roles (write operations) | `ProjectAdmin`, `SeniorResearcher`, `Researcher`, service roles (read operations) | Annual (automatic) |
| `phi-landing-key` | S3 landing zone (raw upload) | `InfraAdmin` (upload role) | `ValidationLambdaRole`, `ProjectAdmin` | Annual (automatic) |
| `audit-key` | Audit account: CloudTrail logs, Config snapshots, gatekeeper logs | `CloudTrailRole`, `ConfigRole`, `GatekeeperLambdaRole` | `ProjectAdmin` (compliance review only) | Annual (automatic) |
| `infra-key` | EBS volumes (EC2 root/data volumes), ECR images, Secrets Manager | `InfraAdmin`, service roles | `InfraAdmin`, service roles, compute instances (transparent) | Annual (automatic) |

### Why Four Keys (Not One)

A single key for everything would be simpler but violates least-privilege:
- **`phi-data-key`** — the main research data key. Researchers can decrypt (they need to read data). IT Staff *cannot* decrypt (separation of duties).
- **`phi-landing-key`** — protects raw uploads before validation. Only the upload role and validation Lambda can interact with it. Researchers never touch the landing zone.
- **`audit-key`** — protects compliance evidence. Only the PI can decrypt for review. Researchers and IT Staff cannot read audit logs (prevents tampering awareness).
- **`infra-key`** — protects infrastructure artifacts (boot volumes, container images, secrets). IT Staff can decrypt (they manage infrastructure). This key does not protect PHI directly.

### Key Policies (Conceptual)

Each key has a resource policy that defines who can use it. These are *in addition to* IAM policies — both must allow the action.

**`phi-data-key` policy:**
```
Allow encrypt: InfraAdmin, ECSTaskRole, ValidationLambdaRole
Allow decrypt: ProjectAdmin, SeniorResearcher, Researcher, ECSTaskRole
Allow admin:   ProjectAdmin
Deny:          InfraAdmin decrypt (explicit deny — cannot read PHI)
```

**`phi-landing-key` policy:**
```
Allow encrypt: InfraAdmin (upload role)
Allow decrypt: ValidationLambdaRole, ProjectAdmin
Allow admin:   ProjectAdmin
Deny:          SeniorResearcher, Researcher (no access to landing zone)
```

**`audit-key` policy:**
```
Allow encrypt: CloudTrailRole, ConfigRole, GatekeeperLambdaRole
Allow decrypt: ProjectAdmin only
Allow admin:   ProjectAdmin
Deny:          All other roles (audit logs are PI-eyes-only for review)
```

**`infra-key` policy:**
```
Allow encrypt: InfraAdmin, service roles
Allow decrypt: InfraAdmin, service roles, compute instances
Allow admin:   ProjectAdmin, InfraAdmin
```

### Rotation

AWS KMS automatic key rotation:
- Generates new key material annually
- Old key material is retained (old ciphertext can still be decrypted)
- New data is encrypted with the new material
- No action required from the team — rotation is transparent
- Rotation events are logged in CloudTrail (compliance evidence)

### Key Deletion (Decommission)

During Phase 6 (Decommission), keys are scheduled for deletion:
- AWS enforces a mandatory waiting period (minimum 7 days, configurable up to 30 days)
- During the waiting period, deletion can be cancelled (safety net)
- After the waiting period, the key is permanently destroyed
- All data encrypted with that key becomes permanently inaccessible — this is *cryptographic erasure*
- Key deletion is logged in CloudTrail
- Deletion schedule is documented as part of the data destruction certification

**Order of operations for decommission:**
1. Verify all data that needs to be retained has been decrypted and archived elsewhere (or confirm nothing needs retention)
2. Schedule `phi-data-key` for deletion (30-day wait recommended)
3. Schedule `phi-landing-key` for deletion
4. Schedule `infra-key` for deletion
5. `audit-key` is retained longest — audit logs must be accessible for the HIPAA retention period (6–7 years). This key is deleted only after the retention period expires.

### Relationship to Services

| Service | Key Used | How Encryption Works |
|---------|----------|---------------------|
| **S3** | `phi-landing-key` or `phi-data-key` (by prefix) | SSE-KMS: S3 calls KMS to encrypt/decrypt objects transparently |
| **RDS** | `phi-data-key` | RDS encrypts storage, backups, and snapshots using the key |
| **EFS** | `phi-data-key` | EFS encrypts file data and metadata at rest |
| **EBS** | `infra-key` | EC2 boot volumes and attached storage encrypted |
| **CloudTrail logs** | `audit-key` | Logs encrypted at delivery to S3 |
| **CloudWatch Logs** | `audit-key` | Log groups encrypted with specified key |
| **Secrets Manager** | `infra-key` | Secrets (database passwords, API keys) encrypted at rest |
| **ECR** | `infra-key` | Container images encrypted in registry |

> [i] **TEACHING NOTE:** KMS encryption is largely transparent to researchers. They don't manually encrypt or decrypt — services handle it automatically based on key policies. A researcher querying RDS sees plaintext results because their IAM role + the key policy together authorize decryption. If their role were revoked, the same query would fail — not because the data disappeared, but because the key policy no longer grants them decrypt. This is why KMS is a *second layer* of access control beyond IAM.

---

## Compute Architecture

### Design Principles

- **Per-researcher IDE instances** — each researcher gets their own EC2 instance running the IDE (Kiro or VS Code Server). Avoids multi-tenancy conflicts, simplifies permissions, and allows individual instance sizing if needed later.
- **SageMaker for notebooks** — managed service with built-in VPC mode, IAM integration, and per-user instances. Reduces operational burden on IT Staff.
- **ECS/Fargate for batch processing** — ephemeral containers that scale to zero when idle. Cost-efficient for pipeline workloads.
- **Start small, scale later** — initial sizing is modest (10K patients is not a large-data problem). The architecture accommodates growth (fMRI scans, larger cohorts, ML training) by resizing instances or adding capacity without redesigning the system.

> [i] **TEACHING NOTE:** The initial system will almost certainly require modification as the project evolves. Data volumes may grow (imaging data, longitudinal records), compute needs may increase (ML training, large-scale analysis), and new services may be needed. The architecture is designed to accommodate this: instances can be resized, new instances added, and services enabled without rebuilding the foundation. Plan for change; don't over-provision at the start.

### IDE Instances (Per-Researcher EC2)

| Attribute | Value |
|-----------|-------|
| **Instance type (initial)** | `m5.xlarge` (4 vCPU, 16GB RAM) — adequate for code editing, moderate data manipulation, AI-assisted development |
| **One per researcher** | PI, Postdoc, Co-PI, Students 1–3 = 6 instances (IT Staff does not need an IDE for research) |
| **Storage** | EBS root volume (encrypted with `infra-key`) + EFS mount (shared working space) |
| **OS** | Amazon Linux 2023 or Ubuntu 22.04 LTS |
| **IDE** | Kiro or VS Code Server (browser-based access via Session Manager port forwarding) |
| **Access** | Via AWS Systems Manager Session Manager — no SSH, no public IP, no inbound ports |
| **Lifecycle** | Auto-start/stop on schedule (see Cost Management below) |

### SageMaker Notebooks

**How researchers access SageMaker:**

SageMaker notebook instances provide a browser-based Jupyter environment. The access path is:

```
Researcher laptop (browser)
        │
        ▼ (HTTPS, internet)
AWS Console / SageMaker presigned URL
        │
        ▼ (authenticated via SSO, MFA verified)
SageMaker notebook instance (running in VPC, private subnet)
        │
        ▼ (Jupyter served over HTTPS via AWS-managed proxy)
Notebook interface in browser
```

The researcher does **not** connect to a port on an EC2 instance directly. Instead:
- SageMaker generates a **presigned HTTPS URL** (time-limited, authenticated)
- The researcher clicks this URL (from the AWS console or a bookmarked link)
- AWS's managed infrastructure proxies the Jupyter interface to the researcher's browser over HTTPS
- The notebook instance itself runs in the VPC private subnet with no public IP
- All data access from the notebook (S3, RDS, EFS) stays within the VPC via private networking

This is different from self-hosted Jupyter where you'd SSH-tunnel to port 8888. SageMaker handles the secure proxying for you.

**Customizing the SageMaker environment (installing libraries):**

SageMaker provides several mechanisms for environment customization:

| Method | Use Case | Persistence |
|--------|----------|-------------|
| **Lifecycle configuration scripts** | Run shell commands at instance creation or start (e.g., `pip install networkx`) | Persists across restarts if in "on-create" script |
| **Custom conda environments** | Create a conda env with all needed packages; register as a Jupyter kernel | Persists on the instance's EBS volume |
| **Custom Docker image** | Build a container with all libraries pre-installed; use as SageMaker notebook image | Fully reproducible; version-controlled |
| **requirements.txt in notebook** | `!pip install -r requirements.txt` in first cell | Per-session (lost on restart unless in lifecycle script) |

**Recommended approach for this project:** Use a **lifecycle configuration script** that installs the project's standard library set (NetworkX, pandas, scikit-learn, etc.) at instance creation. Store the script in the GitHub repo so it's version-controlled. For heavier customization (custom C libraries, specific CUDA versions), use a custom Docker image registered with SageMaker.

**Configuration:**

| Attribute | Value |
|-----------|-------|
| **Instance type (initial)** | `ml.t3.medium` (2 vCPU, 4GB RAM) for exploratory work; `ml.m5.xlarge` for heavier analysis |
| **One per researcher** | Each researcher gets their own notebook instance |
| **VPC mode** | Enabled — instance runs in private subnet; no direct internet access |
| **EFS mount** | Shared filesystem mounted for collaborative access to working files |
| **Root volume** | Encrypted (KMS) |
| **Idle timeout** | Auto-stop after 60 minutes of inactivity (cost management) |

> [i] **NOTE:** SageMaker is the starting point. If the team finds SageMaker's managed environment too restrictive (e.g., needs root access, custom kernels not supported, or specific GPU configurations), a self-managed JupyterHub on EC2 is the fallback. The architecture supports both — the VPC, IAM roles, and EFS mount work identically either way.

### Batch Processing (ECS/Fargate)

For data processing pipelines that run as jobs (not interactive):

| Attribute | Value |
|-----------|-------|
| **Orchestration** | ECS with Fargate launch type (serverless — no EC2 to manage) |
| **Scaling** | Scales to zero when no tasks running; scales up per job submission |
| **Container source** | ECR (images built via GitHub Actions CI/CD) |
| **IAM** | Per-task roles (`ECSTaskRole`) with least-privilege access to data |
| **Networking** | Tasks run in private subnets; access S3/RDS via VPC endpoints |
| **Cost** | Pay only for running tasks (no idle cost) |

### Cost Management: Auto-Start / Auto-Stop

EC2 IDE instances and SageMaker notebooks are expensive when running idle. The following schedule manages costs while preserving flexibility:

**Schedule (applied to all IDE EC2 instances):**

| Event | Time | Days | Mechanism |
|-------|------|------|-----------|
| **Auto-Start** | 6:00 AM Pacific | Mon–Fri | AWS EventBridge rule → Lambda → start instances |
| **Auto-Stop** | 6:00 PM Pacific | Mon–Fri | AWS EventBridge rule → Lambda → stop instances |
| **Weekend** | Stopped | Sat–Sun | No auto-start; manual start available |

**Override mechanisms:**

| Action | Who Can Do It | How |
|--------|---------------|-----|
| **Suspend Auto-Stop** (keep running overnight) | Any team member | Tag instance with `keep-alive=true` (via CLI, console, or Wickr bot command); Lambda checks tag before stopping |
| **Manual Start** (outside schedule) | Any team member | Start instance via CLI (`aws ec2 start-instances`) or Session Manager console; instance runs until next Auto-Stop unless tagged |
| **Resume Auto-Stop** | Automatic | `keep-alive` tag cleared at next morning's Auto-Start; or manually removed |

**SageMaker notebooks:** Use SageMaker's built-in auto-stop (idle timeout of 60 minutes) rather than the schedule-based approach. Notebooks are lighter-weight and start faster, so on-demand start/stop is more practical than a fixed schedule.

**Implementation:** A single Lambda function handles both start and stop, triggered by EventBridge scheduled rules. The function:
1. Lists all EC2 instances tagged `project=securecomputing` and `role=ide`
2. For stop events: checks for `keep-alive=true` tag; skips tagged instances; stops others
3. For start events: starts all instances; clears any `keep-alive` tags from previous night
4. Logs all actions to CloudWatch

> [i] **TEACHING NOTE:** Cost management is not optional for NIH-funded cloud projects. AWS charges by the hour for running instances. A `m5.xlarge` running 24/7 costs ~$140/month; running only business hours (Mon–Fri 6AM–6PM) costs ~$50/month. For 6 IDE instances, that's $540/month saved. The override mechanism ensures cost management doesn't block research — a researcher running a long job simply tags their instance and it stays up.

---

## Monitoring and Audit Stack

### Purpose

The monitoring stack provides four capabilities required by HIPAA and essential for the Black Hat Test:
1. **Audit trail** — who did what, when, from where (every API call logged)
2. **Threat detection** — anomalous behavior identified automatically
3. **Data exposure detection** — PHI found where it shouldn't be
4. **Compliance drift detection** — resources that deviate from security baselines

### Components

| Service | Layer | What It Detects | Alert Mechanism |
|---------|-------|-----------------|-----------------|
| **CloudTrail** | API logging | Every AWS API call (who, what, when, source IP) | Foundation — feeds other services; direct alerts via CloudWatch for specific events |
| **GuardDuty** | Threat intelligence | Anomalous API patterns, credential compromise, reconnaissance, data exfiltration attempts | Security Hub finding → SNS → Wickr notification |
| **Macie** | Data classification | PHI/sensitive data in unexpected S3 locations; unencrypted sensitive data | Security Hub finding → SNS → Wickr notification |
| **AWS Config** | Configuration compliance | Resources that violate rules (unencrypted bucket, open security group, disabled logging) | Config rule non-compliance → SNS → Wickr notification |
| **Security Hub** | Aggregation | Consolidates findings from GuardDuty, Macie, Config, and manual checks into one dashboard | Central view; severity-based alerting |
| **CloudWatch Logs** | Application logging | Gatekeeper decisions, application errors, access patterns | CloudWatch Alarms → SNS → Wickr notification |
| **VPC Flow Logs** | Network metadata | Connection attempts (allowed and denied), traffic patterns, potential exfiltration | Stored for forensic analysis; anomalies detected by GuardDuty |

### CloudTrail Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| **Trail scope** | Organization trail (all regions, all accounts) | No blind spots; covers Production + Audit accounts |
| **Data events** | Enabled for S3 (object-level) and Lambda (invocations) | Logs every PHI access (GetObject, PutObject) not just management operations |
| **Log destination** | S3 bucket in Audit account (cross-account delivery) | Logs isolated from Production; tamper-resistant |
| **Encryption** | `audit-key` (KMS) | Logs encrypted at rest; only PI can decrypt for review |
| **Log file validation** | Enabled | Detects if log files are modified or deleted after delivery |
| **Retention** | 7 years (HIPAA requirement) | S3 lifecycle: Standard → Glacier after 90 days → retain 7 years |

**What CloudTrail captures for the Black Hat Test:**
- Successful data access: "User jane.doe assumed role Researcher, called s3:GetObject on patient_data.parquet at 14:32:07 from IP 10.0.1.47"
- Failed access attempt: "User unknown attempted s3:GetObject on patient_data.parquet — AccessDenied at 03:17:42 from IP 203.0.113.99"

### GuardDuty Configuration

| Setting | Value |
|---------|-------|
| **Enabled in** | Production account + Audit account |
| **Data sources** | CloudTrail, VPC Flow Logs, DNS logs |
| **S3 protection** | Enabled (monitors S3 data plane for anomalies) |
| **EKS/ECS protection** | Enabled if EKS used; ECS runtime monitoring |
| **Malware protection** | Enabled for EBS volumes |

**Findings relevant to this project:**
- `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration` — someone trying to use EC2 credentials from outside AWS
- `Recon:IAMUser/MaliciousIPCaller` — API calls from known-bad IPs
- `Exfiltration:S3/MaliciousIPCaller` — S3 access from suspicious sources
- `UnauthorizedAccess:IAMUser/ConsoleLoginSuccess.B` — console login from unusual location

### Macie Configuration

| Setting | Value |
|---------|-------|
| **Enabled in** | Production account |
| **Scan scope** | All S3 buckets in Production account |
| **Schedule** | Daily automated discovery scan |
| **Custom identifiers** | UW MRN format (`[A-Z]\d{8}`), project-specific patterns |
| **Alerts on** | PHI found outside expected zones (e.g., in a "public" or misconfigured bucket); unencrypted sensitive data |

**Purpose for this project:** Macie validates that PHI is *where it should be* (encrypted, in the right S3 zones) and *not where it shouldn't be* (accidentally copied to an unprotected location, left in a temp bucket).

### AWS Config Rules

Config evaluates resources against rules continuously. The HIPAA conformance pack provides pre-built rules. Key rules for this project:

| Rule | What It Checks | Severity if Non-Compliant |
|------|---------------|---------------------------|
| `s3-bucket-server-side-encryption-enabled` | All S3 buckets encrypted | Critical |
| `s3-bucket-public-read-prohibited` | No public S3 buckets | Critical |
| `s3-bucket-public-write-prohibited` | No public write access | Critical |
| `rds-storage-encrypted` | RDS instances encrypted | Critical |
| `encrypted-volumes` | EBS volumes encrypted | Critical |
| `cloud-trail-enabled` | CloudTrail active | Critical |
| `cloud-trail-log-file-validation-enabled` | Log integrity checking | High |
| `iam-user-mfa-enabled` | MFA on all IAM users | High |
| `vpc-flow-logs-enabled` | Flow logs active on VPC | High |
| `restricted-ssh` | No SSH from 0.0.0.0/0 | High |
| `efs-encrypted-check` | EFS filesystems encrypted | Critical |
| `guardduty-enabled-centralized` | GuardDuty active | High |

**Remediation:** Config can trigger automatic remediation (via SSM Automation) for some rules — e.g., automatically enable encryption on a newly created unencrypted bucket. For this project, we use *detect and alert* rather than auto-remediate, to avoid unexpected changes. IT Staff remediates manually after investigation.

### Alert Flow

```
Detection (CloudTrail / GuardDuty / Macie / Config)
        │
        ▼
Security Hub (aggregates, deduplicates, assigns severity)
        │
        ▼
EventBridge rule (filters by severity: CRITICAL, HIGH)
        │
        ▼
SNS topic (project-security-alerts)
        │
        ├──► Wickr channel (team notification)
        ├──► Email to PI (backup)
        └──► CloudWatch Logs (alert history)
```

**Severity-based routing:**
- **CRITICAL** (e.g., public S3 bucket with PHI, disabled CloudTrail): Immediate alert to PI + IT Staff via Wickr; requires response within 1 hour
- **HIGH** (e.g., failed access attempts, GuardDuty finding): Alert to IT Staff via Wickr; requires triage within 4 hours
- **MEDIUM** (e.g., Config drift, Macie finding in expected location): Logged; reviewed in weekly security review
- **LOW** (e.g., informational findings): Logged only; reviewed monthly

### Response Timeline Definitions

| Severity | Example Triggers | Response Window | What "Response" Means | Who Responds |
|----------|-----------------|-----------------|----------------------|--------------|
| **CRITICAL** | Public S3 bucket containing PHI; CloudTrail disabled; active credential compromise | Within 1 hour | Contain immediately (fix the exposure, re-enable logging, revoke compromised credentials); notify PI; begin incident assessment | IT Staff (contain) + PI (assess severity, decide on breach notification) |
| **HIGH** | Repeated failed access from unknown IP; GuardDuty credential exfiltration finding; unauthorized role assumption attempt | Within 4 hours | IT Staff triages (real threat or false positive?); if real, contain and escalate to PI; document finding and action taken | IT Staff (triage) → PI (if escalated) |
| **MEDIUM** | Config drift (encryption disabled on new resource); Macie flags PHI in expected location; minor policy non-compliance | Within 1 week | Logged; reviewed in next scheduled weekly security review; remediated if needed; documented | IT Staff (remediate) at next review cycle |
| **LOW** | Informational findings (Config rule passed; routine scan completed; expected access patterns) | Monthly review | No action unless pattern emerges over time; reviewed in monthly aggregate | PI (monthly review) |

> [i] **TEACHING NOTE — Why these timelines?** HIPAA does not specify exact response times for security incidents (the only hard deadline is 60 days for breach notification to HHS after *discovery*). These timelines are project-defined and reflect what a 7-person research team can realistically commit to. The PI and IT Staff are the responders — there is no 24/7 SOC. A larger organization with dedicated security operations would set tighter windows (15 minutes for CRITICAL, 1 hour for HIGH). What matters for compliance is: (a) you defined the timelines, (b) you documented them, (c) you can demonstrate you follow them (the Phase 4 incident response drill validates this), and (d) you review and adjust them based on experience. An auditor asks "what are your response times?" — you point here. They ask "do you follow them?" — you point to the incident log and drill reports.

### Audit Account Log Architecture

```
Audit Account (S3)
├── cloudtrail/
│   ├── production-account/        ← All API calls from Production
│   │   ├── 2026/05/16/
│   │   └── ...
│   └── audit-account/             ← API calls within Audit account itself
├── config/
│   ├── snapshots/                 ← Resource configuration history
│   └── compliance/                ← Rule evaluation results
├── gatekeeper/
│   ├── decisions/                 ← Allow/block/warn logs from PHI gatekeeper
│   └── metrics/                   ← Aggregate statistics
├── flowlogs/
│   └── vpc-production/            ← Network traffic metadata
└── alerts/
    └── security-hub-findings/     ← Archived findings with resolution status
```

**Immutability controls:**
- S3 Object Lock (Governance mode): prevents deletion for retention period
- Versioning enabled: overwrites create new versions, don't destroy old ones
- MFA Delete: requires MFA to permanently delete any object version
- Bucket policy: denies `s3:DeleteObject` and `s3:PutBucketPolicy` from Production account roles
- Only `ProjectAdmin` (PI) can access Audit account for review

### Relationship to Black Hat Test

The monitoring stack is what makes the Black Hat Test possible:

| Black Hat Scenario | Detection Mechanism | Evidence Produced |
|-------------------|--------------------|--------------------|
| **(a) Trusted insider, permitted access** | CloudTrail logs the access with full attribution | Who, what, when, from where — complete audit record |
| **(b) Unauthorized access attempt** | CloudTrail logs the denial; GuardDuty flags the anomaly; VPC Flow Logs show the connection | Denied access logged + alert fired + network evidence preserved |

The monitoring stack doesn't just detect — it produces the *evidence chain* needed for HIPAA breach notification: what happened, when, who was affected, and what was done about it.

---

## Cost Management

### Principle

Cloud infrastructure costs are operational expenses, not capital expenses. You pay for what's running. The single most effective cost control is: **stop things that aren't being used.**

Unlike on-premises hardware (which costs the same whether idle or busy), AWS charges by the hour/second for compute and by the GB/month for storage. This means:
- A database running 24/7 for a year costs 8,760 hours × hourly rate
- The same database running only business hours (Mon–Fri, 6AM–6PM) costs ~3,120 hours × hourly rate (64% savings)
- A database *stopped entirely* for a month costs $0 for compute (storage charges still apply)

### Annual Cost Estimate (Ballpark)

Based on 10,000 patients, the architecture described in this document, and business-hours operation:

| Service | Instance/Config | Hourly Rate | Hours/Year | Annual Cost |
|---------|----------------|-------------|------------|-------------|
| **EC2 IDE instances (×6)** | m5.xlarge (4 vCPU, 16GB) | $0.192/hr each | ~3,120 (biz hours) | **$3,594** |
| **RDS PostgreSQL** | db.t3.medium (2 vCPU, 4GB) | $0.068/hr | ~3,120 (biz hours) | **$212** |
| **DocumentDB** | db.t3.medium (2 vCPU, 4GB) | $0.076/hr | ~3,120 (biz hours) | **$237** |
| **SageMaker notebooks (×6)** | ml.t3.medium (2 vCPU, 4GB) | $0.050/hr each | ~1,560 (half biz hours, idle-stop) | **$468** |
| **EFS** | ~50 GB working data | $0.30/GB/month | 12 months | **$180** |
| **S3 (all zones)** | ~500 GB total (PD0–PD3 + audit) | $0.023/GB/month | 12 months | **$138** |
| **NAT Gateway** | Single AZ | $0.045/hr + data | ~3,120 hours | **$140** + data |
| **KMS** | 4 keys | $1/key/month | 12 months | **$48** |
| **CloudTrail** | Data events (S3, Lambda) | ~$2/100K events | ~5M events/year | **$100** |
| **GuardDuty** | Per-account | ~$4/million events analyzed | Varies | **$50–200** |
| **Macie** | S3 scanning | $1/GB scanned first month | ~500 GB | **$50–100** |
| **Config** | Rules + recording | $0.003/rule evaluation | ~70 rules × daily | **$75** |
| **Wickr** | 7 users | Included in AWS (basic tier) | — | **$0** |
| **VPC Endpoints (×15)** | Interface endpoints | $0.01/hr each | 8,760 hrs | **$1,314** |
| | | | **Estimated Total** | **~$6,500–7,500/year** |

> [i] **TEACHING NOTE:** The largest costs are EC2 (compute) and VPC Endpoints. VPC Endpoints are a fixed hourly cost whether or not anyone is using them — they can't be "stopped." This is the price of private networking without internet access. The alternative (NAT Gateway for everything) would be cheaper for endpoints but more expensive for data transfer and less secure. For a real project, evaluate whether all 15 endpoints are needed simultaneously or if some can be provisioned on-demand.

### What Drives Cost Down to $0.10/hr Range?

The $0.10/hr range for databases comes from using the smallest instance classes:

| Instance | vCPU | RAM | Hourly Rate | Use Case |
|----------|------|-----|-------------|----------|
| db.t3.micro | 2 | 1 GB | $0.018/hr | Development/testing only |
| db.t3.small | 2 | 2 GB | $0.036/hr | Very light workloads |
| db.t3.medium | 2 | 4 GB | $0.068/hr | **Starting point for this project** — adequate for 10K patients |
| db.t3.large | 2 | 8 GB | $0.136/hr | If queries need more memory |
| db.r5.large | 2 | 16 GB | $0.240/hr | Memory-intensive analytics |

For 10,000 patients with OMOP tables (~500K rows across all tables), `db.t3.medium` is sufficient. The data fits comfortably in 4GB RAM. You'd only scale up if query complexity or concurrent users demand it.

**DocumentDB** starts higher (~$0.076/hr for db.t3.medium) because it's a cluster-based service. For this project's scale, it's still modest.

### Storage Cost Estimate (10,000 Patients)

| Dataset | Estimated Size | Storage Type | Monthly Cost |
|---------|---------------|--------------|--------------|
| PD0 (OMOP tables in RDS) | ~2–5 GB | RDS storage ($0.115/GB/month) | $0.50 |
| PD0 (patient documents in DocumentDB) | ~2–5 GB | DocumentDB storage ($0.10/GB/month) | $0.50 |
| PD1 (crystallography, ~15K files) | ~50–150 GB | S3 Standard ($0.023/GB/month) | $1.15–3.45 |
| PD2 (VCF files, 10K files) | ~10–50 GB | S3 Standard | $0.23–1.15 |
| PD3 (lab results CSV) | ~1–2 GB | S3 Standard | $0.05 |
| Audit logs (CloudTrail, Flow Logs) | ~50–100 GB/year | S3 Standard → Glacier ($0.004/GB) | $0.40–2.30 |
| EFS (working space) | ~50 GB | EFS ($0.30/GB/month) | $15.00 |
| **Total storage** | **~200–400 GB** | | **~$18–23/month ($216–276/year)** |

Storage is cheap. Compute is where the money goes.

### The Seychelles Scenario: Full Hibernation

**Yes — you can stop everything and reduce spend to near-zero.**

When the entire team is away for an extended period:

| Action | What Stops | What Keeps Running | Residual Cost |
|--------|-----------|-------------------|---------------|
| **Stop EC2 instances** | All 6 IDE instances | EBS volumes (storage only) | ~$0 compute; ~$5/month storage |
| **Stop RDS** | Database compute | Storage retained (automated backups) | ~$0 compute; ~$1/month storage |
| **Stop DocumentDB** | Cluster compute | Storage retained | ~$0 compute; ~$1/month storage |
| **Stop SageMaker notebooks** | All notebook instances | EBS volumes | ~$0 compute; ~$2/month storage |
| **S3** | Cannot "stop" — always on | Data persists | ~$12/month (just storage) |
| **EFS** | Cannot "stop" — always on | Data persists | ~$15/month |
| **VPC Endpoints** | Can be deleted and recreated | — | $0 if deleted; $1,314/year if left running |
| **NAT Gateway** | Can be deleted and recreated | — | $0 if deleted |
| **CloudTrail** | Keeps running (minimal cost when no API calls) | Logging | ~$1/month |
| **GuardDuty/Macie/Config** | Keep running (minimal cost when idle) | Monitoring | ~$5/month |
| **KMS** | Always on (keys exist) | Key storage | $4/month |

**Full hibernation cost: ~$40–50/month** (down from ~$550–625/month during active use).

That's a **92% reduction** — from ~$7,000/year active to ~$500/year hibernated.

### Hibernation Procedure

To hibernate the environment:

```
1. Notify team via Wickr: "Environment hibernating [date] – [date]"
2. Stop all EC2 instances (disable Auto-Start schedule)
3. Stop RDS instance
4. Stop DocumentDB cluster
5. Stop all SageMaker notebook instances
6. (Optional) Delete VPC Endpoints and NAT Gateway for maximum savings
7. Verify: only storage + monitoring charges remain
8. Document: "Environment hibernated [date], reason: [conference/break]"
```

To wake up:

```
1. (If deleted) Recreate VPC Endpoints and NAT Gateway (CDK redeploy)
2. Start RDS instance
3. Start DocumentDB cluster
4. Re-enable Auto-Start schedule for EC2
5. Start EC2 instances (or wait for next Auto-Start)
6. Verify: all services responding; run abbreviated security validation
7. Notify team: "Environment active"
```

> [i] **TEACHING NOTE:** The ability to hibernate is a major advantage of cloud over on-premises. A physical server in a data center costs the same whether anyone uses it or not. Cloud infrastructure can be scaled to zero during breaks, between grant periods, or when the project is in a documentation-only phase. Budget your NIH cloud costs based on *active months*, not 12 months × full rate. For a project active 9 months/year with 3 months hibernated: ~$5,500/year instead of $7,000 (saving ~$1,500 during the 3 hibernated months when only storage charges apply at ~$50/month).

---

## Blank Slate Rule

### Principle

The CDK infrastructure code must be able to cleanly delete and verify deletion of **all** provisioned AWS resources — returning the accounts to a blank state with no zombie services incurring cost. The same resource definitions used for build-up are used for tear-down.

This is not optional. It is a design constraint enforced from day one.

### Why This Matters

Zombie spend — services left running after they're no longer needed — is one of the most common cloud cost problems. It happens because:
- Someone provisions a resource manually (outside IaC) and forgets about it
- A service is created for testing and never cleaned up
- A deployment fails partway through, leaving orphaned resources
- A project ends but no one runs the tear-down

The Blank Slate Rule eliminates this by ensuring: **if CDK created it, CDK can destroy it. If CDK didn't create it, it shouldn't exist.**

### Implementation

**CDK provides this natively.** A CDK stack is a unit of deployment. `cdk destroy` removes all resources defined in the stack. The key requirements:

| Requirement | How CDK Handles It | Project Enforcement |
|-------------|-------------------|---------------------|
| All resources defined in code | CDK stacks define every resource | No manual console provisioning allowed (zero-console rule) |
| Tear-down uses same definitions as build-up | `cdk destroy` reads the same stack definitions | Single source of truth for what exists |
| Deletion order respects dependencies | CloudFormation handles dependency ordering automatically | CDK models dependencies explicitly |
| Propagation delays handled | CloudFormation waits for resource deletion to complete before proceeding | Built-in; no custom pauses needed for most resources |
| Verification after deletion | Post-destroy script enumerates remaining resources | Custom verification script (see below) |

**Propagation delays:** Some AWS resources take minutes to fully delete (RDS instances, KMS keys with waiting periods, S3 buckets that must be emptied first, VPC resources with dependencies). CloudFormation handles most of this automatically — it waits for each resource to reach DELETE_COMPLETE before proceeding to dependent resources. For resources with mandatory waiting periods (KMS: 7–30 days), the stack deletion will complete but the key remains in "pending deletion" state until the waiting period expires.

### Verification Script

After `cdk destroy`, a verification script confirms nothing was left behind:

```python
# Conceptual — verify blank slate
def verify_blank_slate(account_id, region):
    """Enumerate all resources in the account; alert on any that remain."""
    checks = [
        list_ec2_instances(),      # Should be empty
        list_rds_instances(),      # Should be empty
        list_s3_buckets(),         # Should be empty (or only audit retention)
        list_efs_filesystems(),    # Should be empty
        list_vpc_resources(),      # Should be empty (or default VPC only)
        list_kms_keys(),           # Should show only "pending deletion"
        list_lambda_functions(),   # Should be empty
        list_ecs_clusters(),       # Should be empty
        list_documentdb_clusters(),# Should be empty
        list_vpc_endpoints(),      # Should be empty
        list_nat_gateways(),       # Should be empty
    ]
    orphans = [r for check in checks for r in check if r.state != 'deleted']
    if orphans:
        alert(f"ZOMBIE RESOURCES FOUND: {orphans}")
    else:
        log("Blank slate verified: no active resources remain")
```

### Exceptions to Immediate Deletion

Some resources cannot or should not be immediately deleted:

| Resource | Why Not Immediate | Resolution |
|----------|-------------------|------------|
| **KMS keys** | Mandatory 7–30 day waiting period (AWS-enforced safety net) | Schedule deletion; verify after waiting period |
| **S3 buckets with data** | Must be emptied before deletion | Empty bucket (or apply lifecycle expiration), then delete |
| **S3 with Object Lock** | Cannot delete until retention period expires | Document; delete after retention (audit logs: 7 years) |
| **CloudTrail logs (Audit account)** | Must be retained for HIPAA compliance (6–7 years) | Audit account resources are retained separately; not part of Production tear-down |
| **RDS automated backups** | Retained briefly after instance deletion | AWS auto-deletes after retention period; verify |

### Relationship to Decommission (Phase 6)

The Blank Slate Rule is the *mechanism* for Phase 6 (Decommission). The decommission procedure is:
1. Data disposition (export/destroy PHI per policy)
2. `cdk destroy` (remove all infrastructure)
3. Verification script (confirm blank slate)
4. KMS key deletion confirmation (after waiting period)
5. Audit account retention (kept for compliance; destroyed after 7 years)

### Three Operational Modes: DECOMMISSION, HIBERNATE, DESTROY

The project defines three distinct courses of action for managing the CI lifecycle:

#### HIBERNATE (cost management)

**Purpose:** Pause the environment to reduce spend when the team is not actively using it (conferences, breaks, weekends beyond auto-stop).

**What happens:**
- Compute stopped (EC2, RDS, DocumentDB, SageMaker)
- Storage persists (S3, EFS, EBS volumes retained)
- Monitoring continues at minimal cost (GuardDuty, Config, CloudTrail — idle but active)
- VPC Endpoints optionally deleted for additional savings (recreated on wake)
- **Nothing is destroyed. Full restart is fast (minutes to hours).**

**Residual cost:** ~$40–50/month (storage + minimal monitoring)

**Trigger:** Team decision; any team member can initiate via documented procedure.

---

#### DECOMMISSION (HIPAA end-of-life)

**Purpose:** Controlled shutdown at end of Period of Performance, compliant with HIPAA data retention and disposition requirements.

**What happens:**
- PHI data dispositioned per policy (destroyed or returned to source)
- Data destruction certified (who, what, when, method)
- KMS keys scheduled for deletion (30-day waiting period — maximum safety)
- Infrastructure removed via `cdk destroy`
- **Audit logs retained** in Audit account for HIPAA retention period (6–7 years)
- S3 Object Lock protects audit logs from premature deletion
- Final compliance report produced and archived

**Residual cost:** Audit account storage only (~$5–10/month for retained logs, declining as data moves to Glacier)

**Trigger:** PI decision at project end; formal decommission memo signed.

**Timeline:** ~1 week active work + 30 days KMS waiting + 7 years audit retention

---

#### DESTROY (development purge)

**Purpose:** Complete elimination of all resources and data. Nothing remains of the CI, nothing remains of the synthetic data. Used during development when you want to start fresh, test the Blank Slate Rule, or permanently end a synthetic/learning environment with no compliance retention obligations.

**What happens:**
- All S3 buckets force-emptied (all versions, all delete markers purged)
- All databases deleted (RDS, DocumentDB — no final snapshots retained)
- All compute terminated
- All KMS keys scheduled for deletion (7-day minimum — AWS-enforced, cannot be overridden)
- All VPC resources deleted (endpoints, NAT, subnets, VPC itself)
- Audit logs **deleted** (no retention obligation for synthetic data)
- `cdk destroy` removes all CloudFormation stacks
- Verification script confirms blank slate

**Residual cost:** $0 after KMS 7-day waiting period completes.

**Trigger:** PI or IT Staff decision; used for development resets or final project closure when no HIPAA retention applies.

**Timeline:** ~1 hour active work + 7 days for KMS key deletion to finalize.

**AWS-imposed constraint:** KMS keys cannot be deleted instantly. The minimum waiting period is 7 days. During this period, the key is in "pending deletion" state — it cannot be used to encrypt or decrypt, so data is functionally inaccessible immediately. After 7 days, the key is permanently destroyed.

---

#### Development vs. Production Controls

To enable DESTROY to work cleanly, the synthetic/development environment omits certain production HIPAA controls that would block immediate deletion:

| Control | Production (DECOMMISSION) | Development (DESTROY) |
|---------|--------------------------|----------------------|
| S3 Object Lock | Applied (enforces retention period) | **Not applied** (allows immediate deletion). Object Lock is a Real Deployment necessity; omitted in Development Deployment to enable clean DESTROY. |
| MFA Delete on S3 | Enabled (prevents accidental deletion) | **Not enabled** (allows scripted deletion). MFA Delete requires manual MFA input for every permanent deletion — incompatible with automated tear-down scripts. Enable for Real Deployment to protect audit logs from compromised credentials. |
| KMS waiting period | 30 days (maximum safety net) | 7 days (minimum, AWS-enforced) |
| Audit log retention | 7 years (HIPAA requirement) | **Deleted with everything else** |
| Final snapshots (RDS) | Retained | **Skipped** (`skip-final-snapshot` flag) |

> [i] **TEACHING NOTE:** A real production system handling actual PHI would use DECOMMISSION exclusively — you cannot DESTROY a system with real patient data without first satisfying retention obligations. DESTROY exists for the synthetic/learning context where there are no compliance retention requirements. The distinction is important: know which mode applies to your situation before executing. Accidentally running DESTROY on a production system with real PHI would be a compliance violation (destroying records before retention period expires) even though no data breach occurs.

### Relationship to Hibernation

Hibernation (stopping services) is different from both DECOMMISSION and DESTROY:
- **HIBERNATE:** Stop compute, keep storage. Resources still exist; can be restarted. Cost reduced but not zero.
- **DECOMMISSION:** Controlled destruction with compliance obligations. Audit trail retained.
- **DESTROY:** Total elimination. Nothing remains. Zero residual cost (after 7-day KMS wait).

> [i] **TEACHING NOTE:** The Blank Slate Rule also serves as a confidence test. If you can destroy and rebuild your entire environment from CDK code, you know your IaC is complete and correct. If `cdk destroy` followed by `cdk deploy` produces a working environment, your infrastructure is truly reproducible. This is worth testing periodically (in a Dev/Test account if you have one, or during a planned maintenance window).

---

## Security Validation (Gate G5)

### Purpose

Before any PHI enters the environment (even synthetic), the infrastructure must be proven secure. Security validation is the process of verifying that every control works as designed — encryption is active, access is restricted, logging is operational, and the network is locked down. This is Gate G5: the system is not authorized for data loading until validation passes.

### Validation Approach

The validation combines automated scanning with manual verification:

| Method | What It Checks | Tool |
|--------|---------------|------|
| **AWS Config conformance pack** | ~70 HIPAA rules evaluated against all resources | AWS Config (automated, continuous) |
| **Security Hub score** | Aggregated compliance posture (% of checks passing) | Security Hub (automated) |
| **Manual IAM review** | Role permissions match design; no over-privileged roles; explicit denies in place | Manual review of IAM policies against ARCHITECTURE.md role definitions |
| **Encryption verification** | Every storage resource encrypted with correct key; key policies match design | CLI/script: enumerate S3 buckets, RDS instances, EFS, EBS → verify encryption + key ID |
| **Network verification** | No public IPs; no open security groups; VPC endpoints functional; NAT restricted to GitHub | CLI/script: describe security groups, subnets, route tables, endpoints |
| **Logging verification** | CloudTrail delivering to Audit account; data events enabled; Flow Logs active; gatekeeper logging | Verify log delivery by checking Audit account S3 bucket for recent entries |
| **Access control test** | Positive test (authorized role can access data) + negative test (unauthorized role is denied) | Manual: assume each role, attempt access, verify result matches design |
| **Gatekeeper test** | Submit prompt with known PHI → verify block; submit clean prompt → verify pass | Manual: test gatekeeper with sample inputs |

### Validation Checklist

The following must all pass before Gate G5 is satisfied:

**Encryption (all must be TRUE):**
- [ ] All S3 buckets encrypted with SSE-KMS (correct key per zone)
- [ ] RDS instance encrypted with `phi-data-key`
- [ ] EFS filesystem encrypted with `phi-data-key`
- [ ] All EBS volumes encrypted with `infra-key`
- [ ] KMS key rotation enabled on all keys
- [ ] KMS key policies match design (deny InfraAdmin decrypt on PHI keys)

**Network (all must be TRUE):**
- [ ] No EC2 instances have public IPs
- [ ] No security groups allow inbound from 0.0.0.0/0
- [ ] VPC has no internet gateway
- [ ] NAT gateway egress restricted to GitHub IP ranges + port 443 only
- [ ] All required VPC endpoints are active and reachable from private subnets
- [ ] VPC Flow Logs enabled and delivering to Audit account

**IAM (all must be TRUE):**
- [ ] `InfraAdmin` cannot call s3:GetObject on PHI data zones (test: attempt → AccessDenied)
- [ ] `InfraAdmin` cannot call kms:Decrypt on `phi-data-key` (test: attempt → AccessDenied)
- [ ] `Researcher` cannot modify IAM policies (test: attempt → AccessDenied)
- [ ] `Researcher` cannot access S3 landing zone (test: attempt → AccessDenied)
- [ ] `Researcher` cannot access Audit account (test: attempt → AccessDenied)
- [ ] `SeniorResearcher` can read S3 processed zone (test: attempt → success)
- [ ] `SeniorResearcher` can query RDS via study views (test: attempt → success)
- [ ] `ProjectAdmin` can access Audit account logs (test: attempt → success)
- [ ] All roles require MFA for session creation

**Logging (all must be TRUE):**
- [ ] CloudTrail organization trail active (all regions)
- [ ] CloudTrail data events enabled for S3 and Lambda
- [ ] CloudTrail logs appearing in Audit account S3 bucket (check for entries within last hour)
- [ ] CloudTrail log file validation enabled
- [ ] CloudWatch Logs receiving application logs from compute instances
- [ ] VPC Flow Logs active and delivering

**Monitoring (all must be TRUE):**
- [ ] GuardDuty enabled in Production account
- [ ] Macie enabled; scanning Production S3 buckets
- [ ] AWS Config recording; HIPAA conformance pack deployed
- [ ] Security Hub enabled; receiving findings from GuardDuty, Macie, Config
- [ ] Alert flow functional: test finding → EventBridge → SNS → Wickr notification received

**Gatekeeper (all must be TRUE):**
- [ ] Gatekeeper Lambda deployed and reachable from compute instances
- [ ] Prompt with known PHI (test MRN) → blocked; researcher notified; event logged
- [ ] Clean prompt → forwarded to Bedrock; response returned; event logged
- [ ] Gatekeeper failure mode: service stopped → Bedrock access blocked (fail-closed confirmed)

**Compute (all must be TRUE):**
- [ ] IDE instances start/stop on schedule (test Auto-Start and Auto-Stop)
- [ ] Keep-alive tag override works (tag instance → Auto-Stop skips it)
- [ ] Session Manager access works (researcher can connect to IDE instance)
- [ ] SageMaker notebook instance launches in VPC mode (no internet access)
- [ ] EFS mounted and accessible from all compute instances

### Validation Report

Upon completion, IT Staff produces a validation report documenting:

1. **Date of validation**
2. **Checklist results** (pass/fail for each item above)
3. **Findings** (any items that initially failed)
4. **Remediations** (what was fixed and when)
5. **Residual items** (anything accepted as-is with justification — should be zero for CRITICAL items)
6. **Sign-off** (IT Staff certifies validation complete; PI reviews and accepts)

This report is stored in the Audit account as Gate G5 evidence.

### Ongoing Validation (Phase 5)

Security validation is not a one-time event. During operations:
- AWS Config continuously evaluates (any new non-compliance triggers an alert)
- Security Hub score is monitored (target: 100% on CRITICAL/HIGH rules)
- Quarterly manual review repeats the IAM and access control tests
- Any infrastructure change (CDK deployment) triggers re-validation of affected components

> [i] **TEACHING NOTE:** The validation checklist looks long, but most items are automatable. A validation script (Python + boto3) can enumerate resources, check encryption, verify security groups, and test access in minutes. The manual items (gatekeeper test, access control positive/negative tests) take perhaps an hour. The entire validation can be completed in a single day. The *first* time takes longer because you're also fixing what you find. Subsequent validations (after changes) are faster because the baseline is established.

---

## Data Storage Architecture

### Design Decision: Right Store for Each Dataset

| Dataset | Primary Store | Why | Query Method |
|---------|--------------|-----|--------------|
| **PD0 (OMOP relational)** | RDS PostgreSQL | Relational data; SQL joins for cohort queries; OHDSI tooling compatibility | SQL (direct, Athena, or application) |
| **PD0 (patient documents)** | DocumentDB | Denormalized per-patient "chart view"; flexible schema for multi-modal data | Document lookup by MRN/person_id |
| **PD1 (crystallography files)** | S3 | Binary files; not queryable as rows; retrieved and processed by specialized tools | S3 GetObject by key (MRN + study ID) |
| **PD2 (VCF genomics files)** | S3 | Structured files; processed by bioinformatics pipelines, not SQL | S3 GetObject by key (MRN) |
| **PD3 (raw lab CSV)** | S3 | Source-format archive; queryable version already exists in OMOP MEASUREMENT table | Athena (SQL over S3) if needed; otherwise just archive |
| **Metadata index** | PostgreSQL (small table) | Maps MRN → S3 keys for cross-dataset discovery | SQL join against OMOP tables |
| **Audit logs** | S3 (Audit account) | Immutable, cheap, long-retention | Athena for forensic queries |

### Why Not Put Everything in a Database?

- **PD1/PD2 are files, not rows.** You don't query inside a CIF or VCF with SQL — you download the file and process it with domain-specific tools. Storing binary files in a database adds cost (~10–100× more expensive per GB than S3) with no analytical benefit.
- **PD3 already exists in OMOP.** The raw CSV in S3 is the source-format archive. The queryable, standardized version lives in the MEASUREMENT table in PostgreSQL. No need to store it twice in databases.
- **S3 is the natural landing zone.** Data arrives via the upload path into S3. Keeping PD1/2/3 in S3 means no additional ETL step to move files into a database — they stay where they land (after validation).

### Metadata Index (Cross-Dataset Discovery)

A small PostgreSQL table enables queries like "find all patients with crystallography data AND elevated HbA1c":

```sql
-- Example: find patients with both crystallography and diabetes
SELECT m.mrn, m.s3_key, m.dataset, m.study_date
FROM dataset_metadata m
JOIN condition_occurrence c ON m.person_id = c.person_id
WHERE m.dataset = 'PD1'
  AND c.condition_concept_id = 201826  -- Type 2 diabetes (SNOMED)
```

| Column | Type | Description |
|--------|------|-------------|
| person_id | INT | Links to OMOP PERSON table |
| mrn | VARCHAR | Patient MRN (links to S3 object keys) |
| dataset | VARCHAR | PD1, PD2, or PD3 |
| s3_key | VARCHAR | Full S3 object path |
| file_type | VARCHAR | CIF, VCF, CSV |
| study_date | DATE | When the data was collected |
| file_size_bytes | BIGINT | For inventory/audit purposes |

This table is small (~25,000 rows for all PD1+PD2+PD3 files) and adds negligible cost to the PostgreSQL instance.

---

## Synthetic Data Generation (separate repository)

Synthetic PHI is generated in a separate, isolated repository: **`securecomputing-datagen`**.

**Design principle:** The data generation system is a *supplier* to the analysis system, connected only through the documented upload interface. This isolation ensures:

- The datagen environment has no access to the analysis environment (no shared credentials, no network path)
- The analysis environment has no dependency on datagen internals (only on the output format)
- Generated data enters the analysis environment via the same S3 upload path that real PHI would use — dogfooding the upload security, validation, and handoff protocol
- If synthetic data is later replaced with real PHI, nothing in the analysis environment changes — only the data source changes

**What lives in `securecomputing-datagen`:**
- Synthea configuration (or custom generator code)
- Schema definitions for the synthetic patient records
- Generation scripts and parameters (N=10,000 patients)
- Output format specifications (matching what the upload path expects)
- Documentation of what was generated and how

**What does NOT live in `securecomputing-datagen`:**
- Any real PHI (obviously)
- Analysis code
- Infrastructure-as-code for the analysis environment
- Policies or compliance documentation (that's this repo)

---

## Development Tracks

The project is developed along three parallel tracks:

| Track | Scope | Repository | Directory |
|-------|-------|-----------|-----------|
| **Track A: Data Generation** | Synthetic PHI generation (PD0–PD3), manifest creation, upload to S3 | `securecomputing-datagen` | (entire repo) |
| **Track B: Infrastructure** | CDK stacks defining all AWS resources; operational scripts (hibernate, wake, destroy) | `securecomputing` | `infrastructure/`, `ops/` |
| **Track C: Analysis** | Research code that runs on the CI — Dockerized pipelines, notebooks, query scripts | `securecomputing` | `analysis/` |

**Dependencies between tracks:**
- Track C depends on Track B (infrastructure must exist before analysis code can run on it)
- Track C depends on Track A (data must be generated and uploaded before analysis can operate on it)
- Track A and Track B can proceed in parallel (datagen doesn't need the CI to generate data; CI doesn't need data to be built)
- The Docker pipeline demo (Track C) is the integration point that proves all three tracks work together

### Repository Structure (securecomputing)

```
securecomputing/
├── docs/                    # Project documentation
│   ├── PROJECT_OVERVIEW.md
│   ├── ARCHITECTURE.md
│   ├── GATES.md
│   ├── PHASE0_CHARTER.md
│   ├── RISK_ASSESSMENT.md
│   ├── POLICY_AI_ACCEPTABLE_USE.md
│   ├── POLICY_SUITE.md
│   └── NISTDocs.md
├── infrastructure/          # Track B: CDK stacks
│   ├── app.py              # CDK entry point — instantiates all stacks
│   ├── cdk.json            # CDK configuration
│   ├── requirements.txt    # Python dependencies for CDK
│   └── stacks/
│       ├── vpc_stack.py
│       ├── iam_stack.py
│       ├── kms_stack.py
│       ├── storage_stack.py
│       ├── compute_stack.py
│       ├── monitoring_stack.py
│       └── gatekeeper_stack.py
├── analysis/                # Track C: Research analysis code
│   ├── containers/          # Dockerfiles + app code for ECS tasks
│   ├── notebooks/           # SageMaker notebook templates (no output cells)
│   └── scripts/             # Utility scripts (queries, data processing)
├── ops/                     # Operational scripts
│   ├── hibernate.sh
│   ├── wake.sh
│   ├── destroy.sh
│   └── verify_blank_slate.py
└── .gitignore
```

### CDK Entry Point (`infrastructure/app.py`)

`app.py` is the CDK application entry point. It does not build infrastructure directly — it **defines** the infrastructure by instantiating stack classes, then CDK synthesizes those definitions into CloudFormation templates and deploys them.

```python
# Conceptual structure of app.py
import aws_cdk as cdk
from stacks.vpc_stack import VpcStack
from stacks.iam_stack import IamStack
from stacks.kms_stack import KmsStack
from stacks.storage_stack import StorageStack
from stacks.compute_stack import ComputeStack
from stacks.monitoring_stack import MonitoringStack
from stacks.gatekeeper_stack import GatekeeperStack

app = cdk.App()

# Configuration
env = cdk.Environment(account="PRODUCTION_ACCOUNT_ID", region="us-west-2")
destroy_mode = True  # Development default: no Object Lock, no MFA Delete, 7-day KMS

# Stacks deployed in dependency order
vpc = VpcStack(app, "VpcStack", env=env)
kms = KmsStack(app, "KmsStack", env=env, destroy_mode=destroy_mode)
iam = IamStack(app, "IamStack", env=env, vpc=vpc)
storage = StorageStack(app, "StorageStack", env=env, vpc=vpc, kms=kms, destroy_mode=destroy_mode)
compute = ComputeStack(app, "ComputeStack", env=env, vpc=vpc, kms=kms, iam=iam, storage=storage)
monitoring = MonitoringStack(app, "MonitoringStack", env=env, vpc=vpc, storage=storage)
gatekeeper = GatekeeperStack(app, "GatekeeperStack", env=env, vpc=vpc, kms=kms)

app.synth()
```

**How it works:**
1. You run `cdk deploy --all` from the `infrastructure/` directory
2. CDK reads `app.py`, instantiates all stack objects (which define resources in Python)
3. CDK synthesizes each stack into a CloudFormation template (JSON)
4. CDK deploys each template to AWS in dependency order
5. CloudFormation creates the actual AWS resources

**To tear down:** `cdk destroy --all` reverses the process — CloudFormation deletes all resources in reverse dependency order.

**The `destroy_mode` flag:** When `True` (development default), stacks omit Object Lock, MFA Delete, and use 7-day KMS deletion. When `False` (production), stacks apply full HIPAA retention controls. This single flag is the switch between DESTROY-compatible and DECOMMISSION-compatible configurations.
