#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Tags
from gds_idea_cdk_constructs import EnvConfig
from gds_idea_cdk_constructs.web_app import AuthType, WebApp

app = cdk.App()


Tags.of(app).add("Environment", "development")
Tags.of(app).add("ManagedBy", "cdk")
Tags.of(app).add("repo", "TBA")

cdk_env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"],
)

env_config = EnvConfig(cdk_env)

stack = WebApp(
    app,
    env_config=env_config,
    app_name="dumper",
    authentication=AuthType.COGNITO,
    docker_context_path=".",
    dockerfile_path="src/Dockerfile",
)


app.synth()
