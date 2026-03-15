---
name: intranet-network-deploy
description: Deploy EasyTier P2P network, mihomo TUN mode proxy, and AI CLI tools for intranet machines. Use when you need to (1) Set up EasyTier mesh network with Docker, (2) Deploy mihomo with TUN mode for transparent proxying (solves Antigravity AI chat issues), (3) Install AI CLI tools (Claude Code, Codex, Gemini CLI) with auto-updates, (4) Configure hapi for remote access, (5) Sync configuration files, (6) Set up auto-start on boot for all services. TUN mode is the recommended solution for Go programs that bypass HTTP_PROXY environment variables.
---

# Intranet Network Deploy

Complete deployment solution for intranet machines: EasyTier P2P network, mihomo TUN mode proxy (transparent proxying), AI CLI tools, and hapi with auto-start configuration.

## Quick Start

```bash
# Full deployment (EasyTier + mihomo TUN mode + AI CLI tools)
bash scripts/deploy.sh

# Deploy EasyTier only
bash scripts/deploy_easytier.sh <network-name> <network-secret>

# Deploy mihomo with TUN mode (recommended)
bash scripts/deploy_mihomo_local.sh

# Configure proxy via KAIFU02 (alternative)
bash scripts/setup_remote_proxy.sh PROXY_SERVER_IP 7890

# Install AI CLI tools only
bash scripts/install_cli_tools.sh

# Setup hapi
bash scripts/setup_hapi.sh
```

## Components

### 1. EasyTier P2P Network

Deploy EasyTier as Docker container with auto-restart:

```bash
bash scripts/deploy_easytier.sh <network-name> <network-secret>
```

- Creates Docker container with `unless-stopped` restart policy
- Configures P2P mesh network
- Auto-starts on system boot

### 2. Mihomo Proxy (TUN Mode)

**Recommended: Local TUN mode** (transparent proxying):
```bash
bash scripts/deploy_mihomo_local.sh
```

TUN mode features:
- Transparent proxying at network layer (no environment variables needed)
- Uses gvisor stack for userspace networking
- DNS hijacking with fake-ip mode for optimal performance
- Solves Go programs bypassing HTTP_PROXY (e.g., Antigravity language_server)
- Auto-route and auto-detect-interface for seamless integration

**Alternative: Remote mode via KAIFU02** (requires proxy environment variables):
```bash
bash scripts/setup_remote_proxy.sh PROXY_SERVER_IP 7890
```

Note: TUN mode is superior for intranet scenarios as it handles all TCP/UDP traffic transparently without application-level configuration.

### 3. AI CLI Tools

Install Claude Code, Codex, and Gemini CLI:

```bash
bash scripts/install_cli_tools.sh
```

Installs:
- `@anthropic-ai/claude-code@latest`
- `@openai/codex@latest`
- `@google/gemini-cli@latest`

**Auto-update cron job**:
```bash
bash scripts/setup_cron.sh "0,12"  # Update at 00:00 and 12:00 daily
```

### 4. Hapi (Optional)

Install hapi for remote access:

```bash
bash scripts/setup_hapi.sh [custom-domain]
```

- Local hub setup
- Cloudflared tunnel support
- Custom domain configuration

### 5. Antigravity AI Chat Fix

**Solution: mihomo TUN mode** (deployed in step 2)

TUN mode solves Antigravity connection issues:
- Antigravity's Go-based `language_server_linux_x64` bypasses HTTP_PROXY environment variables
- TUN mode intercepts all TCP connections at network layer (transparent proxying)
- No application-level configuration needed
- No wrapper scripts or LD_PRELOAD hacks required

**Verification**:
```bash
# 1. Check mihomo TUN interface
ip addr show Meta

# 2. Check DNS hijacking
ss -tulnp | grep :1053

# 3. Test connection (should work without proxy env vars)
unset http_proxy https_proxy
curl -I https://www.google.com

# 4. Monitor mihomo logs
docker logs -f mihomo
```

**Important**: Comment out proxy environment variables in `~/.bashrc` to avoid conflicts with TUN mode:
```bash
# Proxy via KAIFU02 (TUN mode enabled on remote)
# Temporarily disabled - using local mihomo TUN mode
#export http_proxy=http://PROXY_SERVER_IP:7890
#export https_proxy=http://PROXY_SERVER_IP:7890
#export no_proxy=localhost,127.0.0.1,INTERNAL_NETWORK
```

### 6. Configuration Files

Sync configuration files:

```bash
# Copy mihomo config to standard location
cp assets/mihomo/config.yaml ~/.config/mihomo/

# Sync EasyTier config
cp assets/easytier/config.json /path/to/easytier/
```

## Verification

Test connectivity:

```bash
# Check EasyTier peers
easytier-cli peer

# Check EasyTier routes
easytier-cli route

# Test mihomo TUN mode (no proxy env vars needed)
unset http_proxy https_proxy
curl -I https://www.google.com
curl -I https://github.com

# Check TUN interface
ip addr show Meta

# Check DNS hijacking
ss -tulnp | grep :1053

# Monitor mihomo traffic
docker logs -f mihomo

# Check AI CLI tools
claude-code --version
codex --version
gemini-cli --version

# Check hapi status
hapi status
```

## Auto-Start Configuration

All services are configured for auto-start:

- **EasyTier**: Docker restart policy `unless-stopped`
- **Mihomo**: Docker restart policy `unless-stopped` with TUN mode
- **AI CLI tools**: Auto-update via cron (logs to `/tmp/cli-update.log`)

