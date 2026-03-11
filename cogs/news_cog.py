import os
import asyncio
import discord
from discord.ext import commands, tasks
from core.logger_config import logger

from utils.api_fetcher import fetch_latest_news
from utils.embed_builder import build_news_embed
from utils.dedup_store import DedupStore

# Load konfigurasi dari env
# Nilai default dipasang untuk menghindari error saat dev
try:
    NEWS_INTERVAL_MINUTES = int(os.getenv("NEWS_INTERVAL_MINUTES", "15"))
except ValueError:
    NEWS_INTERVAL_MINUTES = 15

try:
    MAX_NEWS_PER_BATCH = int(os.getenv("MAX_NEWS_PER_BATCH", "5"))
except ValueError:
    MAX_NEWS_PER_BATCH = 5

class NewsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Path disesuaikan agar tersimpan di direktori data pada root proyek (c:\Users\Administrator\oasis\data)
        self.store = DedupStore(os.path.join("data", "posted_news.json"))
        self.post_news.change_interval(minutes=NEWS_INTERVAL_MINUTES)
        self.post_news.start()

    def cog_unload(self):
        self.post_news.cancel()

    @tasks.loop(minutes=15) # Default, akan ditimpa di __init__
    async def post_news(self):
        news_channel_str = os.getenv("NEWS_CHANNEL_ID")
        if not news_channel_str:
            logger.warning("NEWS_CHANNEL_ID tidak diatur di .env. Mengabaikan auto-post berita.")
            return

        try:
            channel_id = int(news_channel_str)
        except ValueError:
            logger.error(f"NEWS_CHANNEL_ID tidak valid: {news_channel_str}")
            return
            
        channel = self.bot.get_channel(channel_id)
        if not channel:
            # Channel belum tercache, coba fetch
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception as e:
                logger.error(f"Channel berita tidak ditemukan atau tidak ada akses: {e}")
                return

        articles = await fetch_latest_news()
        if not articles:
            return  # API sedang down atau mengembalikan kosong
            
        # Filter berita yang belum diposting
        new_articles = [a for a in articles if not self.store.is_posted(a.get("link", ""))]

        # Batasi jumlah posting per interval agar tidak spam
        for article in new_articles[:MAX_NEWS_PER_BATCH]:
            try:
                embed = build_news_embed(article)
                await channel.send(embed=embed)
                self.store.mark_posted(article.get("link", ""))
                logger.info(f"Berhasil memposting berita: {article.get('title', 'Tanpa Judul')}")
                # Jeda 2 detik antar posting untuk menghindari rate-limit Discord
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Gagal memposting berita {article.get('title', '')}: {e}")

    @post_news.before_loop
    async def before_post_news(self):
        # Tunggu bot siap sebelum mulai loop
        await self.bot.wait_until_ready()
        logger.info("NewsCog loop is starting...")

async def setup(bot):
    await bot.add_cog(NewsCog(bot))
