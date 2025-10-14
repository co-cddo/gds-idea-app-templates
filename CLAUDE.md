# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**This is a template repository** for data scientists to learn how to deploy web applications to AWS with authentication. It demonstrates deploying Streamlit, Dash, or FastAPI applications with AWS Cognito authentication behind an Application Load Balancer.

The project showcases two custom libraries:
- **`gds-idea-cdk-constructs`**: Custom CDK constructs that simplify deploying web apps with ALB + Cognito
- **`cognito-auth`**: Authentication helpers for Streamlit and FastAPI that extract user info from ALB headers

Data scientists can use this as a starting point by:
1. Cloning the repository
2. Running `uv run configure <app-name> <framework>` to configure their app (streamlit, dash, or fastapi)
3. Developing in VS Code dev container (recommended) or testing with `uv run smoke_test --wait`
4. Customizing the application code in `app_src/`
5. Deploying with `cdk deploy`

## Development Commands

### Option 1: Dev Container (Recommended)

The easiest way to get started is using VS Code dev containers:

1. Install VS Code and the "Dev Containers" extension
2. Open this folder in VS Code
3. Click "Reopen in Container" when prompted (or use Command Palette: "Dev Containers: Reopen in Container")
4. Wait for container to build (first time only)
5. Dependencies are automatically installed via `uv sync`

**What's included:**
- Python 3.13 with UV pre-installed
- Git and GitHub CLI
- SSH agent forwarding for private repo access
- Auto-configured with dev mock auth files
- Port 8501 forwarded for Streamlit
- Python extensions and Ruff formatter

**Running the app in dev container:**
```bash
cd app_src
uv run streamlit run streamlit_app.py
```
Then open http://localhost:8501

### Option 2: Local Environment with UV

```bash
# Install UV (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync dependencies
uv sync                    # Install CDK dependencies
cd app_src && uv sync      # Install app dependencies

# Run Streamlit locally
cd app_src
uv run streamlit run streamlit_app.py
```

### CDK Commands

```bash
# Synthesize CloudFormation template
cdk synth

# List all stacks
cdk ls

# Compare deployed stack with current state
cdk diff

# Deploy to AWS
cdk deploy

# Set AWS environment variables if needed
export CDK_DEFAULT_ACCOUNT=123456789012
export CDK_DEFAULT_REGION=eu-west-2
```

### Template Configuration

```bash
# Configure app name and framework (updates pyproject.toml and copies framework files)
uv run configure <app-name> <framework>
uv run configure my-app streamlit

# Or edit pyproject.toml [tool.webapp] manually and sync:
uv run configure
```

### Docker Testing (Smoke Test)

```bash
# Build and run smoke test (exits after health check)
uv run smoke_test

# Build and run with interactive wait (press Enter to stop)
uv run smoke_test --wait
```

The smoke test validates your configuration and builds/tests the Docker container using docker-compose.

### AWS Role Provision for Dev Container (Optional)

If the application needs AWS access during development, you can provide AWS role credentials to the dev container:

```bash
# Interactive - prompts for MFA code (runs on HOST)
uv run provide-role

# Non-interactive with MFA code
uv run provide-role --mfa-code 123456

# Custom duration (1 hour instead of default 12 hours)
uv run provide-role --duration 3600
```

**How it works:**
- Runs on the **host machine** (not in container)
- Uses `aws sts assume-role` with MFA (auto-detected MFA serial)
- Writes temporary credentials to `.aws-dev/credentials` in standard AWS format
- This directory is mounted into the container at `/home/vscode/.aws/`
- Credentials update **live** (no container restart needed)
- Default duration: 12 hours (43200 seconds)

**Configuration in `pyproject.toml`:**
```toml
[tool.webapp.dev]
aws_role_arn = "arn:aws:iam::123456789012:role/AppRuntimeRole"
aws_region = "eu-west-2"  # Optional
```

**Important:** This is for the **runtime role** that your app needs, NOT the deployment role you use for `cdk deploy`. These are two separate roles.

### Testing

```bash
# Run tests
pytest

# Run tests with verbose output
pytest -v
```

## Architecture

### CDK Infrastructure (app.py)

The main CDK app (`app.py`) defines the infrastructure using the `WebApp` construct from `gds-idea-cdk-constructs`:

