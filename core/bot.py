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
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f'Loaded extension: {filename}')
                except Exception as e:
                    logger.error(f'Failed to load extension {filename}: {e}')
        
        await self.tree.sync()
        logger.info(f"Slash commands synced for {self.user}")

    async def on_ready(self):
        logger.info(f'Bot logged in as {self.user} (ID: {self.user.id})')
        logger.info('Sistem siap!')
