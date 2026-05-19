<div align="center">
<img
  src="assets/AutoPaws.png"
  width="220"
  alt="Auto-Paws logo"
/>
</div>


### Auto-Paws

A lightweight macOS menu bar app that auto-approves Claude Code permission prompts inside VS Code / Cursor. Toggle on → every Bash / Edit / Write prompt is allowed automatically. Toggle off → normal manual prompts. Works across every VS Code window, every Space, every backgrounded state — no screen capture, no synthetic clicks.

## Download

**Option 1** — Install via the command line:

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

The installer downloads the latest `Auto-Paws.app`, drops it into `/Applications`, strips Gatekeeper quarantine, registers the Claude Code hook, and launches the app.

**Option 2** — Grab the latest `.zip` from [GitHub Releases](https://github.com/ritvik-hue/Auto-Paws/releases/latest).

After unzipping, drag **Auto-Paws.app** into Applications, then run once:

```bash
xattr -dr com.apple.quarantine /Applications/Auto-Paws.app
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install_hook.command | bash
```

> Requires **macOS 12+** on **Apple Silicon**, `jq` (`brew install jq`), and Claude Code installed in VS Code / Cursor.

## Use

1. **🐾 yellow paw** appears in the menu bar after install.
2. Restart your Claude Code panel in VS Code / Cursor once — it needs to pick up the new hook.
3. Click the paw → **Start watching**. Icon turns **🐾 green**.
4. Claude Code now auto-approves every permission prompt across every VS Code window. Counters update live in the menu.
5. Click → **Stop watching** to return to normal manual prompts.

### Menu

| Item | What it shows |
|---|---|
| Status | `idle` or `watching` |
| Approvals (session) | Count since the widget started or you reset the session |
| Approvals (lifetime) | All-time count since you installed Auto-Paws |
| Time saved | Estimated, at ~10 seconds per skipped prompt |
| Reset session count | Zeroes the session counter |
| Reset lifetime count | Wipes the lifetime log (with confirm dialog) |

## How it works

Auto-Paws installs a Claude Code `PreToolUse` hook at `~/.claude/hooks/auto_yes_check.sh` and registers it in `~/.claude/settings.json`. When you toggle **Start watching**, the app writes a flag file at `~/.claude_auto_yes/active`. Before Claude Code shows any permission prompt, it runs the hook script — if the flag is present, the script responds with `allow` and Claude Code skips the prompt entirely.

```
[Menu bar toggle] ──writes──▶ ~/.claude_auto_yes/active ──read by──▶ PreToolUse hook → "allow"
```

No screen capture, no OCR, no UI scraping, no synthetic keystrokes. Works for every window across every Space, regardless of foreground state.

## Update

Re-run the install command. Overwrites the existing app, keeps your hook config and lifetime stats.

```bash
curl -sSL https://raw.githubusercontent.com/ritvik-hue/Auto-Paws/main/install.sh | bash
```

## Auto-start at login

System Settings → General → **Login Items** → **+** → select `/Applications/Auto-Paws.app`.

## Trust note

While the widget is in the **green** state, **every** Claude Code tool call (Bash, Edit, Write, MultiEdit, WebFetch, ...) is auto-approved. Toggle off between tasks if you want manual control. Closing the app cleanly always removes the flag.

## Build from source

```bash
git clone https://github.com/ritvik-hue/Auto-Paws.git
cd Auto-Paws
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt py2app
python setup.py py2app
open dist/Auto-Paws.app
```

## Uninstall

```bash
rm -rf /Applications/Auto-Paws.app
rm ~/.claude/hooks/auto_yes_check.sh
rm -rf ~/.claude_auto_yes
jq '.hooks.PreToolUse = (.hooks.PreToolUse | map(select((.hooks // []) | map(.command) | join(",") | contains("auto_yes_check.sh") | not)))' ~/.claude/settings.json > /tmp/s.json && mv /tmp/s.json ~/.claude/settings.json
```

## Contributing

Contributions welcome.

1. **Fork** the repository.
2. **Clone** your fork:
   ```bash
   git clone https://github.com/<your-username>/Auto-Paws.git
   ```
3. Create a feature branch:
   ```bash
   git checkout -b my-feature
   ```
4. Make your changes. Test with `python3 auto_yes.py` from the repo root.
5. Verify the build still works: `bash build.command` (or `python setup.py py2app`).
6. **Commit** with a clear message and **push** your branch:
   ```bash
   git push origin my-feature
   ```
7. Open a **Pull Request** against `main`.

### Guidelines

- Keep PRs focused — one feature or fix per PR.
- Match the existing code style (PEP 8, no unnecessary deps).
- Bump `CFBundleVersion` and `CFBundleShortVersionString` in `setup.py` when shipping.

## License

[MIT](LICENSE).

---

Built for [Claude Code](https://claude.ai/code).
