import discord
from discord.ext import commands
from core.logger_config import logger
import os
import asyncio
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from bot_status_server import start_status_server


class OasisBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self._synced = False

    async def setup_hook(self):
        # Registrasi persistent views untuk ticket system
        from views.ticket_button import TicketPanelView
        from views.ticket_controls import TicketControlsView

        self.add_view(TicketPanelView())
        self.add_view(TicketControlsView())

        # Inisialisasi database tiket
        from utils.db import init_db

        await init_db()

        # Memuat cogs secara otomatis menggunakan path absolut
        cogs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cogs'))
        for filename in os.listdir(cogs_path):
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
            # Step 1: Copy command dari global tree ke setiap guild, lalu sync (instan)
            for guild in self.guilds:
                try:
                    self.tree.copy_global_to(guild=guild)
                    synced = await self.tree.sync(guild=guild)
                    logger.info(f"Synced {len(synced)} commands to {guild.name}")
                except Exception as e:
                    logger.error(f"Failed to sync to {guild.name}: {e}")

            # Step 2: Hapus global commands dari Discord agar tidak duplikat
            # (semua command sudah live di guild level)
            self.tree.clear_commands(guild=None)
            await self.tree.sync()

            self._synced = True

        logger.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        logger.info("Sistem siap!")
        asyncio.create_task(start_status_server(self))
