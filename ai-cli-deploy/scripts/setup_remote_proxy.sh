#!/bin/bash
set -e

PROXY_HOST="${1:-PROXY_SERVER_IP}"
PROXY_PORT="${2:-7890}"

echo "Configuring proxy via $PROXY_HOST:$PROXY_PORT"

# Test connectivity to proxy host
if ! ping -c 2 "$PROXY_HOST" > /dev/null 2>&1; then
  echo "✗ Cannot reach $PROXY_HOST. Check EasyTier connection."
  exit 1
fi

echo "✓ Connectivity to $PROXY_HOST verified"

# Test proxy service
if curl -x "http://$PROXY_HOST:$PROXY_PORT" -I https://www.google.com --connect-timeout 5 > /dev/null 2>&1; then
  echo "✓ Proxy service is working"
else
  echo "✗ Proxy service not responding on $PROXY_HOST:$PROXY_PORT"
  exit 1
fi

# Add proxy config to bashrc if not already present
if ! grep -q "export http_proxy=http://$PROXY_HOST:$PROXY_PORT" ~/.bashrc; then
  echo "" >> ~/.bashrc
  echo "# Proxy via KAIFU02 (added by intranet-network-deploy)" >> ~/.bashrc
  echo "export http_proxy=http://$PROXY_HOST:$PROXY_PORT" >> ~/.bashrc
  echo "export https_proxy=http://$PROXY_HOST:$PROXY_PORT" >> ~/.bashrc
  echo "export no_proxy=localhost,127.0.0.1,INTERNAL_NETWORK" >> ~/.bashrc
  echo "✓ Proxy configuration added to ~/.bashrc"
else
  echo "✓ Proxy configuration already exists in ~/.bashrc"
fi

# Stop local mihomo if running
if docker ps | grep -q mihomo; then
  echo "Stopping local mihomo container (not needed for remote proxy)..."
  docker stop mihomo
  docker rm mihomo
  echo "✓ Local mihomo removed"
fi

echo ""
echo "Proxy configuration complete!"
echo "Run 'source ~/.bashrc' to apply in current terminal"
