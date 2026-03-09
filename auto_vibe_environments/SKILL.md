---
name: auto_vibe_environments
description: Automatically deploy and configure development tools including Agent Reach, GitHub CLI, and npm package auto-updates. Use when the user wants to set up their development environment, install Agent Reach, configure GitHub authentication, set up scheduled updates, or mentions "部署工具", "安装环境", "deploy tools", "setup environment", "install agent reach", "configure github", "定时更新", "自动更新", or wants to manage development tools and packages.
---

# Auto Vibe Environments

Automatically deploy and configure essential development tools and set up automated maintenance.

## What this skill does

Deploys and configures a complete development environment including:
- **Agent Reach**: Multi-platform content access (Twitter, YouTube, GitHub, Reddit, etc.)
- **GitHub CLI**: GitHub authentication and repository management
- **Auto-update system**: Scheduled npm package updates with cron jobs

Capabilities:
- Install Agent Reach with all dependencies
- Configure GitHub CLI authentication
- Set up automatic npm package updates
- Manage update schedules and package lists

## When to use this skill

Use this skill when the user wants to:
- Deploy development environment tools
- Install Agent Reach
- Configure GitHub CLI authentication
- Set up automatic npm package updates
- Create scheduled tasks for package maintenance
- Add or remove packages from auto-update lists
- Change update schedules

## Core Components

### 1. Agent Reach Installation
Installs Agent Reach with all dependencies for multi-platform content access.

**What gets installed:**
- Agent Reach Python package
- Node.js dependencies (xreach, undici)
- yt-dlp for YouTube
- mcporter for search backend
- WeChat article tools
- Xiaoyuzhou transcription tools

**Channels enabled by default:**
- YouTube, RSS, Web pages (Jina Reader)
- Twitter/X, Bilibili, WeChat articles
- Exa semantic search (free, no API key)

### 2. GitHub CLI Setup
Installs and authenticates GitHub CLI for repository management.

**Installation steps:**
- Add GitHub CLI repository
- Install gh package
- Run authentication flow
- Verify authentication status

### 3. Skill Creator Installation
Installs the official Anthropic skill-creator for creating and managing Claude skills.

**What gets installed:**
- Complete skill-creator from GitHub
- Evaluation and benchmarking tools
- Skill packaging and optimization scripts

**Installation source:**
- GitHub: https://github.com/anthropics/skills/tree/main/skills/skill-creator

### 4. Find Skills Installation
Installs the Vercel Labs find-skills tool for discovering and installing agent skills.

**What gets installed:**
- Complete find-skills from GitHub
- Skill discovery and search capabilities
- Integration with skills.sh ecosystem

**Installation source:**
- GitHub: https://github.com/vercel-labs/skills/tree/main/skills/find-skills

### 5. NPM Auto-Update System
Creates scheduled tasks to keep npm packages up to date.

**Default packages:**
- @anthropic-ai/claude-code
- @openai/codex

**Default schedule:** 12:00 and 00:00 daily

## Implementation Workflow

### Initial User Interaction

**IMPORTANT**: When this skill is first invoked, ALWAYS use AskUserQuestion to ask the user which components they want to install. This ensures the user has control over what gets installed on their system.

Use AskUserQuestion with the following configuration:
- Question: "Which development tools would you like to install?"
- Header: "Setup Options"
- Options (all selected by default via multiSelect):
  1. "Agent Reach" - Multi-platform content access (Twitter, YouTube, GitHub, etc.)
  2. "GitHub CLI" - GitHub authentication and repository management
  3. "Skill Creator" - Official Anthropic skill creation and management tool
  4. "Find Skills" - Vercel Labs skill discovery and installation tool
  5. "NPM Auto-Updates" - Scheduled package updates with cron jobs (includes skill-creator and find-skills updates)
- Set multiSelect: true to allow multiple selections
- Default: All options selected

After receiving the user's selection, proceed with installing only the selected components.

### Full Environment Setup
When user says "部署开发环境" or "setup my dev environment":

1. **Install Agent Reach**
   ```bash
   pip install https://github.com/Panniantong/agent-reach/archive/main.zip
   agent-reach install --env=auto
   ```

2. **Install GitHub CLI**
   ```bash
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update && sudo apt install gh -y
   ```

3. **Authenticate GitHub**
   ```bash
   gh auth login
   ```
   Guide user through browser authentication with one-time code.

4. **Install Skill Creator**
   ```bash
   git clone https://github.com/anthropics/skills.git /tmp/skills-repo
   cp -r /tmp/skills-repo/skills/skill-creator ~/.claude/skills/
   rm -rf /tmp/skills-repo
   ```

5. **Install Find Skills**
   ```bash
   git clone https://github.com/vercel-labs/skills.git /tmp/vercel-skills
   cp -r /tmp/vercel-skills/skills/find-skills ~/.claude/skills/
   rm -rf /tmp/vercel-skills
   ```

6. **Set up NPM auto-updates**
   - Create update script at `~/update-npm-packages.sh`
   - Add packages: @anthropic-ai/claude-code, @openai/codex
   - Add skill-creator update check from GitHub
   - Configure cron job for scheduled updates
   - Set up logging to `~/npm-update.log`

