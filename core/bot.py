import discord
from discord.ext import commands
from core.logger_config import logger
import os

class OasisBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Memuat Cogs secara otomatis
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                cog_name = f'cogs.{filename[:-3]}'
                if cog_name not in self.extensions:
                    try:
                        await self.load_extension(cog_name)
                        logger.info(f'Loaded extension: {filename}')
                    except Exception as e:
                        logger.error(f'Failed to load extension {filename}: {e}')

    async def on_ready(self):
        # Sync slash commands ke setiap guild (instan, tidak perlu tunggu 1 jam)
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                synced = await self.tree.sync(guild=guild)
                logger.info(f"Synced {len(synced)} commands to {guild.name} ({guild.id})")
            except Exception as e:
                logger.error(f"Failed to sync commands to {guild.name}: {e}")

        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info("Sistem siap!")

