from abc import ABC, abstractmethod

from aws_cdk import (
    CfnOutput,
    aws_cognito as cognito,
    aws_elasticloadbalancingv2 as elbv2,
    aws_elasticloadbalancingv2_actions as elbv2_actions,
)
from constructs import Construct

from ..config.app_config import AppConfig


class IAuthStrategy(ABC):
    """Interface for an authentication strategy."""

    def __init__(self, scope: Construct, app_config: AppConfig, app_name: str):
        self.scope = scope
        self.app_config = app_config
        self.app_name = app_name

    @abstractmethod
    def create_listener_action(
        self, target_group: elbv2.IApplicationTargetGroup
    ) -> elbv2.ListenerAction:
        """Return the ALB listener action for this strategy."""
        pass

    @abstractmethod
    def create_outputs(self) -> None:
        """Create any strategy-specific CloudFormation outputs."""
        pass


class NoAuthStrategy(IAuthStrategy):
    """A strategy for apps with no authentication."""

    def create_listener_action(
        self, target_group: elbv2.IApplicationTargetGroup
    ) -> elbv2.ListenerAction:
        """The action is to simply forward traffic."""
        return elbv2.ListenerAction.forward([target_group])


class CognitoAuthStrategy(IAuthStrategy):
    """A strategy for apps using Cognito authentication."""

    def __init__(self, scope: Construct, app_config: AppConfig, app_name: str):
        super().__init__(scope, app_config, app_name)
        # Perform all Cognito-specific resource lookups and creation here.
        self._setup_cognito_resources()

    def _setup_cognito_resources(self):
        """Looks up and creates all necessary Cognito resources."""
        self.user_pool = cognito.UserPool.from_user_pool_id(
            self.scope, "ExistingUserPool", self.app_config.user_pool_id
        )

        self.user_pool_domain = cognito.UserPoolDomain.from_domain_name(
            self.scope,
            "ExistingCustomCognitoDomain",
            user_pool_domain_name=f"auth.{self.app_config.domain_name}",
        )

        alb_domain_name = f"{self.app_name}.{self.app_config.domain_name}"

        self.cognito_client = cognito.UserPoolClient(
            self.scope,
            "Client",
            user_pool=self.user_pool,
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
                callback_urls=[f"https://{alb_domain_name}/oauth2/idpresponse"],
                logout_urls=[f"https://{alb_domain_name}"],
            ),
        )

    def create_listener_action(
        self, target_group: elbv2.IApplicationTargetGroup
    ) -> elbv2.ListenerAction:
        """Returns the Cognito authentication action for the ALB listener."""
        return elbv2_actions.AuthenticateCognitoAction(
            user_pool=self.user_pool,
            user_pool_client=self.cognito_client,
            user_pool_domain=self.user_pool_domain,
            next=elbv2.ListenerAction.forward([target_group]),
        )

    def create_outputs(self) -> None:
        """Creates the Cognito Client ID CloudFormation output."""
        CfnOutput(
            self.scope,
            "CognitoClientId",
            value=self.cognito_client.user_pool_client_id,
            description=f"Cognito Client ID for {self.app_name}",
        )
