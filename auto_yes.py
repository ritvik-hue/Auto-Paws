#!/usr/bin/env python3
"""Auto-Paws — menu bar widget for Claude Code auto-approval."""
import os
import platform
import time
import traceback
from datetime import datetime
from pathlib import Path

import rumps
from Foundation import NSOperationQueue, NSProcessInfo

WIDGET_DIR = Path.home() / ".claude_auto_yes"
WIDGET_DIR.mkdir(exist_ok=True)
FLAG_PATH = WIDGET_DIR / "active"
APPROVALS_LOG = WIDGET_DIR / "approvals.log"
LIFETIME_PATH = WIDGET_DIR / "lifetime.txt"
WATCHING_SECONDS_PATH = WIDGET_DIR / "watching_seconds.txt"
LOG_PATH = WIDGET_DIR / "log.txt"
HOOK_PATH = Path.home() / ".claude" / "hooks" / "auto_yes_check.sh"

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
ICON_IDLE = SCRIPT_DIR / "assets" / "menubar_idle.png"
ICON_ACTIVE = SCRIPT_DIR / "assets" / "menubar_active.png"

# Average seconds saved per auto-approval (read prompt, evaluate, click, refocus).
SEC_PER_APPROVAL = 10

# Persist watching seconds every N ticks to limit disk writes
FLUSH_EVERY_TICKS = 15

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


def count_approvals_log():
    if not APPROVALS_LOG.exists():
        return 0
    try:
        with open(APPROVALS_LOG, "rb") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def read_int_file(path):
    if not path.exists():
        return 0
    try:
        return int(path.read_text().strip() or "0")
    except Exception:
        return 0


def write_int_file(path, n):
    try:
        path.write_text(str(int(n)))
    except Exception as e:
        log(f"Failed to write {path}: {e}")


