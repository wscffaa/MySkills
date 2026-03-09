#!/bin/bash
# Check and update find-skills from GitHub

SKILL_PATH="$HOME/.claude/skills/find-skills"
TEMP_REPO="/tmp/vercel-skills-update"

# Clone the latest version
git clone --depth 1 https://github.com/vercel-labs/skills.git "$TEMP_REPO" 2>/dev/null

if [ -d "$TEMP_REPO/skills/find-skills" ]; then
    # Check if there are differences
    if ! diff -r "$SKILL_PATH" "$TEMP_REPO/skills/find-skills" > /dev/null 2>&1; then
        echo "Updating find-skills..."
        rm -rf "$SKILL_PATH"
        cp -r "$TEMP_REPO/skills/find-skills" "$SKILL_PATH"
        echo "find-skills updated successfully"
    fi
fi

# Cleanup
rm -rf "$TEMP_REPO"
