# Web App Template with AWS Cognito Authentication

A template repository for deploying Streamlit, Dash, or FastAPI applications to AWS ECS with Cognito authentication behind an Application Load Balancer.

## Features

- 🚀 **Multi-framework support**: Choose between Streamlit, Dash, or FastAPI
- 🔐 **Built-in authentication**: AWS Cognito integration with ALB
- 🐳 **Docker-based deployment**: ECS Fargate with auto-scaling
- 📦 **Infrastructure as Code**: AWS CDK for reproducible deployments
- 🛠️ **Dev container ready**: VS Code dev containers for instant development environment
- ✅ **Smoke testing**: Validate builds and health checks before deployment

## Quick Start

### Prerequisites

- [UV](https://docs.astral.sh/uv/) - Modern Python package manager
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- [Docker](https://www.docker.com/) (optional, for local testing)
- [VS Code](https://code.visualstudio.com/) with Dev Containers extension (recommended)

### 1. Clone and Install

```bash
git clone <this-repo>
cd <repo-name>
uv sync
```

### 2. Configure Your App

Choose your app name and framework:

```bash
# Set app name and framework (streamlit, dash, or fastapi)
uv run configure my-app streamlit

# This updates pyproject.toml and copies framework files to app_src/
```

Or edit `pyproject.toml` manually:

```toml
[tool.webapp]
app_name = "my-app"
framework = "streamlit"  # or "dash" or "fastapi"
```

Then sync:

```bash
uv run configure
```

### 3. Develop

**Option A: VS Code Dev Container (Recommended)**

1. Open in VS Code
2. Click "Reopen in Container" when prompted
3. Dependencies auto-install, dev environment ready
4. Run your app inside the container

**Option B: Smoke Test**

```bash
# Build and test with Docker
uv run smoke_test --wait

# Then open http://localhost:8501
```

### 4. Deploy to AWS

```bash
# Set AWS environment
export CDK_DEFAULT_ACCOUNT=123456789012
export CDK_DEFAULT_REGION=eu-west-2

# Deploy
cdk deploy
```

## Project Structure

```
.
├── app.py                      # CDK infrastructure definition
├── pyproject.toml              # Project config (includes [tool.webapp])
├── cdk.json                    # CDK configuration
│
├── template/                   # Template tooling
│   ├── configure.py            # Configuration script
│   ├── smoke_test.py           # Docker smoke test
│   └── frameworks/             # Framework templates
│       ├── streamlit/
│       ├── dash/
│       └── fastapi/
│
├── app_src/                    # Active application (generated)
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── <framework>_app.py
│
└── .devcontainer/              # VS Code dev container config
    └── docker-compose.yml
```

## Available Commands

### Template Configuration

```bash
# Configure with CLI arguments
uv run configure <app-name> <framework>

# Sync from pyproject.toml (after manual edit)
uv run configure
```

### Testing

```bash
# Smoke test (quick validation)
uv run smoke_test

# Smoke test with interactive wait
uv run smoke_test --wait
```

### CDK Commands

```bash
# Synthesize CloudFormation template
cdk synth

# List stacks
cdk ls

# Compare with deployed stack
cdk diff

# Deploy
cdk deploy

# Destroy
cdk destroy
```

## Frameworks

### Streamlit

- Built-in health endpoint: `/_stcore/health`
- Uses `StreamlitAuth` helper from `cognito-auth` library
- Simple, Pythonic UI development

### Dash

- Custom health endpoint: `/health`
- Uses `DashAuth` helper from `cognito-auth` library
- Plotly-based dashboards with callback architecture

### FastAPI

- Custom health endpoint: `/health`
- Uses `FastAPIAuth` middleware from `cognito-auth` library
- High-performance async API framework

## Architecture

The infrastructure uses custom CDK constructs from `gds-idea-cdk-constructs`:

- **Application Load Balancer** with Cognito authentication
- **ECS Fargate** for container orchestration
- **Auto-scaling** based on CPU/memory
- **CloudWatch** logging and monitoring

Configuration is managed through `pyproject.toml`:

```python
# app.py
app_config = AppConfig.from_pyproject()
deployment_config = DeploymentConfig(cdk_env)

stack = WebApp(
    app,
    deployment_config=deployment_config,
    app_config=app_config,
    authentication=AuthType.COGNITO,
)
```

## Authentication

The ALB injects Cognito authentication headers:

- `x-amzn-oidc-data`: JWT with user claims (email, username, etc.)
- `x-amzn-oidc-accesstoken`: Cognito access token with groups

Applications use the `cognito-auth` library to extract and validate these headers.

## Development Workflow

1. **Configure**: `uv run configure my-app streamlit`
2. **Develop**: Open in VS Code dev container or run `uv run smoke_test --wait`
3. **Customize**: Edit `app_src/<framework>_app.py`
4. **Test**: Smoke test validates build and health checks
5. **Deploy**: `cdk deploy` to AWS
6. **Iterate**: Switch frameworks anytime with `uv run configure`

## AWS Authentication for Dev Container (Optional)

If your application needs AWS access during development (e.g., to access S3, DynamoDB, etc.), you can provide AWS credentials to the dev container.

### Understanding the Two-Role Model

There are **two different AWS roles** in this project:

1. **Deployment Role** - Your personal AWS role used to run `cdk deploy` (you already have this)
2. **Runtime Role** - The role your application needs when running in the container (what `provide-role` sets up)

### Setup

1. **Configure the runtime role** in `pyproject.toml`:

```toml
[tool.webapp.dev]
aws_role_arn = "arn:aws:iam::123456789012:role/AppRuntimeRole"
aws_region = "eu-west-2"  # Optional, defaults to eu-west-2
```

2. **Provide credentials to the container** (run on your HOST machine):

```bash
# Interactive - prompts for MFA code
uv run provide-role

# Non-interactive
uv run provide-role --mfa-code 123456

# Custom duration (1 hour instead of default 12 hours)
uv run provide-role --mfa-code 123456 --duration 3600
```

3. **Credentials are immediately available** in the dev container (no restart needed!)

```bash
# Inside dev container
aws sts get-caller-identity
# Your app now has AWS access
```

### How It Works

- MFA device is auto-detected from your AWS configuration
- Temporary credentials are written to `.aws-dev/` on your host (gitignored)
- This directory is mounted into the container at `/home/vscode/.aws/`
- AWS SDK/CLI automatically uses these credentials
- Credentials expire after 12 hours by default
- To refresh: just re-run `uv run provide-role` on your host

### Notes

- ⚠️ This is **optional** - only needed if your app requires AWS access during development
- ✅ Credentials update **live** - no container restart needed
- ✅ Completely separate from CDK deployment credentials
- ✅ Standard AWS credentials format (`[default]` profile)

## Switching Frameworks

```bash
# Switch to FastAPI
uv run configure my-app fastapi

# Or edit pyproject.toml and sync
uv run configure
```

This updates the configuration and copies new framework files to `app_src/`.

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
