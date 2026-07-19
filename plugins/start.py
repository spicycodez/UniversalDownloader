from pyrogram import Client, filters
from pyrogram.types import Message


@Client.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply_text(
        "👋 **Universal Downloader Bot**\n\n"
        "Just paste a supported link — no commands needed:\n\n"
        "YouTube • YouTube Shorts • Instagram (Posts/Reels/Stories) • "
        "Facebook • X (Twitter) • Threads • Reddit • Pinterest • "
        "Vimeo • Dailymotion • Twitch Clips • Streamable • SoundCloud • TikTok\n\n"
        "I'll detect the platform automatically and send the media back "
        "in the original quality."
    )
