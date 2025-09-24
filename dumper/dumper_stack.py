# cdk_dumper_project/cdk_dumper_project_stack.py
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_certificatemanager as acm,
    aws_cognito as cognito,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_actions as elbv2_actions,
    aws_iam as iam,
    aws_route53 as route53,
    aws_s3 as s3,
    aws_wafv2 as wafv2,
)
from aws_cdk.aws_ecr_assets import Platform
from constructs import Construct


class DumperStack(Stack):  # The class name matches the file name
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_name: str,
        domain_name: str,
        cloudfront_domain_name: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.app_name = app_name or "dumper"
        self.domain_name = domain_name or "gds-idea.click"
        self.cloudfront_domain_name = (
            cloudfront_domain_name or "d1cp3mv9sf5cdw.cloudfront.net"
        )
        self.alb_domain_name = f"{self.app_name}.{self.domain_name}"

        # Use existing VPC, user pool, waf, log_bucket.
        VPC_ID = "vpc-0cd35f828528b0830"
        USER_POOL_ID = "eu-west-2_T6nubwfbi"
        WAF_ARN = "arn:aws:wafv2:eu-west-2:992382722318:regional/webacl/gds-idea-auth_waf/4579dad9-1266-41ba-b471-8de45a00c524"

        vpc = ec2.Vpc.from_lookup(self, "ExistingVPC", vpc_id=VPC_ID)
        pool = cognito.UserPool.from_user_pool_id(
            self, "ExistingUserPool", USER_POOL_ID
        )

        parent_hosted_zone = route53.HostedZone.from_lookup(
            self,
            "HostedZone",
            domain_name=self.domain_name,
        )

        app_hosted_zone = route53.HostedZone(
            self,
            f"{self.app_name}HostedZone",
            zone_name=self.alb_domain_name,
        )

        # create delegation
        route53.NsRecord(
            self,
            f"{self.app_name}NsRecord",
            zone=parent_hosted_zone,
            record_name=self.app_name,
            values=app_hosted_zone.hosted_zone_name_servers,
        )

        certificate = acm.Certificate(
            self,
            f"{self.app_name}Certificate",
            domain_name=self.alb_domain_name,
            validation=acm.CertificateValidation.from_dns(parent_hosted_zone),
        )

        client = cognito.UserPoolClient(
            self,
            "Client",
            user_pool=pool,
            user_pool_client_name=f"{self.app_name}UserPoolClient",
            generate_secret=True,
            supported_identity_providers=[
                cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            auth_flows=cognito.AuthFlow(user=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                # You MUST provide the ALB's specific callback URL format
                callback_urls=[f"https://{self.alb_domain_name}/oauth2/idpresponse"],
                logout_urls=[f"https://{self.alb_domain_name}"],
            ),
        )

        user_pool_domain = cognito.UserPoolDomain.from_domain_name(
            self,
            "ExistingCustomCognitoDomain",
            user_pool_domain_name=f"auth.{self.domain_name}",
        )

        cognito.CfnManagedLoginBranding(
            self,
            "MyCfnManagedLoginBranding",
            user_pool_id=pool.user_pool_id,
            client_id=client.user_pool_client_id,
            use_cognito_provided_values=True,
        )

        cluster = ecs.Cluster(self, f"{self.app_name}Cluster", vpc=vpc)
        role = iam.Role(
            self,
            f"{self.app_name}TaskRole",
            # This principal allows the ECS task to assume this role
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        # Define the Fargate Task
        task_definition = ecs.FargateTaskDefinition(
            self,
            f"{self.app_name}TaskDef",
            memory_limit_mib=512,
            cpu=256,
            task_role=role,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.X86_64,
            ),
        )
        task_definition.add_container(
            f"{self.app_name}Container",
            image=ecs.ContainerImage.from_asset(
                ".",
                file="src/Dockerfile",
                # ADD THIS: Tell the CDK asset builder to build for the same architecture
                platform=Platform.LINUX_AMD64,
            ),
            port_mappings=[ecs.PortMapping(container_port=80)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix=f"{self.app_name}-app"),
        )
        # ## 5. Create the Fargate Service
        # This runs and maintains your task definition.
        fargate_service = ecs.FargateService(
            self,
            f"{self.app_name}FargateService",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=1,
            # CHANGE THIS: Deploy into PUBLIC subnets instead of private ones.
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            # ADD THIS: Assign a public IP so the task can pull its Docker image.
            assign_public_ip=True,
        )

        target_group = elbv2.ApplicationTargetGroup(
            self,
            f"{self.app_name}TargetGroup",
            vpc=vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[fargate_service],
            health_check={
                "path": "/",
                "healthy_threshold_count": 2,
                "unhealthy_threshold_count": 5,
                "interval": Duration.seconds(30),
            },
        )

        ### --- CREATE THE LOAD BALANCER AND LISTENERS --- ###
        # this should load the
        # 1. Create an S3 bucket to store the logs

        log_bucket = s3.Bucket.from_bucket_name(
            self, "ALBAccessLogsBucket", f"{self.domain_name}-logs"
        )

        lb = elbv2.ApplicationLoadBalancer(
            self,
            f"{self.app_name}-alb",
            vpc=vpc,
            internet_facing=True,
        )

        lb.log_access_logs(log_bucket, prefix=f"access/{self.alb_domain_name}")
        lb.log_connection_logs(log_bucket, prefix=f"connection/{self.alb_domain_name}")

        # 2. Add a listener on Port 80 to redirect to HTTPS
        lb.add_listener(
            "HttpListener",
            port=80,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS", port="443", permanent=True
            ),
        )

        # 3. Add the HTTPS listener and the Cognito authentication rule
        https_listener = lb.add_listener(
            "HttpsListener",
            port=443,
            certificates=[certificate],  # Uses the certificate you already created
            default_action=elbv2_actions.AuthenticateCognitoAction(
                user_pool=pool,
                user_pool_client=client,
                user_pool_domain=user_pool_domain,
                # After a successful login, forward the request to your Fargate service
                next=elbv2.ListenerAction.forward([target_group]),
            ),
        )

        # --- Step 2: Create the association ---
        # This construct creates the link between the WAF and the ALB.

        waf_association = wafv2.CfnWebACLAssociation(
            self,
            "WAF-ALB-Association",
            resource_arn=lb.load_balancer_arn,
            web_acl_arn=WAF_ARN,
        )

        # 5. Output the ALB's DNS name for reference
        CfnOutput(self, "LoadBalancerDNS", value=lb.load_balancer_dns_name)
