\newpage

<!-- SOURCE: COMPLETION.md -->

# Demonstrator vs. Production: Completion Steps

This document describes what the demonstrator system builds, what it deliberately omits, and what a real project must add.

---

## What This Demonstrator Is

This project is a **teaching and reference implementation** — not a turnkey production system. It demonstrates:

- The full lifecycle framework (Phases 0–6, Gates G1–G6)
- Organizational controls (policies, roles, training approach, risk assessment)
- Technical architecture (VPC, IAM, KMS, monitoring, gatekeeper design)
- Working CDK infrastructure code (deployable, destroyable)
- Synthetic data generation pipeline (PD0–PD3, clinically coherent)
- Cost management (auto-start/stop, hibernation, DESTROY)
- AI governance (gatekeeper concept, agentic audit, prompt hygiene)

---

## What This Demonstrator Is NOT

This demonstrator does not function as a complete build template. Each PHI project — and each computing infrastructure implementation thereby — is presumed a **bespoke system**. The builders must be able to complete and test the code-as-infrastructure machinery for their specific institutional context, data types, team composition, and compliance requirements.

**The demonstrator is intentionally incomplete in areas where:**
- Institutional specifics vary (SSO configuration, SCP details, BAA terms)
- Production hardening requires testing against real workloads
- HIPAA retention obligations apply only to real PHI (not synthetic data)
- Security controls must be validated by the team that will operate them

---

## Synthetic Prototype vs. Operational System: Feature Comparison

### Storage & Encryption

| Feature | Synthetic Prototype | Operational System | Gap |
|---------|--------------------|--------------------|-----|
| S3 Object Lock | Not applied | Required on audit bucket | Must implement |
| MFA Delete | Not enabled | Required on audit bucket | Must implement |
| KMS deletion wait | 7 days (minimum) | 30 days (maximum safety) | Config change only |
| RDS final snapshot | Skipped | Retained before deletion | Config change only |
| Multi-AZ (RDS, EFS) | Single-AZ (cost savings) | Multi-AZ (resilience) | Config change + cost |
| Audit log retention | Deleted with everything | 6–7 years (Glacier lifecycle) | Must implement lifecycle rules |
| Glacier transition | Not configured | Standard → Glacier at 90 days | Must implement |

### Security & Access Control

| Feature | Synthetic Prototype | Operational System | Gap |
|---------|--------------------|--------------------|-----|
| IAM key policies (deny IT decrypt) | Documented, not enforced in CDK | Explicit deny statements in key policies | Must implement |
| SSO federation | Not configured (IAM User keys) | UW SSO → AWS IAM Identity Center | Institutional dependency |
| SCP enforcement | Documented as UW IT responsibility | Verified against actual SCPs | Institutional dependency |

### Services & Tooling

| Feature | Synthetic Prototype | Operational System | Gap |
|---------|--------------------|--------------------|-----|
| Gatekeeper Lambda | Designed, not deployed | Deployed, tested, fail-closed verified | Must build |
| Macie (PHI discovery) | Deferred for cost | Enabled, scanning all buckets | Enable + configure |
| DocumentDB | Not deployed (cost) | Deployed for patient document views | Add to CDK + cost |
| DECOMMISSION script | Not written | Orchestrates PHI destruction → infra teardown → audit retention | Must write and test |

### Organizational

| Feature | Synthetic Prototype | Operational System | Gap |
|---------|--------------------|--------------------|-----|
| Incident response drill | Designed (Black Hat Test) | Executed and documented | Must perform |
| HIPAA training | Approach documented | All personnel trained with certificates | Must procure and complete |

---

## Adapting the Synthetic Prototype

The Synthetic Prototype (SP) is a reference architecture — not a fill-in-the-blanks template. Transitioning to an Operational System (OS) requires a structured discovery process that captures the specific requirements of the real research program and maps them to IaC modifications.

### The Adaptation Process

The SP was built through a question-and-answer interview process between the PI and an AI assistant. The same approach applies when adapting it for a real project: a series of structured conversations that progressively narrow the design space from generic to specific.

**Who participates:**
- Principal Investigator (research requirements, data types, team composition)
- IT/Infrastructure staff (institutional constraints, existing services, network policies)
- Compliance/Privacy officer (regulatory requirements, institutional policies, BAA status)
- Budget authority (cost constraints, funding timeline)

