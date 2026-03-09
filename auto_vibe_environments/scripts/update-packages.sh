#!/bin/bash
# Auto NPM Update Script
# Checks for outdated npm packages and updates them if newer versions are available

# Default packages
npm outdated -g @anthropic-ai/claude-code 2>/dev/null | grep -q '@anthropic-ai/claude-code' && npm install -g @anthropic-ai/claude-code@latest --force
npm outdated -g @openai/codex 2>/dev/null | grep -q '@openai/codex' && npm install -g @openai/codex@latest --force

# Update skill-creator from GitHub
SKILL_PATH="$HOME/.claude/skills/skill-creator"
TEMP_REPO="/tmp/skills-repo-update"

git clone --depth 1 https://github.com/anthropics/skills.git "$TEMP_REPO" 2>/dev/null

if [ -d "$TEMP_REPO/skills/skill-creator" ]; then
    if ! diff -r "$SKILL_PATH" "$TEMP_REPO/skills/skill-creator" > /dev/null 2>&1; then
        rm -rf "$SKILL_PATH"
        cp -r "$TEMP_REPO/skills/skill-creator" "$SKILL_PATH"
    fi
fi

rm -rf "$TEMP_REPO"

# Update find-skills from GitHub
FIND_SKILLS_PATH="$HOME/.claude/skills/find-skills"
VERCEL_REPO="/tmp/vercel-skills-update"

git clone --depth 1 https://github.com/vercel-labs/skills.git "$VERCEL_REPO" 2>/dev/null

if [ -d "$VERCEL_REPO/skills/find-skills" ]; then
    if ! diff -r "$FIND_SKILLS_PATH" "$VERCEL_REPO/skills/find-skills" > /dev/null 2>&1; then
        rm -rf "$FIND_SKILLS_PATH"
        cp -r "$VERCEL_REPO/skills/find-skills" "$FIND_SKILLS_PATH"
    fi
fi

rm -rf "$VERCEL_REPO"
