import os
import asyncio
import logging
import urllib.parse
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------------- CONFIG ----------------
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")
PORT = int(os.environ.get("PORT", 8080))
HOST = "0.0.0.0"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not API_ID or not API_HASH or not BOT_TOKEN or not PUBLIC_URL:
    print("❌ Missing Environment Variables")
    exit(1)

# ---------------- TELEGRAM BOT ----------------
bot = Client(
    "DiskWalaSession",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ---------------- WEB SERVER ----------------
routes = web.RouteTableDef()

@routes.get("/")
async def home(request):
    return web.Response(text="✅ Bot Running Successfully")

@routes.get("/stream/{chat_id}/{message_id}")
async def stream_handler(request):
    try:
        chat_id = int(request.match_info["chat_id"])
        message_id = int(request.match_info["message_id"])

        message = await bot.get_messages(chat_id, message_id)
        media = message.video or message.document or message.audio

        if not media:
            return web.Response(status=404, text="No Media Found")

        file_name = getattr(media, "file_name", "video.mp4") or "video.mp4"
        mime_type = getattr(media, "mime_type", "video/mp4") or "video/mp4"

        async def file_stream():
            async for chunk in bot.stream_media(message):
                yield chunk

        return web.Response(
            body=file_stream(),
            headers={
                "Content-Type": mime_type,
                "Content-Disposition": f'inline; filename="{file_name}"',
                "Access-Control-Allow-Origin": "*"
            }
        )

    except Exception as e:
        logger.error(e)
        return web.Response(status=500, text="Server Error")

# ---------------- BOT COMMAND ----------------
@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("👋 Send me a video and I will generate App Play Link.")

# ---------------- MEDIA HANDLER ----------------
@bot.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def media_handler(client, message):
    try:
        chat_id = message.chat.id
        msg_id = message.id

        media = message.video or message.document or message.audio
        if not media:
            return

        file_name = getattr(media, "file_name", "file") or "file"

        # Direct Stream Link
        stream_link = f"{PUBLIC_URL}/stream/{chat_id}/{msg_id}"

        # Android Deep Link (IMPORTANT: same scheme in AndroidManifest)
        app_link = f"livebox://play?url={urllib.parse.quote(stream_link)}"

        await message.reply_text(
            f"✅ Ready To Play\n\n📂 {file_name}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Open in App", url=app_link)]
            ])
        )

    except Exception as e:
        logger.error(e)

# ---------------- RUN SERVER ----------------
async def main():
    web_app = web.Application(client_max_size=1024**3)
    web_app.add_routes(routes)

    runner = web.AppRunner(web_app)
    await runner.setup()

    site = web.TCPSite(runner, HOST, PORT)
    await site.start()

    await bot.start()
    logger.info("✅ Bot Started")

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
