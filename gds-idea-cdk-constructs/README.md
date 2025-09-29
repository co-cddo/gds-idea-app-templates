# gds-idea-cdk-constructs 

A repo for commonly used constructs in the team. 

## WebApp

This simplified the deployment of containerised applications in the gds-idea infrastructure.

## Features

* **Deploy any containerized web app** from a local Dockerfile.
* **Automated infrastructure** setup including ECS Fargate, Application Load Balancer, VPC integration, and DNS route creationg
* **Built-in authentication patterns** (`AuthType.COGNITO` or `AuthType.NONE`).
* **Configurable** container resources (CPU, memory, environment variables).
* **Secure by default** with support for custom IAM task roles.
* **Environment-aware configuration** for deploying to different AWS accounts (e.g., DEV, PROD).



## Prerequisites

Before using this library, you need to have the following:
1.  An AWS account with credentials configured for your environment.
2.  **AWS CDK v2** installed and bootstrapped in your target account and region.
3.  **Docker** installed and running on your local machine.
4.  An existing AWS infrastructure that includes:
    * A VPC
    * A Route 53 parent hosted zone
    * An S3 bucket for access logs
    * (For Cognito auth) An AWS Cognito User Pool and Domain

This library's `EnvConfig` class is designed to look up these existing resources.


## Installation

Install the library using pip:

```bash
pip install gds-idea-cdk-constructs
```

***

## Usage

All constructs are designed to be used within a standard AWS CDK application.

### 1. Initial Setup

In your CDK app's stack file (e.g., `app.py`), start by setting up the environment configuration. The `EnvConfig` class automatically selects the right settings based on the AWS account ID.

```python
# app.py
import os
import aws_cdk as cdk
from constructs import Construct

from gds_idea_cdk_constructs import EnvConfig
from gds_idea_cdk_constructs.web_app import AuthType, WebApp, 

# 1. Define your CDK app and environment
app = cdk.App()

# If you have correctly exported your AWS_PROFILE in the terminal this will look up the correct values.
cdk_env = cdk.Environment(
    account=os.environ["CDK_DEFAULT_ACCOUNT"],
    region=os.environ["CDK_DEFAULT_REGION"],
)

# 2. Instantiate the environment-specific configuration - this looks up the correct arns for the existing infrastructure.
env_config = EnvConfig(cdk_env=cdk_env)

# 3. Instantiate the stack
stack = WebApp(
    app,
    env_config=env_config,
    app_name="example",
    authentication=AuthType.COGNITO,  # Use our standard cognito authentication
    docker_context_path=".",
    dockerfile_path="src/Dockerfile", # Path to your dockerfile
)


app.synth()

```

### 2. Example: Public App with No Authentication

To deploy an application that is publicly accessible, simply set the `authentication` property to `AuthType.NONE`.

```python
# Deploys a publicly accessible container
public_app = WebApp(
    self,
    env_config=env_config,
    app_name="public-app",
    authentication=AuthType.NONE, # <-- Set authentication type
)
```

### 3. Advanced Usage

This example shows how to customize the container's resources, provide environment variables, and attach a custom IAM role for the application.

```python
# Inside the MyWebAppStacks class
import aws_cdk.aws_iam as iam

# 1. Define custom container properties
advanced_container_props = WebAppContainerProperties(
    cpu=512,  # 0.5 vCPU
    memory_limit_mib=1024,  # 1 GB
    desired_count=2,
    health_check_path="/health",
    environment_variables={
        "DATABASE_URL": "your-db-url-from-secrets-manager",
        "LOG_LEVEL": "INFO",
    },
)

# 2. Define a custom IAM role for the container task
custom_task_role = iam.Role(
    self, "MyWebAppTaskRole",
    assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
    description="Role for my-app to access an S3 bucket"
)

# 3. Grant permissions to the role
custom_task_role.add_to_policy(
    iam.PolicyStatement(
        actions=["s3:GetObject"],
        resources=["arn:aws:s3:::my-important-bucket/*"]
    )
)

# 4. Create the WebApp with the advanced configuration
advanced_app = WebApp(
    self,
    env_config=env_config,
    app_name="advanced-app",
    docker_context_path="./path/to/your/app/advanced",
    container_props=advanced_container_props, # <-- Pass custom props
    task_role=custom_task_role, # <-- Pass custom role
)
```

***

