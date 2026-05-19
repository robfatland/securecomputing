#!/usr/bin/env python3
"""
CDK Application Entry Point
=============================
Defines all infrastructure for the Synthetic PHI Research Environment.

Mode: DESTROY (development default)
- No Object Lock on S3
- No MFA Delete
- 7-day KMS key deletion (AWS minimum)
- Single-AZ everything (cheap)
- RemovalPolicy.DESTROY on all resources

To deploy:   cdk deploy --all
To destroy:  cdk destroy --all
To preview:  cdk synth
"""

import aws_cdk as cdk
from stacks.vpc_stack import VpcStack
from stacks.kms_stack import KmsStack
from stacks.storage_stack import StorageStack
from stacks.compute_stack import ComputeStack
from stacks.monitoring_stack import MonitoringStack

app = cdk.App()

# Configuration
DESTROY_MODE = True  # Development: no retention, no Object Lock, cheap instances
REGION = "us-west-2"
PROJECT_TAG = "securecomputing"

env = cdk.Environment(region=REGION)

# Tag all resources for cost tracking and identification
tags = {
    "project": PROJECT_TAG,
    "mode": "destroy" if DESTROY_MODE else "production",
    "managed-by": "cdk",
}

# --- Stacks (deployed in dependency order) ---

# 1. Networking
vpc_stack = VpcStack(app, "SecureComputing-VPC",
    env=env,
    destroy_mode=DESTROY_MODE,
)

# 2. Encryption keys
kms_stack = KmsStack(app, "SecureComputing-KMS",
    env=env,
    destroy_mode=DESTROY_MODE,
)

# 3. Storage (S3, RDS, EFS)
storage_stack = StorageStack(app, "SecureComputing-Storage",
    env=env,
    destroy_mode=DESTROY_MODE,
    vpc=vpc_stack.vpc,
    phi_data_key=kms_stack.phi_data_key,
    phi_landing_key=kms_stack.phi_landing_key,
    infra_key=kms_stack.infra_key,
)

# 4. Compute (EC2 IDE instances, auto-start/stop)
compute_stack = ComputeStack(app, "SecureComputing-Compute",
    env=env,
    destroy_mode=DESTROY_MODE,
    vpc=vpc_stack.vpc,
    infra_key=kms_stack.infra_key,
    data_bucket=storage_stack.data_bucket,
    phi_data_key=kms_stack.phi_data_key,
)

# 5. Monitoring (CloudTrail, GuardDuty, Config)
monitoring_stack = MonitoringStack(app, "SecureComputing-Monitoring",
    env=env,
    destroy_mode=DESTROY_MODE,
    vpc=vpc_stack.vpc,
    audit_key=kms_stack.audit_key,
    data_bucket=storage_stack.data_bucket,
)

# Apply tags to all stacks
for stack in [vpc_stack, kms_stack, storage_stack, compute_stack, monitoring_stack]:
    for key, value in tags.items():
        cdk.Tags.of(stack).add(key, value)

app.synth()
