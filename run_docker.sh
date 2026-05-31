#!/bin/bash
set -e

echo "========================================="
echo "   Yuno AI Agent Orchestration Platform  "
echo "        Unified Docker Automation        "
echo "========================================="

# 1. Clean up old container
echo -e "\n[1/3] Cleaning up old container..."
if [ "$(docker ps -a -q -f name=yuno_app)" ]; then
    echo "Stopping and removing existing 'yuno_app' container..."
    docker stop yuno_app >/dev/null 2>&1 || true
    docker rm yuno_app >/dev/null 2>&1 || true
else
    echo "No existing container found."
fi

# 2. Build the unified Docker image
echo -e "\n[2/3] Building unified Docker image..."
docker build -t yuno-platform .

# 3. Start the newly built container
echo -e "\n[3/3] Starting Yuno AI Platform container on port 8000..."
docker run -d -p 8000:8000 --name yuno_app --env-file ./backend/.env yuno-platform:latest

echo -e "\n========================================="
echo "   Success! Yuno AI Platform is Active   "
echo "========================================="
echo "Visual Builder & Observability Dashboard: http://localhost:8000"
echo "========================================="
