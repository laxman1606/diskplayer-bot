import os
import asyncio
import logging
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO)

API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL")
PORT = int(os.environ.get("PORT", 8080))

if not API_ID or not API_HASH or not BOT_TOKEN:
    print("❌ Missing Environment Variables!")
    exit(1)

bot = Client(
    "DiskWalaBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

routes = web.RouteTableDef()

@routes.get("/")
async def home(request):
    return web.Response(text="✅ Bot Running Successfully")

@routes.get("/stream/{chat_id}/{message_id}")
async def stream(request):
    chat_id = int(request.match_info["chat_id"])
    message_id = int(request.match_info["message_id"])

    message = await bot.get_messages(chat_id, message_id)
    media = message.video or message.document or message.audio

    if not media:
        return web.Response(text="No Media", status=404)

    async def generator():
        async for chunk in bot.stream_media(message):
            yield chunk

    return web.Response(
        body=generator(),
        headers={"Content-Type": media.mime_type or "video/mp4"}
    )

@bot.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def media_handler(client, message):
    chat_id = message.chat.id
    msg_id = message.id

    link = f"{PUBLIC_URL}/stream/{chat_id}/{msg_id}"

    await message.reply_text(
        "✅ Ready To Stream",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("▶️ Play Video", url=link)]]
        )
    )

async def main():
    app = web.Application(client_max_size=1024**3)
    app.add_routes(routes)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await bot.start()
    print("✅ Bot Started")

    await asyncio.Event().wait()

asyncio.run(main())
