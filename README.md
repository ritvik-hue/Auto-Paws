# Auto-Paws 🐾

[![macOS](https://img.shields.io/badge/macOS-12%2B-blue)](https://www.apple.com/macos/)
[![Apple Silicon](https://img.shields.io/badge/arch-arm64-orange)](https://support.apple.com/en-us/HT211814)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/ritvik-hue/Auto-Paws?include_prereleases)](https://github.com/ritvik-hue/Auto-Paws/releases)

Tiny macOS menu-bar app. Toggle on → **Claude Code auto-approves every permission prompt** in every VS Code / Cursor window, even when those windows are in the background.

No screen capture, no UI scraping, no synthetic clicks. Auto-Paws installs a Claude Code `PreToolUse` hook that returns `allow` server-side before any prompt is shown.

---

## Install

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

Full step-by-step guide → [**docs/INSTALL.md**](docs/INSTALL.md)

### Requirements

- macOS 12+ on Apple Silicon
- `jq` (`brew install jq` if missing)
- Claude Code in VS Code or Cursor

---

## Use

1. **🟦** appears in your menu bar after install
2. Restart your Claude Code panel in VS Code/Cursor (one time, so the new hook is picked up)
3. **🟦 → Start watching → 🟢** = auto-approve on
4. **🟢 → Stop watching → 🟦** = back to normal manual prompts

The **Approvals** counter in the menu shows how many prompts have been skipped since the widget was started.

---

## How it works

When you click **Start watching**, Auto-Paws writes `~/.claude_auto_yes/active`. Before Claude Code shows any permission prompt, it runs the hook script `~/.claude/hooks/auto_yes_check.sh`. The script checks for the flag file — if present, it emits JSON telling Claude Code to skip the prompt.

```
[Menu bar toggle] ──writes──▶ ~/.claude_auto_yes/active ──read by──▶ PreToolUse hook → "allow"
```

Works across all VS Code/Cursor windows, every Space, every foreground state. No screen capture needed.

---

## Trust note ⚠️

While Auto-Paws is **🟢**, **every** Claude Code tool call (Bash, Edit, Write, MultiEdit, WebFetch, ...) is auto-approved. Toggle off between tasks if you want manual control. Closing the app always removes the flag.

---

## Update

Run the install command again. Idempotent — overwrites the existing app, leaves your hook config alone.

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

---

## Auto-start at login

System Settings → General → **Login Items** → **+** → `/Applications/Auto-Paws.app`.

---

## Uninstall

```bash
rm -rf /Applications/Auto-Paws.app
rm ~/.claude/hooks/auto_yes_check.sh
rm -rf ~/.claude_auto_yes
jq '.hooks.PreToolUse = (.hooks.PreToolUse | map(select((.hooks // []) | map(.command) | join(",") | contains("auto_yes_check.sh") | not)))' ~/.claude/settings.json > /tmp/s.json && mv /tmp/s.json ~/.claude/settings.json
```

---

## Build from source

```bash
git clone https://github.com/ritvik-hue/Auto-Paws.git
cd Auto-Paws
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt py2app
python setup.py py2app
open dist/Auto-Paws.app
```

---

## License

[MIT](LICENSE)
