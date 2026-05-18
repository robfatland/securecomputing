"""
Compute Stack
==============
- EC2 IDE instances (t3.medium, one per researcher) (~$30/month each at biz hours)
- Auto-start/stop Lambda + EventBridge schedule
- SSM Session Manager access (no SSH, no public IPs)

Cost: ~$180/month (6 instances × $30 at business hours)

Note: SageMaker notebooks are provisioned separately (manual or future stack)
since they have their own lifecycle management.
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_kms as kms,
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
)
from constructs import Construct


class ComputeStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 destroy_mode: bool = True,
                 vpc: ec2.Vpc = None,
                 infra_key: kms.Key = None,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal = RemovalPolicy.DESTROY if destroy_mode else RemovalPolicy.RETAIN

        # IAM Role for IDE instances (SSM access + basic operations)
        self.ide_role = iam.Role(self, "IDEInstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"  # Enables Session Manager
                ),
            ],
        )

        # Security group for IDE instances
        self.ide_sg = ec2.SecurityGroup(self, "IDESecurityGroup",
            vpc=vpc,
            description="IDE instances - no inbound; outbound restricted",
            allow_all_outbound=False,  # Restrict outbound explicitly
        )
        # No inbound rules — access is via SSM Session Manager only

        # Outbound: allow HTTPS to VPC CIDR (for VPC endpoints)
        self.ide_sg.add_egress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(443),
            "HTTPS to VPC endpoints",
        )

        # Outbound: S3 uses Gateway Endpoint (route table based, no SG rule needed)

        # Outbound: allow HTTPS to GitHub IPs (via NAT)
        # GitHub publishes IPs at https://api.github.com/meta
        # Major ranges (as of 2024): 140.82.112.0/20, 143.55.64.0/20, 185.199.108.0/22, 192.30.252.0/22
        github_cidrs = [
            "140.82.112.0/20",
            "143.55.64.0/20",
            "185.199.108.0/22",
            "192.30.252.0/22",
            "20.201.28.0/24",
            "4.148.0.0/16",
        ]
        for cidr in github_cidrs:
            self.ide_sg.add_egress_rule(
                ec2.Peer.ipv4(cidr),
                ec2.Port.tcp(443),
                f"HTTPS to GitHub ({cidr})",
            )
            self.ide_sg.add_egress_rule(
                ec2.Peer.ipv4(cidr),
                ec2.Port.tcp(22),
                f"SSH to GitHub ({cidr}) for git+ssh",
            )

        # Outbound: allow DNS (needed for resolution)
        self.ide_sg.add_egress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(53),
            "DNS (TCP)",
        )
        self.ide_sg.add_egress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.udp(53),
            "DNS (UDP)",
        )

        # Outbound: allow NFS to EFS (port 2049) within VPC
        self.ide_sg.add_egress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(2049),
            "NFS to EFS",
        )

        # Outbound: allow PostgreSQL to RDS within VPC
        self.ide_sg.add_egress_rule(
            ec2.Peer.ipv4(vpc.vpc_cidr_block),
            ec2.Port.tcp(5432),
            "PostgreSQL to RDS",
        )

        # Create 6 IDE instances (PI, Postdoc, Co-PI, Students 1-3)
        researcher_names = ["pi", "postdoc", "copi", "student1", "student2", "student3"]
        self.instances = []

        for name in researcher_names:
            instance = ec2.Instance(self, f"IDE-{name}",
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MEDIUM,
                ),
                machine_image=ec2.MachineImage.latest_amazon_linux2023(),
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ),
                security_group=self.ide_sg,
                role=self.ide_role,
                block_devices=[
                    ec2.BlockDevice(
                        device_name="/dev/xvda",
                        volume=ec2.BlockDeviceVolume.ebs(
                            volume_size=50,  # GB
                            encrypted=True,
                        ),
                    ),
                ],
            )
            # Tag for auto-start/stop Lambda
            instance.instance.add_property_override("Tags", [
                {"Key": "project", "Value": "securecomputing"},
                {"Key": "role", "Value": "ide"},
                {"Key": "researcher", "Value": name},
                {"Key": "auto-manage", "Value": "true"},
            ])
            self.instances.append(instance)

        # --- Auto-Start/Stop Lambda ---
        auto_manage_code = """
import boto3
import os

ec2_client = boto3.client('ec2')

def handler(event, context):
    action = event.get('action', 'stop')
    
    # Find all instances tagged for auto-management
    response = ec2_client.describe_instances(
        Filters=[
            {'Name': 'tag:project', 'Values': ['securecomputing']},
            {'Name': 'tag:role', 'Values': ['ide']},
            {'Name': 'tag:auto-manage', 'Values': ['true']},
        ]
    )
    
    instance_ids = []
    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            
            # Check keep-alive tag (skip stop if tagged)
            tags = {t['Key']: t['Value'] for t in instance.get('Tags', [])}
            
            if action == 'stop':
                if tags.get('keep-alive') == 'true':
                    print(f"Skipping {instance_id} (keep-alive=true)")
                    continue
                if state == 'running':
                    instance_ids.append(instance_id)
            elif action == 'start':
                if state == 'stopped':
                    instance_ids.append(instance_id)
                # Clear keep-alive tag on start
                if tags.get('keep-alive') == 'true':
                    ec2_client.delete_tags(
                        Resources=[instance_id],
                        Tags=[{'Key': 'keep-alive'}]
                    )
    
    if instance_ids:
        if action == 'stop':
            ec2_client.stop_instances(InstanceIds=instance_ids)
            print(f"Stopped: {instance_ids}")
        elif action == 'start':
            ec2_client.start_instances(InstanceIds=instance_ids)
            print(f"Started: {instance_ids}")
    else:
        print(f"No instances to {action}")
    
    return {'action': action, 'instances': instance_ids}
"""

        auto_manage_fn = lambda_.Function(self, "AutoManageLambda",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.handler",
            code=lambda_.Code.from_inline(auto_manage_code),
            timeout=Duration.seconds(60),
            environment={"REGION": self.region},
        )

        # Grant EC2 permissions to Lambda
        auto_manage_fn.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "ec2:DescribeInstances",
                "ec2:StartInstances",
                "ec2:StopInstances",
                "ec2:DeleteTags",
            ],
            resources=["*"],
            conditions={
                "StringEquals": {"ec2:ResourceTag/project": "securecomputing"}
            },
        ))
        # DescribeInstances needs unrestricted resource
        auto_manage_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["ec2:DescribeInstances"],
            resources=["*"],
        ))

        # EventBridge: Auto-Start at 6 AM Pacific (Mon-Fri)
        events.Rule(self, "AutoStartRule",
            schedule=events.Schedule.cron(
                minute="0", hour="13",  # 13:00 UTC = 6:00 AM Pacific
                week_day="MON-FRI",
            ),
            targets=[targets.LambdaFunction(auto_manage_fn,
                event=events.RuleTargetInput.from_object({"action": "start"}),
            )],
        )

        # EventBridge: Auto-Stop at 6 PM Pacific (Mon-Fri)
        events.Rule(self, "AutoStopRule",
            schedule=events.Schedule.cron(
                minute="0", hour="1",  # 01:00 UTC next day = 6:00 PM Pacific
                week_day="MON-FRI",
            ),
            targets=[targets.LambdaFunction(auto_manage_fn,
                event=events.RuleTargetInput.from_object({"action": "stop"}),
            )],
        )
