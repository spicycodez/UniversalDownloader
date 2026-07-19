import asyncio
import os
import time
import uuid
from typing import Callable, Optional

import yt_dlp

from config import DOWNLOAD_PATH, COOKIES_FILE, PROXY_URL
from utils.logger import logger

MEDIA_EXTENSIONS = (".mp4", ".mkv", ".webm", ".mov", ".mp3", ".m4a", ".ogg", ".jpg", ".jpeg", ".png", ".webp")


class DownloadResult:
    __slots__ = ("file_path", "thumb_path", "info")

    def __init__(self, file_path: str, thumb_path: Optional[str], info: dict):
        self.file_path = file_path
        self.thumb_path = thumb_path
        self.info = info


def _build_ydl_opts(out_template: str, progress_hook: Callable) -> dict:
    opts = {
        "outtmpl": out_template,
        # Best available video+audio, merged; falls back to best single stream
        # (e.g. audio-only for SoundCloud) automatically.
        "format": "bestvideo*+bestaudio/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [progress_hook],
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "writethumbnail": True,
        "socket_timeout": 30,
    }
    if COOKIES_FILE and os.path.exists(COOKIES_FILE):
        opts["cookiefile"] = COOKIES_FILE
    if PROXY_URL:
        opts["proxy"] = PROXY_URL
    return opts


def _find_output_file(base_no_ext: str) -> Optional[str]:
    for ext in MEDIA_EXTENSIONS:
        candidate = base_no_ext + ext
        if os.path.exists(candidate):
            return candidate
    return None


async def download_media(url: str, progress_callback: Optional[Callable] = None) -> DownloadResult:
    """
    Downloads media from `url` with yt-dlp inside a thread executor, so the
    Pyrogram event loop is never blocked by yt-dlp's synchronous I/O.

    `progress_callback` is an async function accepting the raw yt-dlp
    progress dict; it's scheduled back onto the event loop from the
    worker thread.
    """
    loop = asyncio.get_event_loop()
    job_id = uuid.uuid4().hex[:10]
    out_template = os.path.join(DOWNLOAD_PATH, f"{job_id}_%(title).80s.%(ext)s")

    last_update = {"t": 0.0}

    def hook(d):
        if progress_callback is None:
            return
        now = time.time()
        if d.get("status") == "downloading" and now - last_update["t"] < 1.5:
            return
        last_update["t"] = now
        try:
            asyncio.run_coroutine_threadsafe(progress_callback(d), loop)
        except RuntimeError:
            pass  # loop already closed (e.g. shutdown mid-download)

    def run():
        opts = _build_ydl_opts(out_template, hook)
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if "entries" in info and info["entries"]:
                info = info["entries"][0]

            raw_path = ydl.prepare_filename(info)
            base, _ = os.path.splitext(raw_path)

            file_path = _find_output_file(base) or raw_path
            thumb_path = None
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                candidate = base + ext
                if os.path.exists(candidate) and candidate != file_path:
                    thumb_path = candidate
                    break

            return file_path, thumb_path, info

    try:
        file_path, thumb_path, info = await loop.run_in_executor(None, run)
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"yt-dlp error for {url}: {e}")
        raise

    return DownloadResult(file_path, thumb_path, info)
