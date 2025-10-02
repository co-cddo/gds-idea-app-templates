#!/bin/bash

# --- Configuration ---
IMAGE_NAME="my-dumper-app"
CONTAINER_NAME="dumper-test-container"
HOST_PORT=8501
CONTAINER_PORT=80
HEALTH_CHECK_URL="http://localhost:${HOST_PORT}/_stcore/health"
MAX_WAIT_SECONDS=300
CHECK_INTERVAL_SECONDS=2

# --- Argument Parsing ---
# Default behavior is to exit immediately after the health check.
# If the --wait flag is passed, this will be set to true.
WAIT_FOR_INPUT=false
if [ "$1" == "--wait" ]; then
  WAIT_FOR_INPUT=true
fi

# --- Cleanup Function ---
# This function runs when the script exits to ensure the container is stopped and removed.
cleanup() {
  echo
  echo "---"
  echo "🧹 Cleaning up test container..."
  docker stop ${CONTAINER_NAME} > /dev/null 2>&1
  docker rm ${CONTAINER_NAME} > /dev/null 2>&1
  echo "✅ Cleanup complete."
}

# Trap the script's exit signal to run the cleanup function automatically.
trap cleanup EXIT

# --- Main Script ---

# Stop on the first error
set -e

echo "---"
echo "🏗️  Building Docker image: ${IMAGE_NAME}"
docker build --platform linux/amd64 -f src/Dockerfile -t ${IMAGE_NAME} .

echo "---"
echo "🚀 Running container '${CONTAINER_NAME}' in the background..."
docker run -d -p ${HOST_PORT}:${CONTAINER_PORT} --name ${CONTAINER_NAME} ${IMAGE_NAME}

echo "---"
echo "🩺 Performing health check, polling for up to ${MAX_WAIT_SECONDS} seconds..."

SECONDS_WAITED=0
# Loop until the health check passes or the timeout is reached
until curl --fail -s -o /dev/null "${HEALTH_CHECK_URL}"; do
  if [ ${SECONDS_WAITED} -ge ${MAX_WAIT_SECONDS} ]; then
    echo # Newline for clean output
    echo "❌ Health check FAILED! The application did not respond in time."
    echo "---"
    echo "🗒️  Showing container logs for debugging:"
    docker logs ${CONTAINER_NAME}
    exit 1
  fi

  printf "." # Print a dot to show progress
  sleep ${CHECK_INTERVAL_SECONDS}
  SECONDS_WAITED=$((SECONDS_WAITED + CHECK_INTERVAL_SECONDS))
done

echo # Newline for clean output
echo "✅ Health check PASSED! The application is running correctly."

# If the --wait flag was passed, pause here until the user presses Enter.
if [ "$WAIT_FOR_INPUT" = true ]; then
  echo "---"
  echo "➡️  Container '${CONTAINER_NAME}' is running on http://localhost:${HOST_PORT}"
  echo "   --wait flag detected. Press [ENTER] to stop the container and clean up."
  read -r
fi

# The script exits here. The 'trap' will trigger the cleanup function.
exit 0