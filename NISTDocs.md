# NIST Documents for HIPAA and CUI Compliance

Reference guide to key NIST Special Publications relevant to operating
PHI-ready (HIPAA) and CUI-compliant research systems.


## Shared (relevant to both HIPAA and CUI)

| Document | Title | Relevance |
|----------|-------|-----------|
| SP 800-53 | Security and Privacy Controls for Information Systems and Organizations | Master control catalog. HIPAA implementations often map to it; CUI controls (800-171) are derived from its moderate baseline. |
| SP 800-30 | Guide for Conducting Risk Assessments | Methodology for the risk analysis required by both HIPAA Security Rule and CUI control families. |
| SP 800-88 | Guidelines for Media Sanitization | Covers secure disposal of storage media containing PHI or CUI. |


## HIPAA-Specific

| Document | Title | Relevance |
|----------|-------|-----------|
| SP 800-66 | Implementing the HIPAA Security Rule: A Cybersecurity Resource Guide | Direct mapping of HIPAA Security Rule requirements to implementation guidance. The starting point for HIPAA compliance. |
| SP 800-111 | Guide to Storage Encryption Technologies | Referenced for HIPAA's "addressable" encryption requirements for data at rest. |
| NIST CSF | Cybersecurity Framework | HHS encourages using the CSF for HIPAA compliance. Published crosswalks map CSF functions to HIPAA Security Rule standards. |


## CUI-Specific

| Document | Title | Relevance |
|----------|-------|-----------|
| SP 800-171 | Protecting Controlled Unclassified Information in Nonfederal Systems and Organizations | The primary document. Defines 110 required security controls for CUI. Referenced by DFARS 252.204-7012. |
| SP 800-171A | Assessing Security Requirements for Controlled Unclassified Information | Assessment procedures and determination statements for evaluating compliance with each 800-171 control. |
| SP 800-172 | Enhanced Security Requirements for Protecting Controlled Unclassified Information | Advanced controls beyond 800-171 for CUI associated with critical programs or high-value assets. |
| SP 800-37 | Risk Management Framework for Information Systems and Organizations | Lifecycle process for system authorization. Provides context for how contractor systems integrate with federal risk management. |
| SP 800-63 | Digital Identity Guidelines | Referenced for 800-171 identification and authentication controls (MFA, credential management). |


## Relationship Summary

```
SP 800-53 (master catalog, ~1000 controls)
    │
    ├── HIPAA path:
    │     SP 800-66 maps HIPAA Security Rule → 800-53 controls
    │     Flexible: "addressable" controls allow justified alternatives
    │
    └── CUI path:
          SP 800-171 = tailored subset of 800-53 moderate baseline (110 controls)
          SP 800-171A = how to assess those 110 controls
          SP 800-172 = enhanced tier for critical programs
          CMMC = certification framework verifying 800-171 via third-party audit
```


## Key Differences in Approach

| Aspect | HIPAA | CUI |
|--------|-------|-----|
| Primary NIST doc | SP 800-66 | SP 800-171 |
| Flexibility | High — addressable controls, justify alternatives | Low — all 110 controls required |
| Assessment | Self-assessment common; OCR audits rare | Formal assessment required; CMMC involves third-party auditors |
| Incident reporting | 60 days | 72 hours |
| Certification | None required (compliance is self-attested) | CMMC certification (third-party verified) |
