# Installing Auto-Paws

A step-by-step guide for getting Auto-Paws running on your Mac.

## One-line install (recommended)

Open **Terminal** (Cmd+Space → "Terminal" → Enter) and paste:

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

That's it. The installer will:

1. Check you have `jq` and `python3` available
2. Download the latest `Auto-Paws.app` from GitHub Releases
3. Move it to `/Applications/Auto-Paws.app`
4. Strip the macOS quarantine flag so Gatekeeper doesn't block it
5. Install the Claude Code permission hook at `~/.claude/hooks/auto_yes_check.sh`
6. Register the hook in `~/.claude/settings.json`
7. Launch the app — look for **🟦** in your menu bar

---

## Prerequisites

| Tool | Why | Install command |
|---|---|---|
| macOS 12+ on Apple Silicon | The app is built arm64-only | n/a |
| `jq` | Safe JSON editing of `~/.claude/settings.json` | `brew install jq` |
| `python3` | Used by `install.sh` to parse the GitHub API response | Ships with macOS Command Line Tools — `xcode-select --install` if missing |
| Claude Code in VS Code or Cursor | The thing being auto-approved | Install Claude Code extension first |

If you don't have Homebrew yet: see [brew.sh](https://brew.sh).

---

## First-time use

1. After install, the **🟦** icon appears in your menu bar (top-right of screen, near the clock).
2. **Restart your Claude Code panel** in VS Code/Cursor — close it, reopen it. This is only needed once; Claude Code reads the hook config at startup.
3. Click **🟦** → **Start watching**. Icon turns **🟢**.
4. Ask Claude Code to run any command — it will execute instantly with no permission prompt.
5. The **Approvals** counter in the menu ticks up each time a prompt is skipped.
6. Click **🟢** → **Stop watching** to return to normal manual approval.

---

## Auto-start at login (optional)

1. System Settings → General → **Login Items**
2. Click **+** under "Open at Login"
3. Select `/Applications/Auto-Paws.app`

Now Auto-Paws launches automatically every time you log in.

---

## Updating

Run the same one-line install command again:

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

It downloads the latest release and overwrites the existing app. Your hook config stays in place.

---

## Manual install (if you can't use curl-bash)

1. Go to the [Releases page](https://github.com/ritvik-hue/Auto-Paws/releases/latest).
2. Download `Auto-Paws.app.zip`.
3. Double-click to unzip → drag `Auto-Paws.app` to `/Applications`.
4. **Important — clear the quarantine flag** so it can launch:
   ```bash
   xattr -dr com.apple.quarantine /Applications/Auto-Paws.app
   ```
   Or right-click the app → **Open** → confirm in the dialog (one-time).
5. Install the hook manually:
   ```bash
   curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install_hook.command | bash
   ```
6. Launch the app from Applications.

---

## Build from source

If you want to build the app yourself instead of using the prebuilt release:

```bash
git clone https://github.com/ritvik-hue/Auto-Paws.git
cd Auto-Paws
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt py2app
python setup.py py2app
open dist/Auto-Paws.app
```

The .app appears in `dist/`. Drag to `/Applications` if you want to keep it.

---

## Troubleshooting

### `jq not found`
Install Homebrew (https://brew.sh), then `brew install jq`. Re-run installer.

### `"Auto-Paws" is damaged and can't be opened`
The quarantine flag wasn't removed. Run:
```bash
xattr -dr com.apple.quarantine /Applications/Auto-Paws.app
```
Then launch the app from Applications.

### `python3: command not found`
Run `xcode-select --install` to install the macOS Command Line Tools.

### Menu bar icon doesn't show after launch
Wait a few seconds — first launch is slower because macOS verifies the signature. If still nothing after 10 seconds, run from Terminal to see errors:
```bash
/Applications/Auto-Paws.app/Contents/MacOS/Auto-Paws
```

### Claude Code still prompts even when 🟢
The Claude Code panel must be restarted once after install so it picks up the new hook. Close the Claude Code panel in VS Code/Cursor and reopen.

### Approvals counter stuck at 0
Trigger any Claude Code tool call (ask Claude to run a command). The counter only increments when the hook actually fires.

### Want to confirm the hook is registered
```bash
jq '.hooks.PreToolUse' ~/.claude/settings.json
ls -la ~/.claude/hooks/auto_yes_check.sh
```
You should see an entry pointing at `auto_yes_check.sh` and the script with executable permissions.

---

## Uninstall

```bash
# Remove the app
rm -rf /Applications/Auto-Paws.app

# Remove the hook
rm ~/.claude/hooks/auto_yes_check.sh

# Remove widget state
rm -rf ~/.claude_auto_yes

# Remove the hook entry from ~/.claude/settings.json
jq '.hooks.PreToolUse = (.hooks.PreToolUse | map(select((.hooks // []) | map(.command) | join(",") | contains("auto_yes_check.sh") | not)))' ~/.claude/settings.json > /tmp/s.json && mv /tmp/s.json ~/.claude/settings.json
```

---

## Security notes

- While Auto-Paws is **🟢**, **every** Claude Code tool call is auto-approved. That includes Bash commands, file writes, file edits, web fetches — anything Claude Code would normally ask permission for.
- Toggle off (**🟦**) between tasks if you want to review individual commands.
- Closing the app cleanly always removes the flag. If the app crashes mid-session and you're worried the flag is still set:
  ```bash
  rm -f ~/.claude_auto_yes/active
  ```
- The hook script is plain bash and lives in your home directory. You can inspect it any time:
  ```bash
  cat ~/.claude/hooks/auto_yes_check.sh
  ```
- Nothing is sent over the network. All state stays on your Mac.

---

## Reporting issues

Open an issue at https://github.com/ritvik-hue/Auto-Paws/issues. Include:
- macOS version (`sw_vers`)
- Mac type (Intel or Apple Silicon — `uname -m`)
- The widget log: `~/.claude_auto_yes/log.txt`
