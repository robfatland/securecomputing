"""
Storage Stack
==============
- S3 bucket with zone prefixes (landing/, validated/, processed/, derived/, audit/)
- RDS PostgreSQL (Single-AZ, db.t3.micro) (~$13/month)
- EFS filesystem (One-Zone) (~$8/month for 50GB)

DESTROY mode: auto_delete_objects on S3, skip_final_snapshot on RDS,
RemovalPolicy.DESTROY on all resources.

Cost: ~$33/month (RDS + EFS + S3 storage)
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_s3 as s3,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_efs as efs,
    aws_kms as kms,
)
from constructs import Construct


class StorageStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 destroy_mode: bool = True,
                 vpc: ec2.Vpc = None,
                 phi_data_key: kms.Key = None,
                 phi_landing_key: kms.Key = None,
                 infra_key: kms.Key = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal = RemovalPolicy.DESTROY if destroy_mode else RemovalPolicy.RETAIN

        # --- S3 Data Bucket ---
        # Single bucket with prefix-based zone separation
        self.data_bucket = s3.Bucket(self, "DataBucket",
            bucket_name=None,  # Auto-generated unique name
            encryption=s3.BucketEncryption.KMS,
            encryption_key=phi_data_key,
            versioned=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=removal,
            auto_delete_objects=destroy_mode,
            enforce_ssl=True,
        )

        # --- RDS PostgreSQL ---
        # Single-AZ, db.t3.micro (~$13/month)
        self.db_security_group = ec2.SecurityGroup(self, "RDSSecurityGroup",
            vpc=vpc,
            description="RDS PostgreSQL access",
            allow_all_outbound=False,
        )
        # Allow inbound from VPC CIDR on PostgreSQL port
        self.db_security_group.add_ingress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(5432),
            "PostgreSQL from VPC",
        )

        self.database = rds.DatabaseInstance(self, "OmopDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16,
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO,
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.db_security_group],
            storage_encrypted=True,
            storage_encryption_key=phi_data_key,
            multi_az=False,  # Single-AZ (cheap; risk: no failover)
            allocated_storage=20,  # GB — expandable
            max_allocated_storage=100,
            database_name="omop",
            removal_policy=removal,
            deletion_protection=not destroy_mode,
            backup_retention=Duration.days(7) if not destroy_mode else Duration.days(1),
        )

        # --- EFS Shared Filesystem ---
        # One-Zone for cost savings (~$0.16/GB vs $0.30/GB)
        self.filesystem = efs.FileSystem(self, "SharedEFS",
            vpc=vpc,
            encrypted=True,
            kms_key=phi_data_key,
            performance_mode=efs.PerformanceMode.GENERAL_PURPOSE,
            removal_policy=removal,
            one_zone=True,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                availability_zones=[vpc.availability_zones[0]],
            ),
        )
