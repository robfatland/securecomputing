\newpage

<!-- SOURCE: NISTDocs.md -->

# NIST Documents for HIPAA and CUI Compliance

Reference guide to key NIST Special Publications relevant to operating
PHI-ready (HIPAA) and CUI-compliant research systems.

> **Note:** All NIST publications are public domain and freely available at [csrc.nist.gov](https://csrc.nist.gov/publications). URLs below point to the canonical source. Revision dates noted are the versions this project references.


## Shared (relevant to both HIPAA and CUI)

| Document | Title | Revision | URL | Relevance |
|----------|-------|----------|-----|-----------|
| SP 800-53 Rev. 5 | Security and Privacy Controls for Information Systems and Organizations | Sep 2020 (updated Dec 2020) | https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final | Master control catalog. HIPAA implementations often map to it; CUI controls (800-171) are derived from its moderate baseline. |
| SP 800-30 Rev. 1 | Guide for Conducting Risk Assessments | Sep 2012 | https://csrc.nist.gov/publications/detail/sp/800-30/rev-1/final | Methodology for the risk analysis required by both HIPAA Security Rule and CUI control families. |
| SP 800-88 Rev. 1 | Guidelines for Media Sanitization | Dec 2014 | https://csrc.nist.gov/publications/detail/sp/800-88/rev-1/final | Covers secure disposal of storage media containing PHI or CUI. |


## HIPAA-Specific

| Document | Title | Revision | URL | Relevance |
|----------|-------|----------|-----|-----------|
| SP 800-66 Rev. 2 | Implementing the HIPAA Security Rule: A Cybersecurity Resource Guide | Feb 2024 | https://csrc.nist.gov/publications/detail/sp/800-66/rev-2/final | Direct mapping of HIPAA Security Rule requirements to implementation guidance. The starting point for HIPAA compliance. |
| SP 800-111 | Guide to Storage Encryption Technologies | Nov 2007 | https://csrc.nist.gov/publications/detail/sp/800-111/final | Referenced for HIPAA's "addressable" encryption requirements for data at rest. |
| NIST CSF 2.0 | Cybersecurity Framework | Feb 2024 | https://csrc.nist.gov/publications/detail/white-paper/2024/02/26/nist-cybersecurity-framework-csf-20/final | HHS encourages using the CSF for HIPAA compliance. Published crosswalks map CSF functions to HIPAA Security Rule standards. |


## CUI-Specific

| Document | Title | Revision | URL | Relevance |
|----------|-------|----------|-----|-----------|
| SP 800-171 Rev. 3 | Protecting Controlled Unclassified Information in Nonfederal Systems and Organizations | May 2024 | https://csrc.nist.gov/publications/detail/sp/800-171/rev-3/final | The primary document. Defines required security controls for CUI. Referenced by DFARS 252.204-7012. |
| SP 800-171A Rev. 3 | Assessing Security Requirements for Controlled Unclassified Information | Jun 2024 | https://csrc.nist.gov/publications/detail/sp/800-171a/rev-3/final | Assessment procedures and determination statements for evaluating compliance with each 800-171 control. |
| SP 800-172 | Enhanced Security Requirements for Protecting Controlled Unclassified Information | Feb 2021 | https://csrc.nist.gov/publications/detail/sp/800-172/final | Advanced controls beyond 800-171 for CUI associated with critical programs or high-value assets. |
| SP 800-37 Rev. 2 | Risk Management Framework for Information Systems and Organizations | Dec 2018 | https://csrc.nist.gov/publications/detail/sp/800-37/rev-2/final | Lifecycle process for system authorization. Provides context for how contractor systems integrate with federal risk management. |
| SP 800-63-4 | Digital Identity Guidelines | Dec 2024 | https://csrc.nist.gov/publications/detail/sp/800-63/4/final | Referenced for 800-171 identification and authentication controls (MFA, credential management). |


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

---

*End of NISTDocs.md — Next: ORGANIZATIONAL_STRUCTURE.md*
