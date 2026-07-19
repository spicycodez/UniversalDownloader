import asyncio
import os

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.enums import ChatType

from core.detector import extract_url, detect_platform
from core.downloader import download_media
from core.uploader import upload_media
from utils.progress import build_progress_text, ProgressThrottle
from utils.caption import build_caption
from utils.cleanup import safe_delete
from utils.logger import logger
from config import LOG_GROUP, MAX_FILE_SIZE, MAX_CONCURRENT_DOWNLOADS

# Prevents the same URL being downloaded twice in parallel (e.g. spammed link)
_active_urls: set[str] = set()
_download_semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)


@Client.on_message(filters.text & filters.incoming, group=1)
async def universal_downloader(client: Client, message: Message):
    text = message.text or ""
    url = extract_url(text)
    if not url:
        return

    platform = detect_platform(url)

    if not platform:
        if message.chat.type == ChatType.PRIVATE:
            await message.reply_text(
                "❌ **Unsupported Link**\n\n"
                "This URL is not supported.\n"
                "Please send a valid supported platform link."
            )
        return  # groups: ignore completely, no reply, no spam

    if url in _active_urls:
        return  # duplicate download already in flight

    _active_urls.add(url)
    status_msg = await message.reply_text(f"🔍 Detecting Platform...\n\n🌐 {platform}")
    file_path = None
    thumb_path = None

    try:
        async with _download_semaphore:
            await status_msg.edit_text(f"⚡ Fetching Information...\n\n🌐 {platform}")

            throttle = ProgressThrottle(interval=2.5)

            async def on_progress(d: dict):
                if not throttle.ready():
                    return
                try:
                    await status_msg.edit_text(build_progress_text("📥 Downloading...", d))
                except Exception:
                    pass

            result = await download_media(url, progress_callback=on_progress)
            file_path = result.file_path
            thumb_path = result.thumb_path
            info = result.info

        if not file_path or not os.path.exists(file_path):
            raise FileNotFoundError("Download finished but output file is missing.")

        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            await status_msg.edit_text(
                f"❌ **File Too Large**\n\n"
                f"{file_size / (1024 ** 3):.2f} GB exceeds the "
                f"{MAX_FILE_SIZE / (1024 ** 3):.0f} GB limit for this bot."
            )
            return

        await status_msg.edit_text(f"📤 Uploading...\n\n🌐 {platform}")

        bot_username = client.me.username if client.me else "bot"
        caption = build_caption(bot_username, platform, info, url, file_size)

        await upload_media(
            client=client,
            chat_id=message.chat.id,
            file_path=file_path,
            caption=caption,
            thumb=thumb_path,
            progress_message=status_msg,
            reply_to=message.id,
        )

        await status_msg.edit_text("✅ Completed Successfully")

        if LOG_GROUP:
            try:
                await client.send_message(
                    LOG_GROUP,
                    "📊 **Download Log**\n"
                    f"🌐 Platform: {platform}\n"
                    f"👤 User: `{message.from_user.id if message.from_user else 'unknown'}`\n"
                    f"💬 Chat: `{message.chat.id}`\n"
                    f"📦 Size: {file_size / (1024 ** 2):.1f} MB",
                )
            except Exception as e:
                logger.warning(f"Failed to send log: {e}")

    except FloodWait as e:
        logger.warning(f"FloodWait hit, sleeping {e.value}s")
        await asyncio.sleep(e.value)
        try:
            await status_msg.edit_text("⏳ Rate limited by Telegram, please resend the link shortly.")
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Failed processing {url}: {e}")
        try:
            await status_msg.edit_text(
                "❌ **Download Failed**\n\n"
                "This link could not be processed. It may be private, deleted, "
                "geo-restricted, age-restricted, or currently rate-limited by the platform."
            )
        except Exception:
            pass

    finally:
        _active_urls.discard(url)
        safe_delete(file_path, thumb_path)
