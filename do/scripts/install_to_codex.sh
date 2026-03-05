#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

mkdir -p \
  "$CODEX_HOME/skills/do" \
  "$CODEX_HOME/skills/do/scripts" \
  "$CODEX_HOME/protocols" \
  "$CODEX_HOME/agents"

cp "$ROOT_DIR/SKILL.md" "$CODEX_HOME/skills/do/SKILL.md"
cp "$ROOT_DIR/scripts/csv_artifact_guard.py" "$CODEX_HOME/skills/do/scripts/csv_artifact_guard.py"
cp "$ROOT_DIR/protocols/do-feature.md" "$CODEX_HOME/protocols/do-feature.md"
cp "$ROOT_DIR/protocols/do-csv.md" "$CODEX_HOME/protocols/do-csv.md"
cp "$ROOT_DIR/agents/"*.toml "$CODEX_HOME/agents/"

chmod +x "$CODEX_HOME/skills/do/scripts/csv_artifact_guard.py"

echo "[ok] do skill installed to: $CODEX_HOME"
echo "[next] Restart Codex session, then use:"
echo "       \$do"
echo "       /do <task description>"
echo "       /do-csv <csv path>"
