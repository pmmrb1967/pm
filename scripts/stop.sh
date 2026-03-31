#!/usr/bin/env bash
set -e

CONTAINER_NAME="kanban-studio"

if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
    echo "Kanban Studio stopped."
else
    echo "No running container named '${CONTAINER_NAME}' found."
fi
