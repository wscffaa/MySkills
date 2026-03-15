#!/bin/bash
set -e

NETWORK_NAME="${1:-default-network}"
NETWORK_SECRET="${2:-default-secret}"

echo "Deploying EasyTier with network: $NETWORK_NAME"

# Check if container already exists
if docker ps -a | grep -q easytier; then
  echo "EasyTier container already exists. Removing..."
  docker stop easytier 2>/dev/null || true
  docker rm easytier 2>/dev/null || true
fi

# Deploy EasyTier container
docker run -d \
  --name easytier \
  --restart unless-stopped \
  --network host \
  --cap-add NET_ADMIN \
  -v /dev/net/tun:/dev/net/tun \
  easytier/easytier:latest \
  easytier-core \
  --network-name "$NETWORK_NAME" \
  --network-secret "$NETWORK_SECRET" \
  --ipv4 NODE_IP

echo "EasyTier deployed successfully"
echo "Container restart policy: unless-stopped (auto-start on boot)"

# Wait for container to start
sleep 3

# Verify deployment
if docker ps | grep -q easytier; then
  echo "✓ EasyTier is running"
else
  echo "✗ EasyTier failed to start"
  exit 1
fi
