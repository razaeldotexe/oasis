import discord
from discord import app_commands
from discord.ext import commands
import json
import os
import re
import time
from collections import defaultdict
import asyncio

from core.logger_config import logger
from utils.colors import Oasis

AUTOMOD_DATA_FILE = "data/automod.json"


class Automod(commands.Cog):
    """Cog untuk moderasi otomatis server oasis."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = self.load_config()
        self.spam_tracker = defaultdict(list)

        # Buat folder data jika belum ada
        if not os.path.exists("data"):
            os.makedirs("data")

    def load_config(self):
        if os.path.exists(AUTOMOD_DATA_FILE):
            with open(AUTOMOD_DATA_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def save_config(self):
        with open(AUTOMOD_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_guild_config(self, guild_id: int):
        guild_str = str(guild_id)
        if guild_str not in self.config:
            self.config[guild_str] = {
                "modules": {
                    "spam": True,
                    "link": False,
                    "badwords": True,
                    "mention": True,
                    "caps": True,
                },
                "badwords": [
                    "anjing",
                    "bangsat",
                    "kontol",
                    "memek",
                    "entot",
                    "ngentot",
                ],
                "whitelist_channels": [],
                "log_channel_id": None,
            }
            self.save_config()
        return self.config[guild_str]

    async def _handle_violation(self, message: discord.Message, reason: str):
        try:
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                return

            await message.delete()
            warn_msg = await message.channel.send(
                f"⚠️ {message.author.mention}, pesan Anda dihapus karena: **{reason}**."
            )

            # Log violation
            guild_config = self.get_guild_config(message.guild.id)
            log_channel_id = guild_config.get("log_channel_id")
            if log_channel_id:
                log_channel = message.guild.get_channel(log_channel_id)
                if log_channel:
                    embed = discord.Embed(
                        title="🚧 Pelanggaran Automod", color=discord.Color.red()
                    )
                    embed.add_field(
                        name="User",
                        value=f"{message.author} ({message.author.id})",
                        inline=False,
                    )
                    embed.add_field(
                        name="Channel", value=message.channel.mention, inline=False
                    )
                    embed.add_field(name="Alasan", value=reason, inline=False)
                    embed.add_field(
                        name="Isi Pesan",
                        value=message.content[:1024] or "*(Tidak ada teks)*",
                        inline=False,
                    )
                    await log_channel.send(embed=embed)

            await asyncio.sleep(5)
            await warn_msg.delete()
        except Exception as e:
            logger.error(f"Error handling automod violation: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check manage messages permission (moderator bypass)
        if message.channel.permissions_for(message.author).manage_messages:
            return

        guild_config = self.get_guild_config(message.guild.id)

        # Check channel whitelist
        if message.channel.id in guild_config.get("whitelist_channels", []):
            return

        modules = guild_config.get("modules", {})

        # 1. Anti-spam: 5 pesan dalam 5 detik
        if modules.get("spam", True):
            user_id = message.author.id
            curr_time = time.time()
            self.spam_tracker[user_id].append(curr_time)

            # Hapus history yang lebih lama dari 5 detik
            self.spam_tracker[user_id] = [
                t for t in self.spam_tracker[user_id] if curr_time - t <= 5
            ]

            if len(self.spam_tracker[user_id]) > 5:
                await self._handle_violation(message, "Spamming")
                self.spam_tracker[user_id] = []  # Reset tracker
                return

        # 2. Anti-badwords
        if modules.get("badwords", True):
            badwords = guild_config.get("badwords", [])
            content_lower = message.content.lower()
            if any(badword in content_lower for badword in badwords):
                await self._handle_violation(message, "Mengandung kata terlarang")
                return

        # 3. Anti-link
        if modules.get("link", False):
            url_regex = r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            if re.search(url_regex, message.content):
                await self._handle_violation(
                    message, "Mengirim link tidak diizinkan di channel ini"
                )
                return

        # 4. Anti-mention (> 5 mentions)
        if modules.get("mention", True):
            if len(message.mentions) > 5:
                await self._handle_violation(message, "Terlalu banyak mention")
                return

        # 5. Anti-caps (Lebih dari 70% huruf besar jika panjang pesan > 10)
        if modules.get("caps", True) and len(message.content) > 10:
            alpha_chars = [c for c in message.content if c.isalpha()]
            if alpha_chars:
                upper_chars = sum(1 for c in alpha_chars if c.isupper())
                if upper_chars / len(alpha_chars) > 0.7:
                    await self._handle_violation(
                        message, "Terlalu banyak huruf kapital"
                    )
                    return

    # --- Slash Commands Group ---
    automod = app_commands.Group(
        name="automod",
        description="Konfigurasi modul Automod",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    @automod.command(
        name="toggle", description="Nyalakan atau matikan modul automod tertentu"
    )
    @app_commands.choices(
        module=[
            app_commands.Choice(name="Anti-Spam", value="spam"),
            app_commands.Choice(name="Anti-Link", value="link"),
            app_commands.Choice(name="Anti-Badwords", value="badwords"),
            app_commands.Choice(name="Anti-Mention", value="mention"),
            app_commands.Choice(name="Anti-Caps", value="caps"),
        ]
    )
    async def toggle(
        self,
        interaction: discord.Interaction,
        module: app_commands.Choice[str],
        state: bool,
    ):
        guild_config = self.get_guild_config(interaction.guild_id)
        guild_config["modules"][module.value] = state
        self.save_config()

        status = "Aktif" if state else "Nonaktif"
        await interaction.response.send_message(
            f"✅ Modul **{module.name}** sekarang **{status}**.", ephemeral=True
        )

    @automod.command(name="badword_add", description="Tambahkan kata terlarang")
    async def badword_add(self, interaction: discord.Interaction, word: str):
        guild_config = self.get_guild_config(interaction.guild_id)
        word = word.lower()
        if word not in guild_config["badwords"]:
            guild_config["badwords"].append(word)
            self.save_config()
            await interaction.response.send_message(
                f"✅ `{word}` ditambahkan ke daftar badwords.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ `{word}` sudah ada di daftar badwords.", ephemeral=True
            )

    @automod.command(name="badword_remove", description="Hapus kata terlarang")
    async def badword_remove(self, interaction: discord.Interaction, word: str):
        guild_config = self.get_guild_config(interaction.guild_id)
        word = word.lower()
        if word in guild_config["badwords"]:
            guild_config["badwords"].remove(word)
            self.save_config()
            await interaction.response.send_message(
                f"✅ `{word}` dihapus dari daftar badwords.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"⚠️ `{word}` tidak ditemukan di daftar badwords.", ephemeral=True
            )

    @automod.command(
        name="whitelist_channel",
        description="Tambah/Hapus channel dari whitelist automod",
    )
    async def whitelist_channel(
        self, interaction: discord.Interaction, channel: discord.TextChannel
    ):
        guild_config = self.get_guild_config(interaction.guild_id)
        if channel.id in guild_config["whitelist_channels"]:
            guild_config["whitelist_channels"].remove(channel.id)
            self.save_config()
            await interaction.response.send_message(
                f"✅ {channel.mention} dilepas dari whitelist.", ephemeral=True
            )
        else:
            guild_config["whitelist_channels"].append(channel.id)
            self.save_config()
            await interaction.response.send_message(
                f"✅ {channel.mention} dimasukkan ke whitelist.", ephemeral=True
            )

    @automod.command(
        name="set_log",
        description="Pilih channel untuk logging pelanggaran (kosongkan untuk mematikan log)",
    )
    async def set_log(
        self, interaction: discord.Interaction, channel: discord.TextChannel = None
    ):
        guild_config = self.get_guild_config(interaction.guild_id)
        if channel:
            guild_config["log_channel_id"] = channel.id
            self.save_config()
            await interaction.response.send_message(
                f"✅ Channel log diatur ke {channel.mention}.", ephemeral=True
            )
        else:
            guild_config["log_channel_id"] = None
            self.save_config()
            await interaction.response.send_message(
                f"✅ Logging pelanggaran dinonaktifkan.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Automod(bot))
