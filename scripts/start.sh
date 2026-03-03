#!/bin/bash

echo "Starting Document Similarity System..."

MODE=${DEPLOY_MODE:-demo}

if [ "$MODE" = "production" ]; then
  docker compose --profile prod up -d
else
  docker compose --profile demo up -d
fi
