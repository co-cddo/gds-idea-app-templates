# Dev Container Setup

This directory contains the configuration for VS Code dev containers, providing a consistent development environment for all team members.

## Quick Start

1. Install [VS Code](https://code.visualstudio.com/) and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open this repository in VS Code
3. Click "Reopen in Container" when prompted (or use Command Palette: `Dev Containers: Reopen in Container`)
4. Wait for the container to build (first time only)
5. Start your app (see "Starting Your App" section below)

## Configuration Files

### `docker-compose.yml` - RUNTIME CONFIGURATION ✅ EDIT THIS

**This is the source of truth for all runtime configuration.**

Modify this file to:
- Add environment variables for your app (`environment` section)
- Change port mappings (`ports` section)
- Add volume mounts (`volumes` section)

Example: Adding a new environment variable
```yaml
environment:
  - COGNITO_AUTH_DEV_MODE=true
  - COGNITO_AUTH_CONFIG_PATH=/app/dev_mocks/dev_mock_authoriser.json
  - MY_CUSTOM_VAR=my_value  # Add your own here
```

This file is used by both:
- VS Code dev containers (automatically)
- Smoke test script (`./smoke-test.sh`)

### `devcontainer.json` - VS CODE SETTINGS ⚙️ CUSTOMIZE AS NEEDED

**This file contains VS Code-specific configuration only.**

Modify this file to:
- Install additional VS Code extensions (`extensions` array)
- Change VS Code editor settings (`settings` object)

This file does NOT contain runtime config (env vars, ports) - those are in docker-compose.yml.

## How It Works

### Container Setup
- **Base**: Uses the production `app_src/Dockerfile` (identical to deployed version)
- **Working directory**: `/app` (mapped to `app_src/`)
- **Port**: App runs on port 80 inside container, accessible at http://localhost:8501
- **Startup**: See "Starting Your App" section above for framework-specific commands

### Volume Mounts
- `app_src/` → `/app` (your code, live editing enabled)
- `dev_mocks/` → `/app/dev_mocks` (mock authentication files)
- UV cache persisted across rebuilds

### Authentication in Dev Mode

#### Option 1: Mock Authentication (Recommended for Local Dev)
When `COGNITO_AUTH_DEV_MODE=true`, which is the default for local dev,  The app uses mock 
files from `dev_mocks/` instead of AWS Cognito:
- `dev_mock_authoriser.json` - Mock ALB/Cognito configuration
- `dev_mock_user.json` - Mock user session data

You can modify either to test if the auth is working as you'd expect. 

### AWS credentials
If your app needs to access AWS services during development, you can provide AWS credentials to the dev container using the `provide_role` script.

**Prerequisites:**
1. Configure your AWS profile (see "AWS Profile Configuration" below)
2. Authenticate with your AWS profile (GDS-users account)

**Two Modes:**

**Pass-through Mode** - Use your current dev/prod role credentials directly:
```bash
# From the host (NOT inside container)
export AWS_PROFILE=aws-prototype  # or your dev/prod profile
uv run provide_role
```

Use this when:
- You haven't created the container/task role yet (early development)
- You want to test with your dev/prod role permissions
- You're developing locally and don't need production-like isolation

**Role Assumption Mode** - Assume a specific container/task role:
```bash
# First, configure the role in pyproject.toml
# [tool.webapp.dev]
# aws_role_arn = "arn:aws:iam::ACCOUNT_ID:role/YourContainerRole"

# Then provide credentials
export AWS_PROFILE=aws-prototype
uv run provide_role
```

Use this when:
- Testing with production-like permissions (container role)
- The container/task role exists in AWS
- You want to verify your app works with the role it will use in production

**Force Pass-through Mode** (skip role even if configured):
```bash
export AWS_PROFILE=aws-prototype
uv run provide_role --use-profile
```

**AWS Profile Configuration:**

Edit `~/.aws/config`:
```ini
[profile aws-prototype]
role_arn = arn:aws:iam::ACCOUNT_ID:role/YourDevRole
source_profile = gds-users
mfa_serial = arn:aws:iam::ACCOUNT_ID:mfa/your-mfa-device
duration_seconds = 28800  # 8 hours
```

**How it works:**
- Credentials are written to `.aws-dev/` on the host
- This directory is mounted into the dev container at `/home/vscode/.aws/`
- Changes take effect immediately (no container restart needed)
- Re-run `uv run provide_role` whenever your credentials expire
- Do not referecnce profile_names in your app_src code. 

## Starting Your App

Once the dev container is running, open a terminal and use the appropriate command for your framework:

### Streamlit
```bash
uv run streamlit run streamlit_app.py --server.port 80
```
Then open http://localhost:8501

### Dash
```bash
uv run python dash_app.py
```
Then open http://localhost:8501

### FastAPI
```bash
uv run uvicorn fastapi_app:app --reload --host 0.0.0.0 --port 80
```
Then open http://localhost:8501

Your code is in `/app/<framework>_app.py` and changes auto-reload on save.

## Common Tasks

### Rebuild Container
If you update dependencies or the Dockerfile:
1. Command Palette: `Dev Containers: Rebuild Container`
2. Or restart VS Code and choose "Rebuild and Reopen in Container"

### View Logs
- Streamlit output appears in the terminal
- Or use Docker Desktop to view container logs

### Add Python Dependencies
1. Edit `app_src/pyproject.toml` dependencies section
2. Run `uv sync` in the terminal (or rebuild container)

### Troubleshooting

**Port 8501 already in use**: Stop any other services using that port, or change the port in `docker-compose.yml` (e.g., `"8502:80"`).

**Changes not reflected**: Most frameworks auto-reload on file changes. If not, refresh the browser or restart your app (see the startup instructions shown in your terminal)

## Architecture Notes

### Why Use Production Dockerfile?
The dev container uses the same Dockerfile as production deployments to ensure environment parity. This prevents "works on my machine" issues.

### Why Port 8501?
- Container runs your app on port 80 (same as production behind ALB)
- Port 8501 is mapped for local access (no sudo needed)
- This mimics the production setup where ALB listens on port 443/80

## Further Reading

- [VS Code Dev Containers documentation](https://code.visualstudio.com/docs/devcontainers/containers)
- [UV documentation](https://docs.astral.sh/uv/)
- Framework docs: [Streamlit](https://docs.streamlit.io/) | [Dash](https://dash.plotly.com/) | [FastAPI](https://fastapi.tiangolo.com/)
