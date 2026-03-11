#!/bin/bash

# Configuration
PROJECT_DIR="/home/administrator/oasis"
SERVICE_NAME="oasis-bot.service"

echo "🚀 Starting deployment..."

cd $PROJECT_DIR

# Pull latest code (if using git)
# git pull origin main

# Update requirements
echo "📦 Updating dependencies..."
pip install -r requirements.txt

# Reload systemd and restart service
echo "🔄 Restarting service..."
sudo systemctl daemon-reload
sudo systemctl restart $SERVICE_NAME

echo "✅ Deployment finished successfully!"
