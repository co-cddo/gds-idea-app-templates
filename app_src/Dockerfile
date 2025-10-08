FROM python:3.13

WORKDIR /app

# Install system dependencies
RUN apt-get update \
 && apt-get install -y --no-install-recommends git openssh-client curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Add GitHub to known_hosts to avoid "Host key verification failed"
RUN mkdir -p -m 0700 ~/.ssh && ssh-keyscan github.com >> ~/.ssh/known_hosts

# Copy app dependency files
COPY app_src/pyproject.toml ./

# Sync dependencies using UV with SSH forwarding for private git dependencies
# Build with: DOCKER_BUILDKIT=1 docker build --ssh default -t dumper:latest -f app_src/Dockerfile .
# This creates a .venv with all dependencies
RUN --mount=type=ssh uv sync

# Copy application
COPY app_src/ .

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK CMD curl --fail http://localhost:80/_stcore/health || exit 1

# Run streamlit using uv
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", "--server.port", "80"]
