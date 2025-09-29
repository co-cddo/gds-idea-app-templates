import logging
from dataclasses import dataclass
from enum import Enum

from aws_cdk import Environment as CdkEnvironment

logger = logging.getLogger(__name__)


class DeploymentEnvironment(Enum):
    DEV = "992382722318"
    PROD = "588077357019"

    @classmethod
    def from_cdk_env(cls, cdk_env: CdkEnvironment) -> "DeploymentEnvironment ":
        """Get environment from CDK Environment."""
        if not cdk_env.account:
            raise ValueError("CDK Environment must have account specified")
        return cls.from_account_id(cdk_env.account)

    @classmethod
    def from_account_id(cls, account_id: str) -> "DeploymentEnvironment ":
        """Get environment from account ID."""
        for env in cls:
            if env.value == account_id:
                return env
        raise ValueError(f"Unknown account ID: {account_id}")

    @property
    def friendly_name(self) -> str:
        """Get lowercase environment name for display/logging."""
        return self.name.lower()


@dataclass
class EnvConfig:
    """Configuration for GDS Idea web applications."""

    def __init__(self, cdk_env: CdkEnvironment):
        """Create EnvConfig for the given CDK Environment."""
        # Validate region
        if cdk_env.region and cdk_env.region != "eu-west-2":
            logger.warning(f"Using region '{cdk_env.region}' - eu-west-2 is preferred")

        # Get environment from CDK env
        try:
            environment = DeploymentEnvironment.from_cdk_env(cdk_env)
        except ValueError as e:
            raise ValueError(f"CDK Environment not configured. {e}") from e

        if environment == DeploymentEnvironment.PROD:
            logger.warning(
                f"Deploying to {environment.friendly_name.upper()} environment "
                "- please double-check configuration"
            )

        # Set instance variables
        self.cdk_env = cdk_env
        self.environment = environment

        # Set environment-specific configuration
        if environment == DeploymentEnvironment.DEV:
            self.domain_name = "gds-idea.click"
            self.cloudfront_domain_name = "d1cp3mv9sf5cdw.cloudfront.net"
            self.vpc_id = "vpc-0cd35f828528b0830"
            self.user_pool_id = "eu-west-2_T6nubwfbi"
            self.waf_arn = (
                "arn:aws:wafv2:eu-west-2:992382722318:regional/webacl/"
                "gds-idea-auth_waf/4579dad9-1266-41ba-b471-8de45a00c524"
            )
            self.log_bucket_name = "gds-idea.click-logs"
        else:
            # Prod environment - you'll need to provide these values
            raise NotImplementedError("Prod environment configuration not yet defined")
