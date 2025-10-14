#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import (
    Tags,
)
from gds_idea_cdk_constructs import AppConfig, DeploymentEnvironment
from gds_idea_cdk_constructs.web_app import AuthType, WebApp

app = cdk.App()

cdk_env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"],
)

app_config = AppConfig.from_pyproject()
dep_config = DeploymentEnvironment(cdk_env)

#
Tags.of(app).add("Environment", dep_config.environment.friendly_name)
Tags.of(app).add("ManagedBy", "cdk")
Tags.of(app).add("Repository", "TBA")
Tags.of(app).add("AppName", app_config.app_name)


stack = WebApp(
    app,
    deployment_config=dep_config,
    app_config=app_config,
    authentication=AuthType.COGNITO,
)

app.synth()
