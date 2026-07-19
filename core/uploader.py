import os
import time
from typing import Optional

from pyrogram.enums import ParseMode
from utils.progress import human_size

VIDEO_EXT = {".mp4", ".mkv", ".webm", ".mov"}
AUDIO_EXT = {".mp3", ".m4a", ".ogg", ".flac", ".wav"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def guess_media_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext in VIDEO_EXT:
        return "video"
    if ext in AUDIO_EXT:
        return "audio"
    if ext in IMAGE_EXT:
        return "photo"
    return "document"


async def upload_media(
    client,
    chat_id: int,
    file_path: str,
    caption: str,
    thumb: Optional[str],
    progress_message,
    reply_to: Optional[int] = None,
):
    media_type = guess_media_type(file_path)
    last = {"t": 0.0}

    async def on_progress(current: int, total: int):
        now = time.time()
        if now - last["t"] < 2 and current != total:
            return
        last["t"] = now
        percent = (current / total * 100) if total else 0
        try:
            await progress_message.edit_text(
                f"📤 Uploading...\n\n"
                f"{percent:.1f}% ({human_size(current)} / {human_size(total)})"
            )
        except Exception:
            pass  # message may already say "Completed" from a race, ignore

    common = dict(
        chat_id=chat_id,
        caption=caption,
        parse_mode=ParseMode.MARKDOWN,
        reply_to_message_id=reply_to,
    )

    if media_type == "video":
        return await client.send_video(
            video=file_path,
            thumb=thumb,
            supports_streaming=True,
            file_name=os.path.basename(file_path),
            progress=on_progress,
            **common,
        )
    if media_type == "audio":
        return await client.send_audio(
            audio=file_path,
            thumb=thumb,
            file_name=os.path.basename(file_path),
            progress=on_progress,
            **common,
        )
    if media_type == "photo":
        return await client.send_photo(photo=file_path, **common)

    return await client.send_document(
        document=file_path,
        thumb=thumb,
        file_name=os.path.basename(file_path),
        progress=on_progress,
        **common,
    )
