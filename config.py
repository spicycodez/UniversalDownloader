import os
from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LOG_GROUP = int(os.getenv("LOG_GROUP")) if os.getenv("LOG_GROUP") else None

DOWNLOAD_PATH = os.getenv("DOWNLOAD_PATH", "downloads")
TEMP_PATH = os.getenv("TEMP_PATH", "temp")

# 4 GB default cap — raise if your bot/account has Telegram Premium upload limits
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(4 * 1024 * 1024 * 1024)))

# Optional: path to a Netscape-format cookies.txt for platforms that need login
# (private posts you have access to, age-restricted content you're allowed to view, etc.)
COOKIES_FILE = os.getenv("COOKIES_FILE", "")

# Optional outbound proxy, e.g. "http://user:pass@host:port"
PROXY_URL = os.getenv("PROXY_URL", "")

MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "3"))

# yt-dlp self-update — checks PyPI periodically, upgrades in-place, and
# restarts the process to load the new version. Set to "false" to disable.
AUTO_UPDATE_YTDLP = os.getenv("AUTO_UPDATE_YTDLP", "true").lower() != "false"
YTDLP_CHECK_INTERVAL = int(os.getenv("YTDLP_CHECK_INTERVAL", str(24 * 60 * 60)))  # seconds, default 24h

os.makedirs(DOWNLOAD_PATH, exist_ok=True)
os.makedirs(TEMP_PATH, exist_ok=True)
os.makedirs("logs", exist_ok=True)
