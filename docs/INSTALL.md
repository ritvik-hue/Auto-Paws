# Installing Auto-Paws

Step-by-step install guide.

## One-line install (recommended)

Open **Terminal** (Cmd+Space → "Terminal" → Enter) and paste:

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

The installer will:

1. Check `jq` and `python3` are available
2. Download the latest `Auto-Paws.app` from GitHub Releases
3. Move it to `/Applications/Auto-Paws.app`
4. Strip the macOS quarantine flag so Gatekeeper doesn't block it
5. Install the Claude Code permission hook at `~/.claude/hooks/auto_yes_check.sh`
6. Register the hook in `~/.claude/settings.json`
7. Launch the app — yellow paw icon appears in your menu bar

---

## Prerequisites

| Tool | Why | Install |
|---|---|---|
| macOS 12+ on Apple Silicon | App built arm64-only | n/a |
| `jq` | Safe JSON edits to `~/.claude/settings.json` | `brew install jq` |
| `python3` | install.sh uses it to parse GitHub API | `xcode-select --install` |
| Claude Code in VS Code or Cursor | The thing being auto-approved | Install Claude Code extension first |

Homebrew: [brew.sh](https://brew.sh).

---

## First-time use

1. After install, the **yellow paw** icon appears in your menu bar (top-right, near the clock).
2. **Restart your Claude Code panel** in VS Code/Cursor — close it, reopen it. One-time. Claude Code reads hook config at startup.
3. Click the paw → **Start watching**. Icon turns **green**.
4. Ask Claude Code to run any command — runs instantly, no prompt.
5. The **Approvals (session)** counter ticks up each skipped prompt.
6. Click the green paw → **Stop watching** to return to normal manual approval.

---

## Menu items

| Item | Description |
|---|---|
| Start / Stop watching | Toggle auto-approval |
| Status | `idle` (yellow) or `watching` (green) |
| Approvals (session) | Skipped since widget started or last "Reset session" |
| Approvals (lifetime) | All-time skipped across all sessions |
| Time saved | Estimated, at ~10 sec per skipped prompt |
| Reset session count | Zeroes the session counter |
| Reset lifetime count | Wipes lifetime log (with confirm dialog) |
| Quit | Exit (removes flag file cleanly) |

---

## Auto-start at login (optional)

1. System Settings → General → **Login Items**
2. Click **+** under "Open at Login"
3. Select `/Applications/Auto-Paws.app`

---

## Updating

Run the install command again:

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

Overwrites the existing app. Hook config and lifetime stats are preserved.

---

## Manual install

1. Download `Auto-Paws.app.zip` from [Releases](https://github.com/ritvik-hue/Auto-Paws/releases/latest)
2. Unzip → drag `Auto-Paws.app` to `/Applications`
3. Clear quarantine + install hook:
   ```bash
   xattr -dr com.apple.quarantine /Applications/Auto-Paws.app
   curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install_hook.command | bash
   ```
4. Launch from Applications.

---

## Build from source

```bash
git clone https://github.com/ritvik-hue/Auto-Paws.git
cd Auto-Paws
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt py2app
python setup.py py2app
open dist/Auto-Paws.app
```

---

## Troubleshooting

### `jq not found`
Install Homebrew (https://brew.sh), then `brew install jq`.

### `"Auto-Paws" is damaged and can't be opened`
Quarantine wasn't removed. Run:
```bash
xattr -dr com.apple.quarantine /Applications/Auto-Paws.app
```

### `python3: command not found`
`xcode-select --install`

### Menu bar icon doesn't show
Wait ~10 seconds (first launch verifies signature). If still nothing:
```bash
/Applications/Auto-Paws.app/Contents/MacOS/Auto-Paws
```
Look for the error output.

### Claude Code still prompts even when paw is green
Restart the Claude Code panel in VS Code/Cursor. It only reads the hook config on startup.

### Approvals counter stuck at 0
Trigger any Claude Code tool call. Counter only increments when the hook actually fires.

### Confirm hook is registered
```bash
jq '.hooks.PreToolUse' ~/.claude/settings.json
ls -la ~/.claude/hooks/auto_yes_check.sh
```

---

## Uninstall

```bash
rm -rf /Applications/Auto-Paws.app
rm ~/.claude/hooks/auto_yes_check.sh
rm -rf ~/.claude_auto_yes
jq '.hooks.PreToolUse = (.hooks.PreToolUse | map(select((.hooks // []) | map(.command) | join(",") | contains("auto_yes_check.sh") | not)))' ~/.claude/settings.json > /tmp/s.json && mv /tmp/s.json ~/.claude/settings.json
```

---

## Security notes

- While the paw is **green**, **every** Claude Code tool call is auto-approved (Bash, Edit, Write, MultiEdit, WebFetch, ...).
- Toggle off (paw goes yellow) between tasks if you want to review individual commands.
- Closing the app cleanly always removes the flag. If the app crashes and you suspect the flag is still set:
  ```bash
  rm -f ~/.claude_auto_yes/active
  ```
- The hook script is plain bash. Inspect any time:
  ```bash
  cat ~/.claude/hooks/auto_yes_check.sh
  ```
- Nothing leaves your Mac.

---

## Reporting issues

[github.com/ritvik-hue/Auto-Paws/issues](https://github.com/ritvik-hue/Auto-Paws/issues). Include:
- macOS version (`sw_vers`)
- arch (`uname -m`)
- Log: `~/.claude_auto_yes/log.txt`
