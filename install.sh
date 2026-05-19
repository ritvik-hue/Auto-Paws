#!/usr/bin/env bash
# Auto-Paws one-line installer.
# Downloads the latest Auto-Paws.app from GitHub Releases, installs to /Applications,
# strips Gatekeeper quarantine, sets up the Claude Code PreToolUse hook, launches the app.
set -euo pipefail

REPO="ritvik-hue/Auto-Paws"
APP_NAME="Auto-Paws.app"
APP_DEST="/Applications/$APP_NAME"
WIDGET_DIR="$HOME/.claude_auto_yes"
HOOK_DIR="$HOME/.claude/hooks"
HOOK_SH="$HOOK_DIR/auto_yes_check.sh"
SETTINGS="$HOME/.claude/settings.json"

echo "Auto-Paws installer"
echo "==================="

# Check prerequisites
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: 'jq' is required to safely update $SETTINGS"
  echo "Install with:  brew install jq"
  echo "Then re-run this installer."
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found. Install macOS Command Line Tools:  xcode-select --install"
  exit 1
fi

# 1. Find latest release asset URL
echo "[1/5] Looking up latest release..."
DOWNLOAD_URL=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
for asset in data.get('assets', []):
    if asset['name'].endswith('.zip'):
        print(asset['browser_download_url'])
        break
")

if [ -z "$DOWNLOAD_URL" ]; then
  echo "ERROR: Could not find a .zip asset in the latest release of $REPO"
  exit 1
fi
echo "       $DOWNLOAD_URL"

# 2. Download + unzip into /Applications
echo "[2/5] Downloading and installing app..."
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "$DOWNLOAD_URL" -o "$TMP/app.zip"
unzip -q "$TMP/app.zip" -d "$TMP"

if [ ! -d "$TMP/$APP_NAME" ]; then
  echo "ERROR: Unzipped archive did not contain $APP_NAME"
  ls -la "$TMP"
  exit 1
fi

rm -rf "$APP_DEST"
mv "$TMP/$APP_NAME" "$APP_DEST"
echo "       Installed to $APP_DEST"

# 3. Strip Gatekeeper quarantine so the app launches without 'damaged' warning
echo "[3/5] Stripping quarantine attribute..."
xattr -dr com.apple.quarantine "$APP_DEST" 2>/dev/null || true

# 4. Install Claude Code hook
echo "[4/5] Installing Claude Code hook..."
mkdir -p "$HOOK_DIR" "$WIDGET_DIR"
cat > "$HOOK_SH" <<'HOOK_EOF'
#!/bin/bash
# Auto-Paws PreToolUse hook — auto-approves when ~/.claude_auto_yes/active exists.
FLAG="$HOME/.claude_auto_yes/active"
APPROVE_LOG="$HOME/.claude_auto_yes/approvals.log"
if [ -f "$FLAG" ]; then
  date +%s >> "$APPROVE_LOG"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"auto-paws active"}}'
fi
exit 0
HOOK_EOF
chmod +x "$HOOK_SH"

# Ensure settings.json exists and is valid before merging
[ -f "$SETTINGS" ] || echo '{}' > "$SETTINGS"
if ! jq empty "$SETTINGS" >/dev/null 2>&1; then
  echo "ERROR: $SETTINGS is not valid JSON. Fix it before re-running."
  exit 1
fi

CMD="bash $HOOK_SH"
TMP_JSON=$(mktemp)
jq --arg cmd "$CMD" '
  .hooks //= {} |
  .hooks.PreToolUse //= [] |
  .hooks.PreToolUse = (
    [.hooks.PreToolUse[] | select((.hooks // []) | map(.command) | index($cmd) | not)] +
    [{matcher: "*", hooks: [{type: "command", command: $cmd, timeout: 3}]}]
  )
' "$SETTINGS" > "$TMP_JSON"
mv "$TMP_JSON" "$SETTINGS"
echo "       Hook registered in $SETTINGS"

# 5. Launch
echo "[5/5] Launching Auto-Paws..."
open "$APP_DEST"

echo ""
echo "Done. Look for the 🟦 icon in your menu bar."
echo "Restart your Claude Code panel in VS Code/Cursor (once) so it picks up the hook."
echo "Then click 🟦 → Start watching."
