import asyncio
import os
import subprocess
import sys
from typing import Optional

import aiohttp
import yt_dlp

from config import OWNER_ID, AUTO_UPDATE_YTDLP, YTDLP_CHECK_INTERVAL
from utils.logger import logger


async def _get_latest_version() -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://pypi.org/pypi/yt-dlp/json", timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                return data["info"]["version"]
    except Exception as e:
        logger.warning(f"yt-dlp version check failed: {e}")
        return None


def _pip_upgrade_yt_dlp() -> bool:
    """Blocking — always call via run_in_executor."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--no-cache-dir", "yt-dlp"],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode == 0:
            logger.info("yt-dlp upgraded successfully.")
            return True
        logger.error(f"yt-dlp upgrade failed: {result.stderr.strip()[:500]}")
        return False
    except Exception as e:
        logger.error(f"yt-dlp upgrade crashed: {e}")
        return False


async def check_and_update(client=None) -> bool:
    """Checks PyPI for a newer yt-dlp release and upgrades if found.

    Returns True if an upgrade was installed (the process must restart
    for the new version to actually be loaded — Python caches the
    imported module in memory).
    """
    current = yt_dlp.version.__version__
    latest = await _get_latest_version()
    if not latest or latest == current:
        return False

    logger.info(f"New yt-dlp version available: {current} -> {latest}. Upgrading...")
    loop = asyncio.get_event_loop()
    success = await loop.run_in_executor(None, _pip_upgrade_yt_dlp)

    if success and client is not None and OWNER_ID:
        try:
            await client.send_message(
                OWNER_ID,
                f"🔄 **yt-dlp auto-updated**\n`{current}` → `{latest}`\nRestarting to apply the update...",
            )
        except Exception:
            pass

    return success


async def auto_update_loop(client):
    """Background task: checks once shortly after startup, then on a
    fixed interval for as long as the process lives. No-op if
    AUTO_UPDATE_YTDLP is disabled in config."""
    if not AUTO_UPDATE_YTDLP:
        logger.info("yt-dlp auto-update is disabled (AUTO_UPDATE_YTDLP=false).")
        return

    await asyncio.sleep(30)  # let the bot finish starting first
    while True:
        try:
            upgraded = await check_and_update(client)
            if upgraded:
                logger.info("Restarting process to load the updated yt-dlp...")
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            logger.error(f"Auto-update loop error: {e}")
        await asyncio.sleep(YTDLP_CHECK_INTERVAL)
