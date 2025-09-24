#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import Aspects
from cdk_nag import AwsSolutionsChecks, NagPackSuppression, NagSuppressions

# The import path correctly points into the 'dumper' directory
from dumper.dumper_stack import DumperStack

app = cdk.App()

env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"], region=os.environ["CDK_DEFAULT_REGION"]
)


stack = DumperStack(
    app,
    "DumperStack",
    app_name="dumper",
    domain_name="gds-idea.click",
    cloudfront_domain_name="d1cp3mv9sf5cdw.cloudfront.net",
    env=env,
)  # This name should match your stack class
# Apply checks
# Aspects.of(stack).add(AwsSolutionsChecks())

app.synth()
