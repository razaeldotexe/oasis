import asyncio
import time
from datetime import datetime, timezone
from aiohttp import web
import discord

STATUS_PORT = 3001
start_time = time.time()

def create_status_app(bot: discord.Client) -> web.Application:
    async def handle_status(request: web.Request) -> web.Response:
        now = datetime.now(timezone.utc)
        uptime_seconds = int(time.time() - start_time)
        guilds = list(bot.guilds) if bot.is_ready() else []
        total_members = sum(g.member_count or 0 for g in guilds)
        data = {
            "online":         bot.is_ready(),
            "bot_name":       str(bot.user) if bot.user else "Unknown",
            "bot_id":         str(bot.user.id) if bot.user else None,
            "avatar_url":     str(bot.user.display_avatar.url) if bot.user else None,
            "ping_ms":        round(bot.latency * 1000, 2),
            "uptime_seconds": uptime_seconds,
            "guild_count":    len(guilds),
            "total_members":  total_members,
            "timestamp":      now.isoformat(),
        }
        return web.json_response(data, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_health(request: web.Request) -> web.Response:
        return web.Response(text="OK")

    app = web.Application()
    app.router.add_get("/status", handle_status)
    app.router.add_get("/health", handle_health)
    return app

async def start_status_server(bot: discord.Client):
    app = create_status_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", STATUS_PORT)
    await site.start()
    print(f"[StatusServer] Running at http://0.0.0.0:{STATUS_PORT}/status")