**What the interviews produce:**
- A modified architecture document reflecting the real project's needs
- Revised CDK parameters (instance types, service selection, team size, storage estimates)
- A cost estimate derived from the adapted design (not from the SP's synthetic workload)

### Interview Topics

The following areas require project-specific answers before the SP can become an OS:

| Topic | SP Assumption | Questions for the Real Project |
|-------|---------------|-------------------------------|
| Team size | 7 people (PI, Postdoc, Co-PI, 3 students, IT) | How many researchers? What roles? Will the team grow? |
| Data volume | 896 MB synthetic | How much real data? Growth rate? Imaging? Genomics at scale? |
| Data types | EHR (OMOP), crystallography (CIF), genomics (VCF), labs (CSV) | What modalities? What formats? What ingest frequency? |
| Compute needs | t3.medium IDE instances | GPU workloads? ML training? Large-memory analysis? |
| AI services | Bedrock (Claude) + Comprehend Medical | Which foundation models? Fine-tuning? Custom endpoints? |
| Availability | Business hours only (auto-start/stop) | 24/7 access needed? Weekend work? Multi-timezone team? |
| Collaboration | Single VPC, shared EFS | Multi-site? Cross-institution data sharing? Federated analysis? |
| Data source | Generated locally (securecomputing-datagen) | Hospital EHR extract? Registry data? External biobank? |
| Retention | None (DESTROY mode) | IRB-mandated retention period? Funding agency requirements? |
| Institutional SSO | Not configured | Which identity provider? SAML? OIDC? Existing AWS Organization? |
| Network policy | NAT restricted to GitHub only | Other external services needed? Package repositories? Data APIs? |
| Budget | ~$400/month active, ~$100/month hibernated | Hard budget cap? Funding period? Cost approval workflow? |

### From Answers to IaC

Interview answers map directly to CDK parameters and architectural decisions:

1. **Team size → EC2 instance count, IAM role definitions, KMS key policy grants**
2. **Data volume → S3 storage class selection, EFS throughput mode, RDS instance size**
3. **Compute needs → Instance family/size, GPU instances, SageMaker configuration**
4. **Availability → EventBridge schedule rules, Multi-AZ decisions, auto-scaling**
5. **Retention → S3 lifecycle policies, Object Lock configuration, Glacier transitions**
6. **SSO → IAM Identity Center configuration, SAML provider setup, role mapping**

### Producing the Cost Estimate

Once the adapted design is complete, the cost estimate follows mechanically:

1. List all AWS services in the revised architecture with their sizing
2. Apply the pricing model for each (on-demand, reserved, savings plan)
3. Factor in the operational schedule (hours/month active vs. hibernated)
4. Add monitoring/logging overhead (CloudTrail data events, VPC Flow Logs, Config rules)
5. Include one-time costs (training procurement, penetration testing, compliance review)
6. Compare against budget constraints; iterate on design if needed

The SP's `COST.md` provides the methodology and baseline numbers. The OS cost estimate replaces the SP's synthetic workload assumptions with real ones.

---

## Completion Steps

### Why This Demonstrator Is Missing Final Decommission

The DECOMMISSION procedure — the controlled, HIPAA-compliant shutdown that retains audit logs for 6–7 years while destroying all PHI — is **documented but not implemented as working code** in this demonstrator. This is deliberate:

1. **Each PHI project is bespoke.** The specific data retention requirements, audit log formats, Glacier lifecycle policies, and legal hold procedures depend on the institution, the IRB protocol, the funding agency, and the data use agreements in effect. A generic DECOMMISSION script cannot anticipate these specifics.

2. **The builders must own the machinery.** A team that cannot write, test, and verify their own DECOMMISSION procedure is not ready to operate a PHI system. The ability to cleanly shut down is as important as the ability to build — and it must be tested (ideally by running DESTROY on the synthetic system, then implementing DECOMMISSION for production).

3. **Retention obligations don't apply to synthetic data.** This demonstrator uses fabricated data with no compliance retention requirements. Building and maintaining a 7-year Glacier archive for synthetic audit logs would cost money and teach nothing that the documentation doesn't already convey.

4. **The `destroy_mode` flag is the bridge.** The CDK code includes a `destroy_mode` boolean. Setting it to `False` is the starting point for production hardening — but the `False` branch requires implementation work (Object Lock, MFA Delete, lifecycle rules, retention policies) that is specific to the production deployment.

### What a Real Project Must Add

To transition from this demonstrator to a production PHI system:

1. **Implement `destroy_mode=False` branch in CDK**
   - Add S3 Object Lock (Governance mode) to audit bucket
   - Enable MFA Delete on audit bucket
   - Set KMS pending deletion to 30 days
   - Enable RDS final snapshot on deletion
   - Add S3 lifecycle rules (Standard → Glacier at 90 days; expire at 7 years)
   - Switch EFS to Standard (multi-AZ)
   - Switch RDS to Multi-AZ

2. **Write `ops/decommission.sh`**
   - Verify all PHI locations (inventory check)
   - Destroy PHI data (empty S3 data zones, delete RDS, delete EFS)
   - Certify destruction (generate destruction report)
   - Tear down infrastructure (`cdk destroy` minus audit bucket)
   - Verify audit bucket remains with Object Lock active
   - Schedule `phi-data-key` and `phi-landing-key` for 30-day deletion
   - Retain `audit-key` (needed to read logs for 7 years)

3. **Write `ops/verify_decommission.py`**
   - Confirm all PHI-containing resources are deleted
   - Confirm audit bucket exists with correct lifecycle policy
   - Confirm KMS keys are in correct state (PHI keys pending deletion; audit key active)
   - Confirm no orphaned resources remain

4. **Test the procedure**
   - Run DECOMMISSION on the synthetic system
   - Verify audit logs survive
   - Verify PHI is irrecoverable
   - Document the test as Phase 4 validation evidence

5. **Institutional integration**
   - Configure SSO federation (replace IAM User keys)
   - Verify SCP compatibility
   - Execute BAAs and sub-awards
   - Complete HIPAA training for all personnel
   - Obtain IRB approval for the specific protocol

---

## The Teaching Principle

This demonstrator teaches by showing the *shape* of a compliant system — the architecture, the policies, the controls, the lifecycle. It does not teach by providing a button that produces compliance. Compliance is not a product; it is a continuous practice performed by trained people operating documented procedures on verified infrastructure.

The gap between this demonstrator and a production system is the gap between understanding and execution. The demonstrator provides the understanding. The team provides the execution.
