# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**This is a template repository** for data scientists to learn how to deploy web applications to AWS with authentication. It demonstrates deploying Streamlit, Dash, or FastAPI applications with AWS Cognito authentication behind an Application Load Balancer.

The project showcases two custom libraries:
- **`gds-idea-cdk-constructs`**: Custom CDK constructs that simplify deploying web apps with ALB + Cognito
- **`cognito-auth`**: Authentication helpers for Streamlit and FastAPI that extract user info from ALB headers

Data scientists can use this as a starting point by:
1. Copying the repository structure
2. Choosing one of the example applications (Streamlit, Dash, or FastAPI)
3. Modifying `app.py` to configure their deployment
4. Customizing the application code in `src/`

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

### Docker Testing

```bash
# Build and run smoke test (exits after health check)
./smoke-test.sh

# Build and run with interactive wait (press Enter to stop)
./smoke-test.sh --wait

# Manual Docker build (requires SSH agent for private Git dependencies)
DOCKER_BUILDKIT=1 docker build --ssh default -t dumper:latest -f src/Dockerfile .

# Run container locally
docker run -d -p 8501:80 --name dumper-container dumper:latest
```

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

- **WebApp Construct**: Creates an ECS Fargate service behind an ALB with Cognito authentication
- **Authentication**: Uses `AuthType.COGNITO` for AWS Cognito User Pool integration
- **Container**: Runs on port 80, health check at `/_stcore/health` (Streamlit endpoint)
- **Environment**: Configured via `EnvConfig` which reads from CDK environment variables

### Application Code (src/)

The repository contains multiple web application implementations:

1. **streamlit_app.py** (Currently deployed)
   - Streamlit application with Cognito authentication
   - Uses `cognito-auth` library with `StreamlitAuth` helper
   - Displays user information and JWT claims from ALB headers
   - Authorization based on groups (`gds-idea`) or specific email addresses

2. **dash_app.py** (Alternative)
   - Dash/Plotly application
   - Uses `cognito_user` library with Dash helpers
   - Decorator-based authentication with domain restrictions

3. **dumper_app.py** (Debugging tool)
   - FastAPI application that displays all ALB headers
   - Useful for debugging authentication and JWT token flow
   - Decodes and displays OIDC data and access tokens

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

- `app.py` - CDK infrastructure definition
- `src/Dockerfile` - Multi-stage Docker build with SSH key forwarding
- `src/streamlit_app.py` - Main Streamlit application
- `src/idea_auth.py` - Token decoding utilities and OAuth2 helpers
- `smoke-test.sh` - Local Docker testing script
- `cdk.json` - CDK configuration and feature flags

## Important Notes

- The Dockerfile uses BuildKit's SSH forwarding to install private Git dependencies at build time
- Always use `DOCKER_BUILDKIT=1 docker build --ssh default` when building locally
- The health check endpoint is `/_stcore/health` (Streamlit-specific)
- Container runs on port 80 internally, typically mapped to 8501 for local testing
- Authentication requires valid Cognito tokens in ALB headers - local testing without ALB will not have authentication
