# Organizational Structure: Large R1 University Medical Research Environment

## Context

Large R1 University with a Medical Department that collects clinical data. Research teams conduct clinical research using this data, including external collaborators at non-University medical facilities.

---

## Organizational Entities and Roles

### 1. Research Team (Primary User Group)

Located within a specific department (e.g., Anesthesiology).

#### Roles and Responsibilities:

**Principal Investigator (PI)**
- Leads the research project
- Responsible for research protocol and compliance
- Approves data access requests
- Accountable for team's use of PHI
- PHI Access Level: Full project access for research purposes
- Responsibilities: Ensures team adheres to protocol, monitors compliance

**Co-Investigator (Co-I)**
- Assists with research design and execution
- May supervise day-to-day research activities
- Reports to PI
- PHI Access Level: Full project access for research purposes
- Responsibilities: Day-to-day oversight, protocol adherence

**Developer**
- Builds systems and software for data analysis
- May create data pipelines or research applications
- Works with de-identified or minimally identifiable data where possible
- PHI Access Level: Limited to necessary data for system development (minimum necessary)
- Responsibilities: Secure coding practices, data handling compliance

**Data Analyst**
- Performs statistical analysis on research data
- Queries and manipulates research datasets
- Prepares findings for publication/reporting
- PHI Access Level: Research project datasets (may contain identifiers)
- Responsibilities: Data handling security, analysis audit trail

**Collaborator PI (External, Non-University Medical Facility)**
- Academic researcher at another institution with access to patient data at their facility
- Partners on multi-site research studies
- Exchanges de-identified data across institutional boundaries
- PHI Access Level: Limited to de-identified or coded data; direct PHI access per BAA only
- Responsibilities: Compliance at their institution, data use restrictions

---

### 2. Departmental Administration

Located within the academic department (e.g., Anesthesiology Department).

#### Roles and Responsibilities:

**Department Chair**
- Oversees departmental operations and compliance
- Approves research protocols at departmental level
- Accountable for departmental resources
- Ensures PI accountability for team compliance
- PHI Access Level: Administrative (no direct PHI access for clinical research data)
- Responsibilities: Departmental governance, escalation authority

**Department Compliance Officer / Manager**
- Day-to-day compliance oversight for departmental research
- Reviews data use agreements and team access
- May coordinate with IRB and CISO
- Documents compliance activities
- PHI Access Level: Administrative (no direct PHI access for clinical research data)
- Responsibilities: Policy enforcement, documentation, training coordination

---

### 3. Institutional Review Board (IRB)

University-wide body governing human subjects research.

#### Roles and Responsibilities:

**IRB Director**
- Oversees all human subjects research at the institution
- Approves research protocols involving human subjects
- Reviews risk and benefit assessments
- Authority to approve, modify, or deny research
- PHI Access Level: Administrative review (may access protocol details, not operational data)
- Responsibilities: Protocol review, compliance monitoring, regulatory reporting

**IRB Coordinator**
- Manages IRB submission and review processes
- Communicates decisions to researchers
- Monitors ongoing research for compliance
- PHI Access Level: Administrative (protocol reviews, not operational data)
- Responsibilities: Process management, compliance tracking

---

### 4. Chief Information Security Officer (CISO)

University-wide information security leadership.

#### Roles and Responsibilities:

**CISO / Security Officer**
- Responsible for enterprise information security strategy
- Ensures infrastructure meets HIPAA Security Rule requirements
- Defines security policies and standards
- Oversees incident response
- May delegate technical implementation to Medical IT
- PHI Access Level: Strategic/administrative (audit and monitoring)
- Responsibilities: Security policy, risk management, incident response leadership, compliance validation

**Security Team Members** (reporting to CISO)
- Implement and monitor security controls
- Conduct vulnerability assessments
- Respond to security incidents
- Maintain audit logs and monitoring systems
- PHI Access Level: Limited to what's necessary for security monitoring
- Responsibilities: Technical security implementation, incident response

---

### 5. Medical IT Organization

University hospital/medical center IT operations.

#### Roles and Responsibilities:

