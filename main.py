import asyncio

from pyrogram import Client, idle

from config import API_ID, API_HASH, BOT_TOKEN
from utils.logger import logger
from utils.auto_updater import auto_update_loop

app = Client(
    "universal_downloader_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="plugins"),
)


async def main():
    await app.start()
    logger.info("Universal Downloader Bot started.")

    # Runs in the background for the whole life of the process — checks
    # PyPI for a newer yt-dlp release, upgrades it, and restarts the
    # process (in place) to load it. See utils/auto_updater.py.
    asyncio.create_task(auto_update_loop(app))

    await idle()

    await app.stop()
    logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
