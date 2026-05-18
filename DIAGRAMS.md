# System Architecture Diagrams

These diagrams render automatically on GitHub. For local rendering, paste into [mermaid.live](https://mermaid.live).

---

## Network Architecture

```mermaid
graph TB
    subgraph Internet
        Laptop[Researcher Laptop<br/>No PHI stored]
        GitHub[GitHub<br/>Code only, no PHI]
    end

    subgraph AWS Account
        subgraph VPC["VPC (10.0.0.0/16)"]
            subgraph Public["Public Subnet (NAT only)"]
                NAT[NAT Gateway<br/>Restricted to GitHub IPs]
            end

            subgraph Private["Private Subnets (all resources)"]
                EC2_PI[EC2: PI IDE<br/>t3.medium]
                EC2_PD[EC2: Postdoc IDE]
                EC2_S1[EC2: Student 1]
                EC2_S2[EC2: Student 2]
                EC2_S3[EC2: Student 3]
                EC2_CP[EC2: Co-PI IDE]
                RDS[(RDS PostgreSQL<br/>OMOP tables)]
                EFS[(EFS Shared<br/>Filesystem)]
                Lambda[Lambda:<br/>Gatekeeper +<br/>Auto-start/stop]
            end

            subgraph Endpoints["VPC Endpoints (private AWS access)"]
                EP_S3[S3 Gateway]
                EP_SSM[SSM]
                EP_KMS[KMS]
                EP_CW[CloudWatch]
                EP_BR[Bedrock]
                EP_CM[Comprehend Medical]
                EP_ECR[ECR]
                EP_STS[STS]
            end
        end

        subgraph Services["AWS Services (outside VPC, accessed via endpoints)"]
            S3[(S3: PHI Data<br/>+ Audit Logs)]
            Bedrock[Bedrock<br/>LLM Inference]
            CompMed[Comprehend Medical<br/>PHI Detection]
            CloudTrail[CloudTrail<br/>API Logging]
            GuardDuty[GuardDuty<br/>Threat Detection]
            KMS[KMS<br/>4 Encryption Keys]
        end
    end

    Laptop -->|SSO + MFA| EP_SSM
    EP_SSM --> EC2_PI
    EP_SSM --> EC2_PD
    EP_SSM --> EC2_S1

    EC2_PI --> EP_S3
    EC2_PI --> EP_BR
    EP_S3 --> S3
    EP_BR --> Lambda
    Lambda --> EP_CM
    EP_CM --> CompMed
    Lambda --> Bedrock

    EC2_PI --> RDS
    EC2_PI --> EFS
    EC2_PI --> NAT
    NAT --> GitHub

    CloudTrail -.->|logs all API calls| S3
    GuardDuty -.->|monitors| CloudTrail
```

---

## Data Flow

```mermaid
graph LR
    subgraph Generation["securecomputing-datagen"]
        Synthea[Synthea<br/>11K patients] --> ETL[Custom ETL]
        ETL --> PD0[PD0: OMOP CSVs]
        Stones[Stone Assignment] --> PD1[PD1: 14K CIF files]
        Stones --> PD2[PD2: 11K VCF files]
        Stones --> PD3[PD3: 1.5M lab rows]
        PD0 --> Manifest[manifest.json<br/>SHA-256 checksums]
        PD1 --> Manifest
        PD2 --> Manifest
        PD3 --> Manifest
    end

    subgraph Upload["Upload Path"]
        Manifest --> S3Land[S3: /landing/]
        S3Land --> ValLambda[Validation Lambda<br/>Verify checksums]
        ValLambda -->|valid| S3Val[S3: /validated/]
        ValLambda -->|invalid| Quarantine[Quarantine + Alert]
    end

    subgraph Storage["Analysis Environment"]
        S3Val --> RDS[(RDS PostgreSQL<br/>OMOP tables)]
        S3Val --> S3Proc[S3: /processed/]
        S3Val --> S3Files[S3: /pd1, /pd2, /pd3 files]
        RDS --> DocDB[(DocumentDB<br/>Patient documents)]
    end

    subgraph Analysis["Research Workflow"]
        IDE[IDE: Kiro/VS Code] --> RDS
        IDE --> S3Files
        Notebook[SageMaker Notebook] --> RDS
        Notebook --> S3Files
        IDE --> Gatekeeper[Gatekeeper Lambda]
        Gatekeeper --> CompMed[Comprehend Medical<br/>PHI scan]
        CompMed -->|clean| Bedrock[Bedrock LLM]
        CompMed -->|PHI detected| Block[Block + Notify]
    end

    subgraph Audit["Audit Trail"]
        CloudTrail[CloudTrail] --> AuditS3[S3: Audit Bucket<br/>Encrypted, immutable]
        Gatekeeper --> AuditS3
        GuardDuty[GuardDuty] --> SecHub[Security Hub]
        Config[AWS Config] --> SecHub
        SecHub --> Alerts[Wickr Alerts]
    end
```

---

## IAM Role Hierarchy

```mermaid
graph TD
    subgraph Human Roles
        PI[ProjectAdmin<br/>Dr. D.R. Smith<br/>Full access + audit]
        IT[InfraAdmin<br/>IT Staff<br/>Infrastructure only<br/>NO PHI decrypt]
        SR[SeniorResearcher<br/>Postdoc + Co-PI<br/>Full study data]
        R[Researcher<br/>Students 1-3<br/>Full study data]
    end

    subgraph Service Roles
        GK[GatekeeperLambdaRole<br/>Comprehend + Bedrock]
        VL[ValidationLambdaRole<br/>S3 landing → validated]
        ECS[ECSTaskRole<br/>S3 + RDS read/write]
        CT[CloudTrailRole<br/>Write to audit bucket]
        CFG[ConfigRole<br/>Read-only all resources]
    end

    subgraph KMS Keys
        PHI[phi-data-key]
        LAND[phi-landing-key]
        AUDIT[audit-key]
        INFRA[infra-key]
    end

    PI -->|decrypt| PHI
    PI -->|decrypt| AUDIT
    SR -->|decrypt| PHI
    R -->|decrypt| PHI
    IT -->|admin but NO decrypt| PHI
    IT -->|decrypt| INFRA
    IT -->|encrypt| LAND

    GK -->|encrypt/decrypt| PHI
    VL -->|decrypt| LAND
    VL -->|encrypt| PHI
    ECS -->|decrypt| PHI
    CT -->|encrypt| AUDIT
```

---

## Lifecycle Modes

```mermaid
stateDiagram-v2
    [*] --> Deployed: cdk deploy --all
    Deployed --> Active: Auto-Start (6AM Mon-Fri)
    Active --> Idle: Auto-Stop (6PM Mon-Fri)
    Idle --> Active: Auto-Start or Manual Start
    
    Active --> Hibernated: ops/hibernate.sh
    Idle --> Hibernated: ops/hibernate.sh
    Hibernated --> Active: ops/wake.sh
    
    Active --> Destroyed: cdk destroy --all
    Idle --> Destroyed: cdk destroy --all
    Hibernated --> Destroyed: cdk destroy --all
    
    Destroyed --> [*]

    note right of Active: ~$400/month
    note right of Hibernated: ~$100/month
    note right of Destroyed: $0
```