6. **Verify installation**
   ```bash
   agent-reach doctor
   gh auth status
   crontab -l
   ```

### Individual Component Setup

#### Agent Reach Only
User: "安装 Agent Reach" or "install agent reach"
- Run pip install
- Run agent-reach install --env=auto
- Show status with agent-reach doctor
- Explain available channels

#### GitHub CLI Only
User: "配置 GitHub" or "setup github cli"
- Install gh CLI
- Run authentication
- Verify with gh auth status

#### Skill Creator Only
User: "安装 Skill Creator" or "install skill creator"
- Clone skills repository
- Copy skill-creator to ~/.claude/skills/
- Verify installation

#### Find Skills Only
User: "安装 Find Skills" or "install find skills"
- Clone vercel-labs/skills repository
- Copy find-skills to ~/.claude/skills/
- Verify installation

#### NPM Auto-Update Only
User: "设置定时更新" or "setup auto updates"
- Create update script (includes npm packages and skill-creator)
- Configure cron job
- Show configuration

## Usage Patterns

### Pattern 1: Full Environment Deployment
User: "部署我的开发环境" or "setup my dev environment"

Execute all three components:
1. Install Agent Reach
2. Install and authenticate GitHub CLI
3. Set up NPM auto-updates

Show final status summary.

### Pattern 2: Agent Reach Installation
User: "安装 Agent Reach" or "install agent reach"

Steps:
- Install via pip
- Run agent-reach install --env=auto
- Show agent-reach doctor output
- Explain available channels and optional configurations

### Pattern 3: GitHub Setup
User: "配置 GitHub" or "setup github"

Steps:
- Install gh CLI (if not installed)
- Run gh auth login
- Guide user through browser authentication
- Verify with gh auth status

### Pattern 4: NPM Auto-Update
User: "设置定时更新" or "setup auto updates"

Steps:
- Create ~/update-npm-packages.sh
- Add default packages (claude-code, codex)
- Configure cron (default: 12:00 and 00:00)
- Set up logging to ~/npm-update.log

### Pattern 5: Custom Schedule
User: "每天早上8点和晚上8点更新"

Parse time and create custom cron schedule.

### Pattern 6: Add/Remove Packages
User: "添加 @vue/cli 到自动更新"

Read existing script, add package, preserve configuration.

## NPM Update Script Details

### Script Template
```bash
#!/bin/bash
npm outdated -g @package/name 2>/dev/null | grep -q '@package/name' && npm install -g @package/name@latest --force
```

This pattern:
- Checks if package has updates available
- Only runs install if update is needed
- Uses `--force` to handle directory lock issues
- Suppresses unnecessary output

### Default Configuration
- **Script location**: `~/update-npm-packages.sh`
- **Log file**: `~/npm-update.log`
- **Default packages**: @anthropic-ai/claude-code, @openai/codex
- **Default schedule**: 0 12,0 * * * (12:00 and 00:00 daily)

### Cron Format Reference
```
minute hour day month weekday command
0-59   0-23 1-31 1-12  0-7
```

Common patterns:
- `0 12,0 * * *` - Daily at noon and midnight
- `0 8,20 * * *` - Daily at 8am and 8pm
- `0 */6 * * *` - Every 6 hours
- `0 2 * * *` - Daily at 2am

## Agent Reach Configuration

### Post-Installation Steps
After installing Agent Reach, guide users on optional configurations:

**GitHub CLI Authentication** (if not done):
```bash
gh auth login
```

**Additional channels** (optional):
- Weibo: `pip install git+https://github.com/Panniantong/mcp-server-weibo.git && mcporter config add weibo --command 'mcp-server-weibo'`
- Xiaoyuzhou podcasts: Install ffmpeg and configure Groq API key
- Reddit: Configure proxy if server IP is blocked
- XiaoHongShu, Douyin, LinkedIn: Install respective MCP servers

### Verification Commands
```bash
agent-reach doctor    # Check Agent Reach status
gh auth status        # Verify GitHub authentication
crontab -l           # List cron jobs
```

## Error Handling

### NPM Update Failures
If npm update fails due to directory locks:
- Script uses `--force` flag automatically
- If persistent issues occur:
  ```bash
  rm -rf ~/.nvm/versions/node/*/lib/node_modules/@package/name
  npm install -g @package/name@latest --force
  ```

### GitHub Authentication Issues
If `gh auth login` fails:
- Ensure browser is available for authentication
- Provide one-time code for manual entry
- Verify with `gh auth status`

### Agent Reach Installation Issues
If installation times out or fails:
- Check internet connection
- Retry with `agent-reach install --env=auto`
- Use `agent-reach doctor` to diagnose issues

## Important Notes

- Always use absolute paths in cron commands
- Redirect output to log files for debugging
- Verify cron syntax before adding jobs
- Test scripts manually before relying on cron
- Agent Reach skill is installed at `~/.claude/skills/agent-reach`
- All configurations persist across sessions
