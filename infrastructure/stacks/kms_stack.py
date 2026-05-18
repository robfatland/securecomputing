"""
KMS Stack
==========
Four encryption keys separated by function:
- phi_data_key: Protects research data (S3 validated/processed/derived, RDS, EFS)
- phi_landing_key: Protects raw upload zone
- audit_key: Protects audit logs (CloudTrail, gatekeeper decisions)
- infra_key: Protects infrastructure (EBS, ECR, Secrets Manager)

DESTROY mode: 7-day pending deletion (AWS minimum).
PRODUCTION mode: 30-day pending deletion.

Cost: $1/key/month = $4/month total.
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_kms as kms,
)
from constructs import Construct


class KmsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 destroy_mode: bool = True, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal = RemovalPolicy.DESTROY if destroy_mode else RemovalPolicy.RETAIN
        pending_window = Duration.days(7) if destroy_mode else Duration.days(30)

        # PHI Data Key — researchers can decrypt; IT Staff cannot
        self.phi_data_key = kms.Key(self, "PhiDataKey",
            alias="securecomputing/phi-data",
            description="Encrypts research PHI data (S3 validated/processed/derived, RDS, EFS)",
            enable_key_rotation=True,
            pending_window=pending_window,
            removal_policy=removal,
        )

        # PHI Landing Key — only upload role and validation Lambda
        self.phi_landing_key = kms.Key(self, "PhiLandingKey",
            alias="securecomputing/phi-landing",
            description="Encrypts raw PHI uploads in S3 landing zone",
            enable_key_rotation=True,
            pending_window=pending_window,
            removal_policy=removal,
        )

        # Audit Key — only PI can decrypt for review
        self.audit_key = kms.Key(self, "AuditKey",
            alias="securecomputing/audit",
            description="Encrypts audit logs (CloudTrail, gatekeeper, Config)",
            enable_key_rotation=True,
            pending_window=pending_window,
            removal_policy=removal,
        )

        # Infrastructure Key — IT Staff can decrypt
        self.infra_key = kms.Key(self, "InfraKey",
            alias="securecomputing/infra",
            description="Encrypts infrastructure (EBS, ECR, Secrets Manager)",
            enable_key_rotation=True,
            pending_window=pending_window,
            removal_policy=removal,
        )
