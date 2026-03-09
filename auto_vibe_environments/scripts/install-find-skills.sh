#!/bin/bash
# Install find-skills from vercel-labs/skills
git clone https://github.com/vercel-labs/skills.git /tmp/vercel-skills
cp -r /tmp/vercel-skills/skills/find-skills ~/.claude/skills/
rm -rf /tmp/vercel-skills
