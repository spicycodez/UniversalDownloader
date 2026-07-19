import time
from typing import Optional


def human_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num < 1024:
            return f"{num:.2f} {unit}"
        num /= 1024
    return f"{num:.2f} PB"


def build_progress_text(stage: str, d: dict) -> str:
    """Turns a yt-dlp progress_hooks dict into a single premium progress message."""
    if d.get("status") != "downloading":
        return stage

    downloaded = d.get("downloaded_bytes", 0) or 0
    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
    speed = d.get("speed") or 0
    eta = d.get("eta")

    percent = (downloaded / total * 100) if total else 0
    bar_len = 12
    filled = int(bar_len * percent / 100)
    bar = "█" * filled + "░" * (bar_len - filled)

    eta_text = f"{eta}s" if eta is not None else "—"

    return (
        f"📥 Downloading...\n\n"
        f"[{bar}] {percent:.1f}%\n"
        f"⚡ {human_size(speed)}/s\n"
        f"📦 {human_size(downloaded)} / {human_size(total)}\n"
        f"⏳ ETA: {eta_text}"
    )


class ProgressThrottle:
    """Caps how often a Telegram message is edited (Telegram rate-limits edits)."""

    def __init__(self, interval: float = 2.0):
        self.interval = interval
        self._last = 0.0

    def ready(self) -> bool:
        now = time.time()
        if now - self._last >= self.interval:
            self._last = now
            return True
        return False