Verify:
```bash
# Check EasyTier restart policy
docker inspect easytier --format='{{.HostConfig.RestartPolicy.Name}}'

# Check mihomo restart policy and TUN capabilities
docker inspect mihomo --format='{{.HostConfig.RestartPolicy.Name}}'
docker inspect mihomo --format='{{.HostConfig.CapAdd}}'

# Check TUN interface after reboot
ip addr show Meta

# Check cron job
crontab -l | grep -E 'claude-code|codex|gemini'
```

## Troubleshooting

### EasyTier not connecting

```bash
# Check container status
docker ps | grep easytier

# View logs
docker logs easytier

# Restart container
docker restart easytier
```

### Mihomo TUN mode not working

```bash
# Check container status
docker ps | grep mihomo
docker logs mihomo | tail -50

# Check TUN interface
ip addr show Meta
# Should show: Meta: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP>

# Check DNS hijacking
ss -tulnp | grep :1053

# Test without proxy env vars
unset http_proxy https_proxy
curl -v https://www.google.com

# Check routing
ip route show table all | grep Meta

# Restart mihomo
docker restart mihomo
sleep 3
ip addr show Meta

# Check for conflicts with iptables/nftables
sudo iptables -t nat -L -n -v
sudo nft list ruleset | grep -A5 "chain nat"
```

### AI CLI tools issues

```bash
# Check installation
which claude-code codex gemini-cli

# View update logs
tail -f /tmp/cli-update.log

# Manual update
sudo npm i -g @anthropic-ai/claude-code@latest
```

### Hapi connection issues

```bash
# Check hapi status
hapi status

# Restart hapi
hapi runner start
```

### API Key Conflict Error (401)

**Error message**: `提供了多个冲突的 API 密钥。请仅使用一种认证方式。`

**Root cause**: Multiple configuration files set both `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN`.

**Check ALL these locations**:

```bash
# 1. Claude Code settings (MOST IMPORTANT)
cat ~/.claude/settings.json | grep -A5 'env'

# 2. System environment
cat /etc/environment | grep ANTHROPIC

# 3. User shell config
grep ANTHROPIC ~/.bashrc ~/.profile ~/.bash_profile ~/.zshrc 2>/dev/null

# 4. Hapi config files
cat ~/.hapi/env
cat ~/.hapi/load_env.sh

# 5. Running process environment
for pid in $(pgrep -f 'hapi hub'); do
  echo "PID $pid:"
  cat /proc/$pid/environ 2>/dev/null | tr '\0' '\n' | grep ANTHROPIC
done
```

**Fix**: Keep ONLY `ANTHROPIC_API_KEY`, remove ALL `ANTHROPIC_AUTH_TOKEN`:

```bash
# Fix ~/.claude/settings.json
cat ~/.claude/settings.json | jq '.env = {"ANTHROPIC_API_KEY": "YOUR_KEY", "ANTHROPIC_BASE_URL": "YOUR_URL"}' > /tmp/settings.json && mv /tmp/settings.json ~/.claude/settings.json

# Fix /etc/environment
sudo sed -i '/ANTHROPIC_AUTH_TOKEN/d' /etc/environment

# Fix ~/.bashrc
sed -i '/ANTHROPIC_AUTH_TOKEN/d' ~/.bashrc

# Fix ~/.hapi/env (keep only API_KEY)
cat > ~/.hapi/env <<EOF
ANTHROPIC_API_KEY=YOUR_KEY
ANTHROPIC_BASE_URL=YOUR_URL
EOF

# Fix ~/.hapi/load_env.sh
cat > ~/.hapi/load_env.sh <<EOF
export ANTHROPIC_API_KEY="YOUR_KEY"
export ANTHROPIC_BASE_URL="YOUR_URL"
EOF

# Restart hapi with clean environment
pkill -9 -f hapi
nohup hapi hub > /tmp/hub.log 2>&1 &
sleep 3
nohup hapi runner start > /tmp/runner.log 2>&1 &
```

**Verify fix**:
```bash
# Check no AUTH_TOKEN in running process
cat /proc/$(pgrep -f 'hapi hub' | head -1)/environ 2>/dev/null | tr '\0' '\n' | grep ANTHROPIC
# Should only show ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL
```

### Configuration sync issues

```bash
# Verify config file exists
ls -la ~/.config/mihomo/config.yaml

# Check file permissions
chmod 644 ~/.config/mihomo/config.yaml
```

### Antigravity AI Chat Connection Issues

**Problem**: Antigravity shows `Cloud Code request timeout` or `Tools: Offline`

**Root cause**: Antigravity's Go-based `language_server_linux_x64` bypasses HTTP_PROXY environment variables

**Solution**: Use mihomo TUN mode for transparent proxying

```bash
# 1. Verify TUN interface is up
ip addr show Meta
# Should show: Meta: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP>

# 2. Check mihomo container status
docker ps | grep mihomo
docker logs mihomo | tail -20

# 3. Verify DNS hijacking
ss -tulnp | grep :1053
# Should show mihomo listening on port 1053

# 4. Test transparent proxying (without proxy env vars)
unset http_proxy https_proxy
curl -I https://www.google.com
# Should succeed via TUN mode

# 5. Check routing rules
ip route show table all | grep Meta

# 6. Monitor real-time traffic
docker logs -f mihomo

# 7. If TUN mode fails, check nftables/iptables conflicts
sudo nft list ruleset | grep -A5 "chain nat"
sudo iptables -t nat -L -n -v

# 8. Restart mihomo if needed
docker restart mihomo
sleep 3
ip addr show Meta
```

**Common issues**:
- **TUN interface not created**: Check Docker capabilities (`--cap-add=NET_ADMIN --device=/dev/net/tun`)
- **DNS not hijacked**: Verify `dns-hijack: [any:53]` in config
- **Routing conflicts**: Check for existing iptables/nftables NAT rules
- **Proxy env vars conflict**: Comment out HTTP_PROXY/HTTPS_PROXY in `~/.bashrc`
