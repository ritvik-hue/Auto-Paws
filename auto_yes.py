#!/usr/bin/env python3
"""Menu bar widget: toggle Claude Code PreToolUse auto-approval via a flag file.

When 'watching': writes ~/.claude_auto_yes/active. A pre-installed PreToolUse hook
in ~/.claude/hooks/auto_yes_check.sh reads that flag and tells Claude Code to
approve every tool call automatically — no permission prompts shown.

Works for every VS Code/Cursor window across every Space, regardless of foreground
app, because the hook runs inside Claude Code's process. No screen capture needed.
"""
import platform
import threading
import traceback
from datetime import datetime
from pathlib import Path

import rumps
from Foundation import NSOperationQueue, NSProcessInfo

WIDGET_DIR = Path.home() / ".claude_auto_yes"
WIDGET_DIR.mkdir(exist_ok=True)
FLAG_PATH = WIDGET_DIR / "active"
APPROVALS_LOG = WIDGET_DIR / "approvals.log"
LOG_PATH = WIDGET_DIR / "log.txt"
HOOK_PATH = Path.home() / ".claude" / "hooks" / "auto_yes_check.sh"

NSActivityUserInitiatedAllowingIdleSystemSleep = 0x00FFFFFF


def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    try:
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def disable_app_nap():
    try:
        return NSProcessInfo.processInfo().beginActivityWithOptions_reason_(
            NSActivityUserInitiatedAllowingIdleSystemSleep,
            "Auto-Paws flag toggle",
        )
    except Exception as e:
        log(f"App Nap disable failed: {e}")
        return None


def count_approvals():
    if not APPROVALS_LOG.exists():
        return 0
    try:
        with open(APPROVALS_LOG, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


class AutoYesApp(rumps.App):
    def __init__(self):
        super().__init__("🟦", quit_button=None)
        self._nap_token = disable_app_nap()
        self.watching = False
        self.baseline_count = 0
        log(f"Startup. macOS {platform.mac_ver()[0]} | Python {platform.python_version()} | arch {platform.machine()}")
        self._check_hook_installed()

        self.watch_item = rumps.MenuItem("Start watching", callback=self.toggle_watch)
        self.status_item = rumps.MenuItem("Status: idle", callback=None)
        self.count_item = rumps.MenuItem("Approvals: 0", callback=None)
        self.reset_item = rumps.MenuItem("Reset count", callback=self.reset_count)
        self.open_log_item = rumps.MenuItem("Open log", callback=self.open_log)
        self.menu = [
            self.watch_item,
            None,
            self.status_item,
            self.count_item,
            self.reset_item,
            None,
            self.open_log_item,
            None,
            rumps.MenuItem("Quit", callback=self.quit_widget),
        ]

        # Make sure flag is off when widget starts — fresh state
        self._remove_flag()

        # Poll approvals log on main thread; rumps.Timer runs on main thread.
        self._timer = rumps.Timer(self._tick, 1)
        self._timer.start()

    def _check_hook_installed(self):
        if not HOOK_PATH.exists():
            log(f"WARNING: hook not installed at {HOOK_PATH}")
            log("Run install_hook.command to set it up.")
        else:
            log(f"Hook found at {HOOK_PATH}")

    def _ui(self, fn):
        try:
            NSOperationQueue.mainQueue().addOperationWithBlock_(fn)
        except Exception:
            fn()

    def _write_flag(self):
        try:
            FLAG_PATH.write_text(datetime.now().isoformat())
            log(f"Flag ON: {FLAG_PATH}")
        except Exception as e:
            log(f"Failed to write flag: {e}")

    def _remove_flag(self):
        try:
            if FLAG_PATH.exists():
                FLAG_PATH.unlink()
                log(f"Flag OFF: {FLAG_PATH}")
        except Exception as e:
            log(f"Failed to remove flag: {e}")

    def toggle_watch(self, sender):
        if self.watching:
            self.watching = False
            self._remove_flag()
            sender.title = "Start watching"
            self.title = "🟦"
            self.status_item.title = "Status: idle"
        else:
            if not HOOK_PATH.exists():
                rumps.alert(
                    "Hook not installed",
                    f"The Claude Code hook was not found at:\n{HOOK_PATH}\n\n"
                    "Run install_hook.command (in the widget folder) once, then try again.",
                )
                return
            self.watching = True
            self.baseline_count = count_approvals()
            self._write_flag()
            sender.title = "Stop watching"
            self.title = "🟢"
            self.status_item.title = "Status: watching"

    def reset_count(self, _):
        try:
            if APPROVALS_LOG.exists():
                APPROVALS_LOG.unlink()
        except Exception as e:
            log(f"reset_count failed: {e}")
        self.baseline_count = 0
        self.count_item.title = "Approvals: 0"

    def open_log(self, _):
        import subprocess
        subprocess.Popen(["open", str(LOG_PATH)])

    def quit_widget(self, _):
        self._remove_flag()
        rumps.quit_application()

    def _tick(self, _):
        total = count_approvals()
        delta = max(0, total - self.baseline_count)
        self.count_item.title = f"Approvals: {delta}"


if __name__ == "__main__":
    log("=" * 50)
    log("Process start")
    try:
        AutoYesApp().run()
    except Exception as e:
        log(f"Fatal: {e}\n{traceback.format_exc()}")
        raise
