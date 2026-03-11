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
        try:
            await self.tree.sync()
            logger.info(f"Slash commands synced for {self.user}")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
            
        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info("Sistem siap!")