def format_duration(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


class AutoYesApp(rumps.App):
    def __init__(self):
        icon = str(ICON_IDLE) if ICON_IDLE.exists() else None
        super().__init__("", icon=icon, template=False, quit_button=None)
        self._nap_token = disable_app_nap()

        self.watching = False
        self.session_baseline = count_approvals_log()

        # Watching-time accounting:
        # disk_seconds = total persisted seconds widget has been in active state across all sessions
        # session_start = wall-clock timestamp of the current active-state segment (None if idle)
        # ticks_since_flush = how many seconds since last disk write (limit I/O)
        self.disk_watching_seconds = read_int_file(WATCHING_SECONDS_PATH)
        self.session_start = None
        self.session_watching_seconds = 0
        self.ticks_since_flush = 0

        log(f"Startup. macOS {platform.mac_ver()[0]} | Python {platform.python_version()} | arch {platform.machine()}")
        self._check_hook_installed()

        self.watch_item = rumps.MenuItem("Start watching", callback=self.toggle_watch)
        self.status_item = rumps.MenuItem("Status: idle", callback=None)
        self.session_item = rumps.MenuItem("Approvals (session): 0", callback=None)
        self.lifetime_item = rumps.MenuItem("Approvals (lifetime): 0", callback=None)
        self.watching_time_item = rumps.MenuItem("Watching time: 0s", callback=None)
        self.time_clicks_item = rumps.MenuItem("Saved (clicks): 0s", callback=None)
        self.time_total_item = rumps.MenuItem("Total time saved: 0s", callback=None)
        self.reset_session_item = rumps.MenuItem("Reset session count", callback=self.reset_session)
        self.reset_lifetime_item = rumps.MenuItem("Reset lifetime stats", callback=self.reset_lifetime)
        self.menu = [
            self.watch_item,
            None,
            self.status_item,
            self.session_item,
            self.lifetime_item,
            None,
            self.watching_time_item,
            self.time_clicks_item,
            self.time_total_item,
            None,
            self.reset_session_item,
            self.reset_lifetime_item,
            None,
            rumps.MenuItem("Quit", callback=self.quit_widget),
        ]

        # Fresh-start: flag off until user toggles on
        self._remove_flag()

        self._refresh_counts()

        # rumps.Timer fires on main thread — safe for UI updates
        self._timer = rumps.Timer(self._tick, 1)
        self._timer.start()

    def _check_hook_installed(self):
        if not HOOK_PATH.exists():
            log(f"WARNING: hook not installed at {HOOK_PATH}")
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

    def _set_icon(self, watching):
        target = ICON_ACTIVE if watching else ICON_IDLE
        if target.exists():
            try:
                self.icon = str(target)
            except Exception as e:
                log(f"Failed to set icon: {e}")

    def _flush_watching_to_disk(self):
        """Move accumulated session_watching_seconds onto disk_watching_seconds and persist."""
        if self.session_watching_seconds <= 0:
            return
        self.disk_watching_seconds += self.session_watching_seconds
        self.session_watching_seconds = 0
        self.ticks_since_flush = 0
        write_int_file(WATCHING_SECONDS_PATH, self.disk_watching_seconds)

    def toggle_watch(self, sender):
        if self.watching:
            # Going from watching -> idle: flush accumulated time and switch off
            self.watching = False
            self._flush_watching_to_disk()
            self.session_start = None
            self._remove_flag()
            sender.title = "Start watching"
            self.status_item.title = "Status: idle"
            self._set_icon(watching=False)
        else:
            if not HOOK_PATH.exists():
                rumps.alert(
                    "Hook not installed",
                    f"The Claude Code hook was not found at:\n{HOOK_PATH}\n\n"
                    "Reinstall Auto-Paws: re-run the curl install command.",
                )
                return
            self.watching = True
            self.session_baseline = count_approvals_log()
            self.session_start = time.time()
            self.session_watching_seconds = 0
            self.ticks_since_flush = 0
            self._write_flag()
            sender.title = "Stop watching"
            self.status_item.title = "Status: watching"
            self._set_icon(watching=True)

    def reset_session(self, _):
        self.session_baseline = count_approvals_log()
        if self.watching:
            # Restart current watching segment cleanly
            self.session_start = time.time()
            self.session_watching_seconds = 0
        self._refresh_counts()

    def reset_lifetime(self, _):
        response = rumps.alert(
            title="Reset lifetime stats?",
            message="Clears all-time approvals, watching time, and time-saved estimates. Cannot be undone.",
            ok="Reset",
            cancel="Cancel",
        )
        if response != 1:
            return
        try:
            if APPROVALS_LOG.exists():
                APPROVALS_LOG.unlink()
        except Exception as e:
            log(f"reset_lifetime: failed to unlink approvals.log: {e}")
        write_int_file(LIFETIME_PATH, 0)
        write_int_file(WATCHING_SECONDS_PATH, 0)
        self.disk_watching_seconds = 0
        self.session_watching_seconds = 0
        if self.watching:
            self.session_start = time.time()
        self.session_baseline = 0
        self._refresh_counts()

    def quit_widget(self, _):
        # Persist any unflushed watching time before exit
        if self.watching:
            self._flush_watching_to_disk()
        self._remove_flag()
        rumps.quit_application()

    def _total_watching_seconds(self):
        return self.disk_watching_seconds + self.session_watching_seconds

    def _refresh_counts(self):
        log_count = count_approvals_log()
        lifetime = log_count + read_int_file(LIFETIME_PATH)
        session = max(0, log_count - self.session_baseline)
        clicks_saved = lifetime * SEC_PER_APPROVAL
        watching = self._total_watching_seconds()
        total_saved = clicks_saved + watching
        self.session_item.title = f"Approvals (session): {session}"
        self.lifetime_item.title = f"Approvals (lifetime): {lifetime}"
        self.watching_time_item.title = f"Watching time: {format_duration(watching)}"
        self.time_clicks_item.title = f"Saved (clicks): {format_duration(clicks_saved)}"
        self.time_total_item.title = f"Total time saved: {format_duration(total_saved)}"

    def _tick(self, _):
        if self.watching:
            self.session_watching_seconds += 1
            self.ticks_since_flush += 1
            if self.ticks_since_flush >= FLUSH_EVERY_TICKS:
                self._flush_watching_to_disk()
        self._refresh_counts()


if __name__ == "__main__":
    log("=" * 50)
    log("Process start")
    try:
        AutoYesApp().run()
    except Exception as e:
        log(f"Fatal: {e}\n{traceback.format_exc()}")
        raise
