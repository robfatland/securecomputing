"""
Monitoring Stack
=================
- CloudTrail (all events + S3 data events)
- GuardDuty (threat detection)
- AWS Config (compliance rules)
- Security Hub (aggregation)

Cost: ~$10–15/month (GuardDuty + Config evaluations + CloudTrail data events)

Note: Macie is deferred (add later for $50-100/month if needed).
CloudTrail logs go to the data bucket /audit/ prefix (in production,
these would go to a separate Audit account).
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_cloudtrail as cloudtrail,
    aws_guardduty as guardduty,
    aws_config as config,
    aws_s3 as s3,
    aws_kms as kms,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


class MonitoringStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 destroy_mode: bool = True,
                 vpc: ec2.Vpc = None,
                 audit_key: kms.Key = None,
                 data_bucket: s3.Bucket = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal = RemovalPolicy.DESTROY if destroy_mode else RemovalPolicy.RETAIN

        # --- Audit Log Bucket ---
        # In production this would be in a separate Audit account.
        # For development, separate bucket in same account.
        self.audit_bucket = s3.Bucket(self, "AuditBucket",
            encryption=s3.BucketEncryption.KMS,
            encryption_key=audit_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=removal,
            auto_delete_objects=destroy_mode,
            enforce_ssl=True,
        )

        # --- CloudTrail ---
        self.trail = cloudtrail.Trail(self, "ProjectTrail",
            bucket=self.audit_bucket,
            encryption_key=audit_key,
            is_multi_region_trail=False,  # Single region (us-west-2) for cost
            include_global_service_events=True,
            send_to_cloud_watch_logs=False,  # Save cost; logs in S3
            enable_file_validation=True,
        )

        # Log S3 data events (GetObject, PutObject) on the data bucket
        self.trail.add_s3_event_selector(
            [cloudtrail.S3EventSelector(bucket=data_bucket)],
            include_management_events=False,
        )

        # --- GuardDuty ---
        # Enable threat detection (~$4/million events)
        guardduty.CfnDetector(self, "GuardDutyDetector",
            enable=True,
            finding_publishing_frequency="FIFTEEN_MINUTES",
        )

        # --- AWS Config ---
        # Config recorder + delivery channel
        config_role = iam.Role(self, "ConfigRole",
            assumed_by=iam.ServicePrincipal("config.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWS_ConfigRole"),
            ],
        )

        config.CfnConfigurationRecorder(self, "ConfigRecorder",
            role_arn=config_role.role_arn,
            recording_group=config.CfnConfigurationRecorder.RecordingGroupProperty(
                all_supported=True,
                include_global_resource_types=True,
            ),
        )

        config.CfnDeliveryChannel(self, "ConfigDelivery",
            s3_bucket_name=self.audit_bucket.bucket_name,
            s3_key_prefix="config/",
        )

        # --- Key Config Rules (subset of HIPAA conformance pack) ---
        # These are the critical rules; full conformance pack can be added later

        config.ManagedRule(self, "S3EncryptionRule",
            identifier="S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED",
            config_rule_name="s3-encryption-enabled",
        )

        config.ManagedRule(self, "S3PublicReadRule",
            identifier="S3_BUCKET_PUBLIC_READ_PROHIBITED",
            config_rule_name="s3-no-public-read",
        )

        config.ManagedRule(self, "RDSEncryptionRule",
            identifier="RDS_STORAGE_ENCRYPTED",
            config_rule_name="rds-encrypted",
        )

        config.ManagedRule(self, "EBSEncryptionRule",
            identifier="ENCRYPTED_VOLUMES",
            config_rule_name="ebs-encrypted",
        )

        config.ManagedRule(self, "CloudTrailEnabledRule",
            identifier="CLOUD_TRAIL_ENABLED",
            config_rule_name="cloudtrail-enabled",
        )
