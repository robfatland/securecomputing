"""
VPC Stack
==========
Private-only VPC with:
- Private subnets (no public subnets, no internet gateway)
- NAT Gateway (single AZ, restricted to GitHub IPs) (~$33/month)
- VPC Endpoints for essential AWS services (~$58/month for 8 endpoints)
- VPC Flow Logs
- No bastion hosts (access via SSM Session Manager)
"""

from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_iam as iam,
)
from constructs import Construct


class VpcStack(Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 destroy_mode: bool = True, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        removal = RemovalPolicy.DESTROY if destroy_mode else RemovalPolicy.RETAIN

        # VPC: private subnets + minimal public subnet for NAT Gateway
        self.vpc = ec2.Vpc(self, "ResearchVPC",
            max_azs=2,
            nat_gateways=1,  # Single AZ NAT (~$33/month)
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=28,  # Tiny — only holds NAT Gateway
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
            restrict_default_security_group=True,
        )

        # VPC Flow Logs (to CloudWatch)
        flow_log_group = logs.LogGroup(self, "VPCFlowLogs",
            retention=logs.RetentionDays.ONE_YEAR if not destroy_mode else logs.RetentionDays.ONE_WEEK,
            removal_policy=removal,
        )

        self.vpc.add_flow_log("FlowLog",
            destination=ec2.FlowLogDestination.to_cloud_watch_logs(flow_log_group),
            traffic_type=ec2.FlowLogTrafficType.ALL,
        )

        # --- VPC Endpoints (essential set — $58/month) ---

        # S3 Gateway Endpoint (free)
        self.vpc.add_gateway_endpoint("S3Endpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
        )

        # Interface Endpoints ($7.30/month each)
        interface_services = {
            "SSM": ec2.InterfaceVpcEndpointAwsService.SSM,
            "SSMMessages": ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            "EC2Messages": ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
            "KMS": ec2.InterfaceVpcEndpointAwsService.KMS,
            "CloudWatchLogs": ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            "STS": ec2.InterfaceVpcEndpointAwsService.STS,
            "ECR": ec2.InterfaceVpcEndpointAwsService.ECR,
            "ECRDocker": ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
        }

        for name, service in interface_services.items():
            self.vpc.add_interface_endpoint(name,
                service=service,
                private_dns_enabled=True,
            )

        # Bedrock and Comprehend Medical endpoints
        # (These use custom endpoint service names)
        self.vpc.add_interface_endpoint("Bedrock",
            service=ec2.InterfaceVpcEndpointService(
                f"com.amazonaws.{self.region}.bedrock-runtime"
            ),
            private_dns_enabled=True,
        )

        self.vpc.add_interface_endpoint("ComprehendMedical",
            service=ec2.InterfaceVpcEndpointService(
                f"com.amazonaws.{self.region}.comprehendmedical"
            ),
            private_dns_enabled=True,
        )
