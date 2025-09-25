import logging

from aws_cdk import (
    CfnOutput,
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    aws_route53 as route53,
    aws_s3 as s3,
    aws_wafv2 as wafv2,
)
from aws_cdk.aws_ecr_assets import Platform
from aws_cdk.aws_route53_targets import LoadBalancerTarget
from constructs import Construct

from ..config.app_config import AppConfig
from .auth_strategies import CognitoAuthStrategy, IAuthStrategy, NoAuthStrategy

# Import the local types and strategies
from .auth_types import AuthType
from .props import WebAppContainerProperties

logger = logging.getLogger(__name__)


class WebApp(Construct):
    """
    A configurable web application stack with a simplified API for authentication.
    This construct acts as a facade, hiding the internal strategy implementation.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_config: AppConfig,
        app_name: str,
        authentication: AuthType | str = AuthType.NONE,
        docker_context_path: str = ".",
        dockerfile_path: str = "src/Dockerfile",
        container_props: WebAppContainerProperties = None,
    ) -> None:
        super().__init__(scope, construct_id)

        self.app_config = app_config
        self.app_name = app_name
        self.container_props = (
            container_props or WebAppContainerProperties()
        )  # Load the default values

        # Derived configuration
        self.alb_domain_name = f"{self.app_name}.{self.app_config.domain_name}"

        # --- Internal Strategy Factory ---
        # This block translates the simple enum/string into the correct internal strategy object.
        self._auth_strategy: IAuthStrategy
        auth_type_str = str(authentication).lower()

        if auth_type_str == AuthType.COGNITO:
            self._auth_strategy = CognitoAuthStrategy(self, app_config, app_name)
        elif auth_type_str == AuthType.NONE:
            self._auth_strategy = NoAuthStrategy(self, app_config, app_name)
        else:
            raise ValueError(f"Unsupported authentication type: {authentication}")
        # --------------------------------

        logger.info(
            f"Creating web app: {self.app_name} with authentication: {auth_type_str}"
        )
        logger.info(f"Domain: {self.alb_domain_name}")

        # The rest of the construct uses the internal strategy where needed
        self._import_existing_resources()
        self._setup_dns_and_certificate()
        self._setup_ecs_resources(docker_context_path, dockerfile_path)
        self._setup_load_balancer()
        self._setup_dns_record()
        self._associate_waf()
        self._create_outputs()

    def _import_existing_resources(self) -> None:
        """Import existing VPC and other shared resources."""
        self.vpc = ec2.Vpc.from_lookup(
            self, "ExistingVPC", vpc_id=self.app_config.vpc_id
        )

        self.parent_hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=self.app_config.domain_name
        )

        self.log_bucket = s3.Bucket.from_bucket_name(
            self, "ALBAccessLogsBucket", self.app_config.log_bucket_name
        )

    def _setup_dns_and_certificate(self) -> None:
        # This method is unchanged
        self.app_hosted_zone = route53.HostedZone(
            self, "AppHostedZone", zone_name=self.alb_domain_name
        )
        route53.NsRecord(
            self,
            "NsRecord",
            zone=self.parent_hosted_zone,
            record_name=self.app_name,
            values=self.app_hosted_zone.hosted_zone_name_servers,
        )
        self.certificate = acm.Certificate(
            self,
            "Certificate",
            domain_name=self.alb_domain_name,
            validation=acm.CertificateValidation.from_dns(self.parent_hosted_zone),
        )

    def _setup_ecs_resources(
        self, docker_context_path: str, dockerfile_path: str
    ) -> None:
        # This method is unchanged
        cpu = self.container_props.cpu
        memory = self.container_props.memory_limit_mib
        desired_count = self.container_props.desired_count
        container_port = self.container_props.container_port
        environment = self.container_props.environment_variables

        self.cluster = ecs.Cluster(self, "Cluster", vpc=self.vpc)
        self.task_role = iam.Role(
            self, "TaskRole", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            memory_limit_mib=memory,
            cpu=cpu,
            task_role=self.task_role,
        )

        environment = self.container_props.get("environment_variables", {})
        self.container = self.task_definition.add_container(
            "Container",
            image=ecs.ContainerImage.from_asset(
                docker_context_path, file=dockerfile_path, platform=Platform.LINUX_AMD64
            ),
            port_mappings=[ecs.PortMapping(container_port=container_port)],
            logging=ecs.LogDrivers.aws_logs(stream_prefix=f"{self.app_name}-app"),
            environment=environment,
        )

        self.fargate_service = ecs.FargateService(
            self,
            "FargateService",
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=desired_count,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            assign_public_ip=True,
        )

    def _setup_load_balancer(self) -> None:
        """Create ALB, delegating the listener action to the auth strategy."""
        health_check_path = self.container_props.health_check_path
        self.target_group = elbv2.ApplicationTargetGroup(
            self,
            "TargetGroup",
            vpc=self.vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[self.fargate_service],
            health_check={"path": health_check_path},
        )

        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self, "LoadBalancer", vpc=self.vpc, internet_facing=True
        )
        self.load_balancer.log_access_logs(
            self.log_bucket, prefix=f"access/{self.alb_domain_name}"
        )

        self.load_balancer.add_listener(
            "HttpListener",
            port=80,
            default_action=elbv2.ListenerAction.redirect(
                protocol="HTTPS", port="443", permanent=True
            ),
        )

        # DELEGATION: Ask the strategy to create the correct listener action
        default_https_action = self._auth_strategy.create_listener_action(
            self.target_group
        )

        self.load_balancer.add_listener(
            "HttpsListener",
            port=443,
            certificates=[self.certificate],
            default_action=default_https_action,
        )

    def _setup_dns_record(self) -> None:
        # This method is unchanged
        route53.ARecord(
            self,
            "ARecord",
            zone=self.app_hosted_zone,
            target=route53.RecordTarget.from_alias(
                LoadBalancerTarget(self.load_balancer)
            ),
        )

    def _associate_waf(self) -> None:
        # This method is unchanged
        wafv2.CfnWebACLAssociation(
            self,
            "WAF-ALB-Association",
            resource_arn=self.load_balancer.load_balancer_arn,
            web_acl_arn=self.app_config.waf_arn,
        )

    def _create_outputs(self) -> None:
        """Create base outputs and delegate to the strategy for specific outputs."""
        CfnOutput(
            self,
            "ApplicationURL",
            value=f"https://{self.alb_domain_name}",
            description=f"Application URL for {self.app_name}",
        )

        # DELEGATION: Ask the strategy to create its own outputs, if any.
        self._auth_strategy.create_outputs()
