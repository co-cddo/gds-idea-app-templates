FROM python:3.13

WORKDIR /app

# Install system dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends git curl ca-certificates sudo \
 && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root vscode user for dev container compatibility
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Copy app dependency files
COPY app_src/pyproject.toml ./

# Sync dependencies using UV (public HTTPS repos, no SSH needed)
RUN uv sync

# Copy application code
COPY app_src/ .

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK CMD curl --fail http://localhost:80/_stcore/health || exit 1

# Run streamlit using uv (production mode)
# Production flags:
#   --server.port=80: Listen on container port 80
#   --server.address=0.0.0.0: Listen on all interfaces
#   --server.headless=true: Don't try to open browser
#   --server.enableCORS=false: Disable CORS (behind ALB)
#   --browser.gatherUsageStats=false: Disable telemetry
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", \
     "--server.port", "80", \
     "--server.address", "0.0.0.0", \
     "--server.headless", "true", \
     "--server.enableCORS", "false", \
     "--browser.gatherUsageStats", "false"]