**Medical IT Director**
- Oversees all clinical IT systems including EMR/EHR
- Custodian of clinical data
- Ensures EMR infrastructure security and availability
- Manages data access provisioning and de-identification
- PHI Access Level: Full (necessary for system administration and custodianship)
- Responsibilities: Data security, access control, system administration

**EMR Data Administrator**
- Manages EMR database, access provisioning, and data exports
- Handles de-identification and data preparation for research
- Responds to data requests from authorized researchers
- Maintains data dictionary and documentation
- PHI Access Level: Full (necessary for data administration)
- Responsibilities: Data provisioning, de-identification, documentation

**Database Administrator (DBA)**
- Manages databases where EMR and research data reside
- Ensures backup, recovery, and system performance
- Implements encryption and access controls
- PHI Access Level: Full (necessary for database administration)
- Responsibilities: Data infrastructure, backup/recovery, encryption implementation

**Network & Security Operations**
- Manages network infrastructure supporting research environments
- Implements firewalls, VPNs, network segmentation
- Monitors network activity for security incidents
- PHI Access Level: Limited to what's necessary for infrastructure monitoring
- Responsibilities: Network security, incident detection

---

## Data Flow Summary

```
Clinical Patients
      ↓
EMR/EHR System (Medical IT custodian)
      ↓
De-identification / Data Request Process
      ↓
Research Data (Researcher access)
      ↓
Analysis / Publication
```

## Access Control Matrix

| Role | Clinical EMR | De-identified Research Data | System Admin | Audit Logs | Policy Decisions |
|------|---|---|---|---|---|
| PI | Limited (approved studies) | Full (approved studies) | None | Own team only | Yes (team-level) |
| Co-I | Limited (approved studies) | Full (approved studies) | None | Own team only | Some (team-level) |
| Developer | Minimum necessary | Limited (dev datasets) | None | Own code/systems | No |
| Data Analyst | Limited (approved data) | Full (approved studies) | None | Own analysis only | No |
| Ext. Collaborator PI | Per BAA only | De-identified only | None | None | Limited (external) |
| Dept. Chair | None | None | Departmental oversight | None | Yes (departmental) |
| Dept. Compliance Officer | None | None | None | Departmental access | Yes (enforce policies) |
| IRB Director | Protocol review only | None | None | Protocol reviews | Yes (protocol approval) |
| IRB Coordinator | Protocol review only | None | None | Protocol reviews | No (process execution) |
| CISO | Audit/strategic | Audit/strategic | Audit/strategic | Full (security) | Yes (security policy) |
| Medical IT Director | Full (custodian) | Full (custodian) | Full | Full | Yes (data custodian) |
| EMR Data Admin | Full (custodian) | Full (custodian) | System data access | Full (custodian) | No (policy execution) |
| DBA | Full (custodian) | Full (custodian) | Full | Full | No (policy execution) |

---

## Key Compliance Considerations

### HIPAA Roles in This Structure

1. **Covered Entity**: The University (medical school/hospital)
   - Responsible for HIPAA compliance
   - Liability for all workforce member actions

2. **Business Associates**: 
   - External Collaborator institution (via Business Associate Agreement)
   - Cloud service providers (if used)

3. **Workforce Members**: All roles listed above
   - Subject to HIPAA training requirements
   - Subject to sanctions policies
   - Monitoring and accountability mechanisms required

### Minimum Necessary Principle

- Researchers should access only data required for their specific research
- Developers should access de-identified data where possible
- Clinical IT should apply de-identification before providing data to research teams

### Accountability and Audit Trail

- All PHI access must be logged and audit trail maintained
- Justification required for each access grant
- Regular review of access logs by appropriate oversight (PI, Dept. Chair, CISO)

### Incident Response

- Clear escalation path: Team member → PI/Dept. Chair → Department Compliance Officer → CISO/Medical IT
- Breach notification procedures involving IRB, CISO, legal
- Documentation of all incidents and responses

---

## Next Steps

1. Map these organizational roles to AWS IAM entities and access patterns
2. Define data flow architecture in AWS
3. Create technical access control policies
4. Design audit and logging mechanisms
