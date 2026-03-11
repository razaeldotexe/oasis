# cogs/auto_voice.py

import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from core.logger_config import logger

DATA_FILE = "data/auto_voice.json"

class AutoVoice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = []
        self.master_channel_id = None
        self.category_id = None
        self._load_data()

    def _load_data(self):
        """Memuat konfigurasi Auto-Voice dari JSON."""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.master_channel_id = data.get("master_channel_id")
                self.category_id = data.get("category_id")
        else:
            self.master_channel_id = None
            self.category_id = None

    def _save_data(self):
        """Menyimpan konfigurasi Auto-Voice ke JSON."""
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump({
                "master_channel_id": self.master_channel_id,
                "category_id": self.category_id
            }, f, indent=4)

    def setup_auto_voice(self, guild, category_id, master_id):
        self.category_id = category_id
        self.master_channel_id = master_id
        self._save_data()


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Prevent if config is missing
        if not self.master_channel_id:
            return

        # 1. LOGIKA SAAT USER MASUK KE MASTER CHANNEL
        if after.channel and after.channel.id == self.master_channel_id:
            guild = member.guild
            
            # Tentukan kategori
            category = None
            if self.category_id:
                category = guild.get_channel(self.category_id)
            
            # Jika tidak ada kategori spesifik yang di-set di env, gunakan kategori dari master channel
            if not category and after.channel.category:
                category = after.channel.category

            channel_name = f"🔊 {member.display_name}'s Room"
            
            try:
                # Bikin room sementara
                new_channel = await guild.create_voice_channel(
                    name=channel_name,
                    category=category
                )
                
                # Simpan id nya
                self.temp_channels.append(new_channel.id)
                # Pindahkan user langsung ke room baru
                await member.move_to(new_channel)
                logger.info(f"AutoVoice: Dibuat {channel_name} untuk {member.display_name}")
            except discord.Forbidden:
                logger.error("AutoVoice: Bot tidak memiliki izin untuk membuat/memindahkan user ke Voice Channel.")
            except discord.HTTPException as e:
                logger.error(f"AutoVoice: Gagal membuat channel - {e}")

        # 2. LOGIKA SAAT USER KELUAR DARI CHANNEL SEMENTARA (cleanup)
        if before.channel and before.channel.id in self.temp_channels:
            if len(before.channel.members) == 0:
                try:
                    await before.channel.delete()
                    self.temp_channels.remove(before.channel.id)
                    logger.info(f"AutoVoice: Dihapus {before.channel.name} karena kosong")
                except discord.NotFound:
                    # Channel mungkin dihapus manual oleh admin
                    if before.channel.id in self.temp_channels:
                        self.temp_channels.remove(before.channel.id)
                except Exception as e:
                    logger.error(f"AutoVoice: Gagal menghapus channel - {e}")

async def setup(bot):
    await bot.add_cog(AutoVoice(bot))
