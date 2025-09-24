#!/bin/bash

# --- Configuration ---
IMAGE_NAME="my-dumper-app"
CONTAINER_NAME="dumper-test-container"
HOST_PORT=8080
CONTAINER_PORT=80
HEALTH_CHECK_URL="http://localhost:${HOST_PORT}/"
STARTUP_WAIT_SECONDS=10 # How long to wait for the app to start

# --- Cleanup Function ---
# This function will run when the script exits, ensuring the container is stopped.
cleanup() {
  echo "---"
  echo "🧹 Cleaning up test container..."
  docker stop ${CONTAINER_NAME} > /dev/null 2>&1
  docker rm ${CONTAINER_NAME} > /dev/null 2>&1
  echo "✅ Cleanup complete."
}

# Trap the script's exit signal to run the cleanup function automatically
trap cleanup EXIT

# --- Main Script ---

echo "---"
echo "🏗️  Building Docker image: ${IMAGE_NAME}"
# Stop on first error
set -e
docker build --platform linux/amd64 -f src/Dockerfile -t ${IMAGE_NAME} .

echo "---"
echo "🚀 Running container '${CONTAINER_NAME}' in the background..."
docker run -d -p ${HOST_PORT}:${CONTAINER_PORT} --name ${CONTAINER_NAME} ${IMAGE_NAME}

echo "---"
echo "⏳ Waiting ${STARTUP_WAIT_SECONDS} seconds for the application to start..."
sleep ${STARTUP_WAIT_SECONDS}

echo "---"
echo "🩺 Performing health check on ${HEALTH_CHECK_URL}..."

# Use curl to check the HTTP status. The --fail flag causes curl to exit with an error
# if the HTTP code is not 2xx.
if curl --fail -s ${HEALTH_CHECK_URL} > /dev/null; then
  echo "✅ Health check PASSED! The application is running correctly."
  exit 0
else
  echo "❌ Health check FAILED! The application did not respond correctly."
  echo "---"
  echo "🗒️  Showing container logs for debugging:"
  docker logs ${CONTAINER_NAME}
  exit 1
fi