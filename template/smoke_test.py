#!/usr/bin/env python3
"""
Smoke Test Script - Validates that the PRODUCTION application builds and runs correctly.

This tests the production Docker image (secure, minimal, non-root) that will be
deployed to AWS ECS, not the development image used in VS Code dev containers.

Usage:
    uv run smoke_test           # Run health check then exit
    uv run smoke_test --wait    # Keep running until you press Enter
"""

import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

# Get repository root (parent of template/ directory)
REPO_ROOT = Path(__file__).parent.parent
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"
COMPOSE_FILE = ".devcontainer/docker-compose.yml"
SERVICE_NAME = "app"
CONTAINER_PORT = 8080
MAX_WAIT_SECONDS = 300
CHECK_INTERVAL_SECONDS = 2


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command."""
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def validate_configuration() -> str:
    """Load framework from config and return health check path."""
    print("---")
    print("🔍 Loading configuration from pyproject.toml...")

    # Read pyproject.toml
    with open(PYPROJECT_PATH, "rb") as f:
        config = tomllib.load(f)

    framework = config.get("tool", {}).get("webapp", {}).get("framework", "")

    if not framework:
        print("❌ ERROR: No framework configured in [tool.webapp]")
        print("💡 Fix: Run 'uv run configure <app-name> <framework>'")
        sys.exit(1)

    # Get health check path for framework
    health_paths = {
        "streamlit": "/_stcore/health",
        "dash": "/health",
        "fastapi": "/health",
    }
    health_path = health_paths.get(framework, "/health")

    print(f"✅ Framework: {framework}, Health check: {health_path}")
    return health_path


def cleanup():
    """Clean up Docker containers."""
    print()
    print("---")
    print("🧹 Cleaning up...")
    run_command(["docker-compose", "-f", COMPOSE_FILE, "down"], check=False)
    print("✅ Cleanup complete.")


def get_host_port() -> str:
    """Get the host port mapping for the container."""
    result = run_command(
        [
            "docker-compose",
            "-f",
            COMPOSE_FILE,
            "port",
            SERVICE_NAME,
            str(CONTAINER_PORT),
        ]
    )
    # Output format: "0.0.0.0:8080"
    return result.stdout.strip().split(":")[-1]


def check_health(url: str) -> bool:
    """Check if health endpoint responds successfully."""
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            return response.status == 200
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
        ConnectionError,
    ):
        return False


def main():
    wait_for_input = "--wait" in sys.argv
    import os

    try:
        # Validate configuration
        health_path = validate_configuration()

        # Set environment to build production target
        env = os.environ.copy()
        env["DOCKER_TARGET"] = "production"

        # Build production image using docker-compose
        print("---")
        print("🏗️  Building PRODUCTION Docker image (secure, non-root, minimal)...")
        print("   Note: Using docker-compose with DOCKER_TARGET=production")
        build_cmd = ["docker-compose", "-f", COMPOSE_FILE, "build"]
        subprocess.run(build_cmd, check=True, env=env)
        print("✅ Build complete")

        # Start container using docker-compose
        print("---")
        print("🚀 Starting production container with docker-compose...")
        up_cmd = ["docker-compose", "-f", COMPOSE_FILE, "up", "-d"]
        subprocess.run(up_cmd, check=True, env=env)
        print("✅ Container started")

        # Get port mapping
        print("---")
        print("🔍 Detecting port mapping...")
        host_port = get_host_port()
        health_url = f"http://localhost:{host_port}{health_path}"
        print(f"   Container port {CONTAINER_PORT} mapped to host port {host_port}")
        print(f"   Health check endpoint: {health_path}")

        # Wait for health check
        print("---")
        print(f"🩺 Performing health check at {health_url}")
        print(f"   Polling for up to {MAX_WAIT_SECONDS} seconds...")

        seconds_waited = 0
        while seconds_waited < MAX_WAIT_SECONDS:
            if check_health(health_url):
                print()  # Newline after dots
                print("✅ Health check PASSED! Production image is working correctly.")
                break

            print(".", end="", flush=True)
            time.sleep(CHECK_INTERVAL_SECONDS)
            seconds_waited += CHECK_INTERVAL_SECONDS
        else:
            print()  # Newline
            print("❌ Health check FAILED! The application did not respond in time.")
            print("---")
            print("🗒️  Showing container logs for debugging:")
            logs = run_command(
                ["docker-compose", "-f", COMPOSE_FILE, "logs"], check=False
            )
            print(logs.stdout)
            sys.exit(1)

        # Wait for user input if requested
        if wait_for_input:
            print("---")
            print(f"➡️  Production container is running on http://localhost:{host_port}")
            print(
                "   --wait flag detected. Press [ENTER] to stop the container and clean up."
            )
            input()

    finally:
        cleanup()


if __name__ == "__main__":
    main()
