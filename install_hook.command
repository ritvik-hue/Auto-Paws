#!/bin/bash
# Installs the Claude Code PreToolUse hook used by the Auto-Yes widget.
# Idempotent: safe to run multiple times.

set -e

HOOK_DIR="$HOME/.claude/hooks"
SETTINGS="$HOME/.claude/settings.json"
HOOK_SH="$HOOK_DIR/auto_yes_check.sh"
WIDGET_DIR="$HOME/.claude_auto_yes"

echo "Setting up Claude Auto-Yes hook..."

mkdir -p "$HOOK_DIR"
mkdir -p "$WIDGET_DIR"

cat > "$HOOK_SH" <<'EOF'
#!/bin/bash
# Claude Code PreToolUse hook — installed by Claude Auto-Yes widget.
# If the widget's flag file exists, auto-approve every tool call.
# Otherwise exit silently and let Claude Code show the normal prompt.

FLAG="$HOME/.claude_auto_yes/active"
APPROVE_LOG="$HOME/.claude_auto_yes/approvals.log"

if [ -f "$FLAG" ]; then
  date +%s >> "$APPROVE_LOG"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"auto-yes widget active"}}'
fi
exit 0
EOF

chmod +x "$HOOK_SH"
echo "  Hook script written to: $HOOK_SH"

if ! command -v jq >/dev/null 2>&1; then
  echo ""
  echo "ERROR: 'jq' is required to safely modify $SETTINGS"
  echo "Install with:  brew install jq"
  echo "Then re-run this script."
  exit 1
fi

if [ ! -f "$SETTINGS" ]; then
  echo "{}" > "$SETTINGS"
fi

# Sanity-check existing settings.json is valid before touching it.
if ! jq empty "$SETTINGS" >/dev/null 2>&1; then
  echo "ERROR: $SETTINGS is not valid JSON. Fix it before running this script."
  exit 1
fi

CMD="bash $HOOK_SH"
TMP=$(mktemp)

jq --arg cmd "$CMD" '
  .hooks //= {} |
  .hooks.PreToolUse //= [] |
  .hooks.PreToolUse = (
    [.hooks.PreToolUse[] | select((.hooks // []) | map(.command) | index($cmd) | not)] +
    [{matcher: "*", hooks: [{type: "command", command: $cmd, timeout: 3}]}]
  )
' "$SETTINGS" > "$TMP"

mv "$TMP" "$SETTINGS"
echo "  Hook registered in: $SETTINGS"

echo ""
echo "Done. Launch the widget:  bash run.command"
echo "Verify hook config:       jq '.hooks.PreToolUse' \"$SETTINGS\""
