from typing import Optional
from utils.progress import human_size

ICONS = {
    "Platform": "🌐",
    "Title": "🎬",
    "Creator": "👤",
    "Quality": "🎞",
    "Size": "📦",
    "Duration": "⏱",
    "Source": "🔗",
}


def format_duration(seconds) -> Optional[str]:
    if not seconds:
        return None
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def build_caption(bot_username: str, platform: str, info: dict, url: str, file_size: int) -> str:
    fields = {
        "Platform": platform,
        "Title": info.get("title"),
        "Creator": info.get("uploader") or info.get("channel") or info.get("uploader_id"),
        "Quality": "Original",
        "Size": human_size(file_size) if file_size else None,
        "Duration": format_duration(info.get("duration")),
        "Source": url,
    }

    lines = ["📥 **Download Completed**", "━━━━━━━━━━━━━━━━━━"]
    for label, value in fields.items():
        if not value:
            continue  # never show empty fields
        icon = ICONS.get(label, "•")
        lines.append(f"{icon} **{label}** : {value}")
    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append(f"Powered by @{bot_username}")
    return "\n".join(lines)
