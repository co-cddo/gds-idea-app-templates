#!/bin/bash

# ============================================================================
# Smoke Test Script - Uses docker-compose for all configuration
# ============================================================================
# This script validates that the application builds and runs correctly.
# All configuration (ports, volumes, env vars) comes from:
#   .devcontainer/docker-compose.yml
#
# Usage:
#   ./smoke-test.sh          # Run health check then exit
#   ./smoke-test.sh --wait   # Keep running until you press Enter
# ============================================================================

# --- Configuration ---
COMPOSE_FILE=".devcontainer/docker-compose.yml"
SERVICE_NAME="app"
CONTAINER_PORT=80
MAX_WAIT_SECONDS=300
CHECK_INTERVAL_SECONDS=2

# --- Argument Parsing ---
WAIT_FOR_INPUT=false
if [ "$1" == "--wait" ]; then
  WAIT_FOR_INPUT=true
fi

# --- Cleanup Function ---
cleanup() {
  echo
  echo "---"
  echo "🧹 Cleaning up..."
  docker-compose -f ${COMPOSE_FILE} down > /dev/null 2>&1
  echo "✅ Cleanup complete."
}

trap cleanup EXIT

# --- Main Script ---
set -e

echo "---"
echo "🏗️  Building Docker image using docker-compose..."
docker-compose -f ${COMPOSE_FILE} build

echo "---"
echo "🚀 Starting container in the background..."
docker-compose -f ${COMPOSE_FILE} up -d

echo "---"
echo "🔍 Detecting port mapping from docker-compose.yml..."
HOST_PORT=$(docker-compose -f ${COMPOSE_FILE} port ${SERVICE_NAME} ${CONTAINER_PORT} | cut -d: -f2)
HEALTH_CHECK_URL="http://localhost:${HOST_PORT}/_stcore/health"
echo "   Container port ${CONTAINER_PORT} mapped to host port ${HOST_PORT}"

echo "---"
echo "🩺 Performing health check, polling for up to ${MAX_WAIT_SECONDS} seconds..."

SECONDS_WAITED=0
until curl --fail -s -o /dev/null "${HEALTH_CHECK_URL}"; do
  if [ ${SECONDS_WAITED} -ge ${MAX_WAIT_SECONDS} ]; then
    echo # Newline for clean output
    echo "❌ Health check FAILED! The application did not respond in time."
    echo "---"
    echo "🗒️  Showing container logs for debugging:"
    docker-compose -f ${COMPOSE_FILE} logs
    exit 1
  fi

  printf "."
  sleep ${CHECK_INTERVAL_SECONDS}
  SECONDS_WAITED=$((SECONDS_WAITED + CHECK_INTERVAL_SECONDS))
done

echo # Newline for clean output
echo "✅ Health check PASSED! The application is running correctly."

if [ "$WAIT_FOR_INPUT" = true ]; then
  echo "---"
  echo "➡️  Container is running on http://localhost:${HOST_PORT}"
  echo "   --wait flag detected. Press [ENTER] to stop the container and clean up."
  read -r
fi

exit 0