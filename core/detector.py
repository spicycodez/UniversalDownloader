import re
from typing import Optional

# Order matters where patterns could overlap — most specific first.
PLATFORM_PATTERNS = {
    "YouTube": re.compile(r"(youtube\.com/(watch|shorts)|youtu\.be/)", re.I),
    "Instagram": re.compile(r"instagram\.com/(p|reel|reels|stories|tv)/", re.I),
    "Threads": re.compile(r"threads\.net", re.I),
    "Twitter": re.compile(r"(twitter\.com|x\.com)/\w+/status/", re.I),
    "Facebook": re.compile(r"(facebook\.com|fb\.watch)/", re.I),
    "Reddit": re.compile(r"reddit\.com/r/\w+/comments/", re.I),
    "Pinterest": re.compile(r"pinterest\.[a-z.]+/pin/", re.I),
    "Snapchat": re.compile(r"snapchat\.com/(t|spotlight)/", re.I),
    "Vimeo": re.compile(r"vimeo\.com/\d+", re.I),
    "Dailymotion": re.compile(r"dailymotion\.com/video/", re.I),
    "Twitch": re.compile(r"(clips\.twitch\.tv/|twitch\.tv/\w+/clip/)", re.I),
    "Streamable": re.compile(r"streamable\.com/", re.I),
    "SoundCloud": re.compile(r"soundcloud\.com/", re.I),
    "TikTok": re.compile(r"tiktok\.com/", re.I),
}

URL_PATTERN = re.compile(r"https?://\S+", re.I)


def extract_url(text: Optional[str]) -> Optional[str]:
    """Pulls the first http(s) URL out of a message, or None."""
    if not text:
        return None
    match = URL_PATTERN.search(text)
    return match.group(0).rstrip(").,") if match else None


def detect_platform(url: str) -> Optional[str]:
    """Returns a friendly platform name, or None if unrecognized.

    None is treated as "unsupported" by the message handler — ignored
    silently in groups, shown as an error in private chats.
    """
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.search(url):
            return platform
    return None