- **AppConfig**: Reads configuration from `pyproject.toml [tool.webapp]` (app name, framework)
- **WebApp Construct**: Creates an ECS Fargate service behind an ALB with Cognito authentication
- **Authentication**: Uses `AuthType.COGNITO` for AWS Cognito User Pool integration
- **Health Check**: Auto-detected based on framework (streamlit: `/_stcore/health`, dash/fastapi: `/health`)
- **Environment**: Configured via `DeploymentConfig` which reads from CDK environment variables

The simplified infrastructure:
```python
app_config = AppConfig.from_pyproject()
deployment_config = DeploymentConfig(cdk_env)

stack = WebApp(
    app,
    deployment_config=deployment_config,
    app_config=app_config,
    authentication=AuthType.COGNITO,
)
```

### Application Code (app_src/)

The `app_src/` directory contains the active web application. Framework files are copied from `template/frameworks/` when you run `uv run configure`.

Available framework templates:

1. **streamlit_app.py** (Streamlit)
   - Streamlit application with Cognito authentication
   - Uses `cognito-auth` library with `StreamlitAuth` helper
   - Displays user information and JWT claims from ALB headers
   - Authorization based on groups or specific email addresses

2. **dash_app.py** (Dash)
   - Dash/Plotly application with Flask backend
   - Uses `cognito-auth` library with `DashAuth` helper
   - Callback-based authentication to avoid Flask context issues
   - Custom `/health` endpoint

3. **fastapi_app.py** (FastAPI)
   - FastAPI application with app-wide authentication middleware
   - Uses `cognito-auth` library with `FastAPIAuth` helper
   - All routes protected by default
   - Custom `/health` endpoint

### Authentication Flow

The ALB with Cognito authentication injects headers:
- `x-amzn-oidc-data`: JWT containing user OIDC claims (email, username, etc.)
- `x-amzn-oidc-accesstoken`: Cognito access token with groups

Application code extracts these headers to:
1. Verify user authentication
2. Check authorization (groups, email domains)
3. Display user information

### Private Dependencies

The application depends on private GitHub repositories:
- `cognito-auth` (from `gds-idea-app-auth`) - Streamlit/FastAPI auth helpers
- `gds-idea-cdk-constructs` - Custom CDK constructs for ALB + Cognito setup

Both are installed via SSH (`git+ssh://git@github.com/...`) and require:
- SSH keys configured for GitHub access
- Docker BuildKit with SSH forwarding (`--ssh default`) for container builds

## Key Files

### Root Level
- `app.py` - CDK infrastructure definition (reads from pyproject.toml)
- `pyproject.toml` - Project configuration including `[tool.webapp]` for app name and framework
- `cdk.json` - CDK configuration and feature flags

### Template Directory
- `template/configure.py` - Configuration script to set app name and framework (run via `uv run configure`)
- `template/smoke_test.py` - Docker build and health check validation (run via `uv run smoke_test`)
- `template/provide_role.py` - AWS role provision script with MFA support (run via `uv run provide-role`)
- `template/frameworks/` - Framework template files (streamlit, dash, fastapi)
  - Each contains: Dockerfile, pyproject.toml, and framework-specific app.py

### AWS Dev Credentials
- `.aws-dev/` - Temporary AWS credentials for dev container (gitignored)
  - Generated by `uv run provide-role`
  - Mounted into container at `/home/vscode/.aws/`
  - Contains `credentials` and `config` files in standard AWS format

### Application
- `app_src/` - Active web application (populated by configure script)
  - Contains the selected framework's files
  - Dockerfile, pyproject.toml, and app file

## Important Notes

- **Configuration**: App name and framework are stored in `pyproject.toml [tool.webapp]` as the single source of truth
- **Framework Switching**: Run `uv run configure <app-name> <framework>` to switch frameworks - it updates config and copies the correct files to `app_src/`
- **Health Check Paths**: Auto-detected by framework (Streamlit: `/_stcore/health`, Dash/FastAPI: `/health`)
- **AWS Credentials**: Optional - use `uv run provide-role` on host to provide AWS access to dev container (MFA required, updates live)
- **Two-Role Model**: Deployment role (for `cdk deploy`) vs runtime role (for app in container) - these are separate
- **Docker**: The Dockerfile uses BuildKit's SSH forwarding to install private Git dependencies at build time
- **Dev Workflow**: Prefer VS Code dev containers for development, or use `uv run smoke_test --wait` for quick testing
- **Container**: Runs on port 80 internally, mapped to 8501 for local testing
- **Authentication**: Requires valid Cognito tokens in ALB headers - local testing without ALB will not have authentication
