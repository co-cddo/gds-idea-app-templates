#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import (
    Tags,
    aws_iam as iam,
)
from gds_idea_cdk_constructs import EnvConfig
from gds_idea_cdk_constructs.web_app import AuthType, WebApp, WebAppContainerProperties

# This is the name of your app, it should contain A-Za-z-_
# You app will be hosted at APP_NAME.gds-idea.click/io (depending on prod/env)
APP_NAME = "streamlit-test"

app = cdk.App()

cdk_env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"],
)

env_config = EnvConfig(cdk_env)


Tags.of(app).add("Environment", env_config.environment.friendly_name)
Tags.of(app).add("ManagedBy", "cdk")
Tags.of(app).add("Repository", "TBA")
Tags.of(app).add("AppName", APP_NAME)


stack = WebApp(
    app,
    env_config=env_config,
    app_name=APP_NAME,
    authentication=AuthType.COGNITO,
    docker_context_path=".",
    dockerfile_path="app_src/Dockerfile",
    container_props=WebAppContainerProperties(
        health_check_path="/_stcore/health",
        environment_variables={"COGNITO_AUTH_SECRET_NAME": f"{APP_NAME}/access"},
    ),
)

stack.task_role.add_to_policy(
    iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=[
            "secretsmanager:GetSecretValue",
        ],
        resources=[
            "arn:aws:secretsmanager:eu-west-2:992382722318:secret:streamlit-test/access-UKBGiP"
        ],
    )
)

app.synth()
