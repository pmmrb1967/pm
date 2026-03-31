#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

CONTAINER_NAME="kanban-studio"
IMAGE_NAME="kanban-studio"
PORT=8000

# Stop and remove any existing container with this name
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Removing existing container..."
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME"
fi

echo "Building image..."
docker build -t "$IMAGE_NAME" "$PROJECT_DIR"

echo "Starting container..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "${PORT}:8000" \
    --env-file "$PROJECT_DIR/.env" \
    "$IMAGE_NAME"

echo "Kanban Studio running at http://localhost:${PORT}"
