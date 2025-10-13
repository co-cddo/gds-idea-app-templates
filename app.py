#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import (
    Tags,
    aws_iam as iam,
)
from gds_idea_cdk_constructs.config import AppConfig, EnvConfig
from gds_idea_cdk_constructs.web_app import AuthType, WebApp

app = cdk.App()

cdk_env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"],
)

app_config = AppConfig.from_pyproject()
env_config = EnvConfig(cdk_env)


Tags.of(app).add("Environment", env_config.environment.friendly_name)
Tags.of(app).add("ManagedBy", "cdk")
Tags.of(app).add("Repository", "TBA")
Tags.of(app).add("AppName", app_config.app_name)


stack = WebApp(
    app,
    env_config=env_config,
    app_config=app_config,
    authentication=AuthType.COGNITO,
)

# Allow developers to assume TaskRole for local dev container testing
# Only allow roles ending with -poweraccess or -admin from testing account
# This enables 'uv run provide-role' to work from assumed dev/admin roles
DEV_TESTING_ACCOUNT = "588077357019"  # Your testing account ID

if env_config.environment.name in ["test", "dev"]:  # Not in production
    stack.task_role.assume_role_policy.add_statements(
        iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            principals=[iam.AccountPrincipal(DEV_TESTING_ACCOUNT)],
            actions=["sts:AssumeRole"],
            conditions={
                "StringLike": {
                    "aws:PrincipalArn": [
                        f"arn:aws:iam::{DEV_TESTING_ACCOUNT}:role/*-poweraccess",
                        f"arn:aws:iam::{DEV_TESTING_ACCOUNT}:role/*-admin",
                    ]
                }
            },
        )
    )

app.synth()
