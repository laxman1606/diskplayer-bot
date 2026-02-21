import os
import asyncio
import urllib.parse
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

PUBLIC_URL = os.environ.get("PUBLIC_URL")
PORT = int(os.environ.get("PORT", 10000))

app = Client(
    "DiskPlayerBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

routes = web.RouteTableDef()

@routes.get("/")
async def home(request):
    return web.Response(text="Bot Running ✅")

@routes.get("/stream/{chat_id}/{message_id}")
async def stream(request):
    chat_id = int(request.match_info["chat_id"])
    message_id = int(request.match_info["message_id"])

    message = await app.get_messages(chat_id, message_id)
    media = message.video or message.document or message.audio

    if not media:
        return web.Response(text="No Media", status=404)

    file_name = media.file_name or "video.mp4"
    mime_type = media.mime_type or "video/mp4"
    file_size = media.file_size or 0

    async def file_sender():
        async for chunk in app.stream_media(message):
            yield chunk

    return web.Response(
        body=file_sender(),
        headers={
            "Content-Type": mime_type,
            "Content-Disposition": f'inline; filename="{file_name}"',
            "Content-Length": str(file_size),
            "Access-Control-Allow-Origin": "*"
        }
    )

@app.on_message(filters.private & (filters.video | filters.document | filters.audio))
async def media_handler(client, message):

    chat_id = message.chat.id
    msg_id = message.id

    stream_link = f"{PUBLIC_URL}/stream/{chat_id}/{msg_id}"
    app_link = f"{PUBLIC_URL}/play?url={urllib.parse.quote(stream_link)}"

    await message.reply(
        "🎬 Your Video is Ready!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Watch in App", url=app_link)]
        ])
    )

async def main():
    web_app = web.Application()
    web_app.add_routes(routes)

    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await app.start()
    print("Bot Running 🚀")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())