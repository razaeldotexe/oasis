import discord
from discord.ext import commands
from core.logger_config import logger
import os

class OasisBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self._synced = False

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
        if not self._synced:
            # Hapus global commands lama agar tidak duplikat
            self.tree.clear_commands(guild=None)
            await self.tree.sync()

            # Sync ke setiap guild (instan)
            for guild in self.guilds:
                try:
                    self.tree.copy_global_to(guild=guild)
                    synced = await self.tree.sync(guild=guild)
                    logger.info(f"Synced {len(synced)} commands to {guild.name}")
                except Exception as e:
                    logger.error(f"Failed to sync to {guild.name}: {e}")

            self._synced = True

        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info("Sistem siap!")


