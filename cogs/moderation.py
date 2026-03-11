import discord
from discord import app_commands
from discord.ext import commands
import datetime
import re
from core.logger_config import logger

def text_to_int(text: str) -> int:
    """Konversi teks angka (Indo/Inggris) ke integer (1-100)."""
    mapping = {
        # Indonesia
        'satu': 1, 'dua': 2, 'tiga': 3, 'empat': 4, 'lima': 5, 
        'enam': 6, 'tujuh': 7, 'delapan': 8, 'sembilan': 9, 'sepuluh': 10,
        'dua puluh': 20, 'tiga puluh': 30, 'empat puluh': 40, 'lima puluh': 50,
        'enam puluh': 60, 'tujuh puluh': 70, 'delapan puluh': 80, 'sembilan puluh': 90,
        'seratus': 100,
        # English
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
        'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90,
        'one hundred': 100
    }
    
    # Cek apakah input adalah angka murni
    if text.isdigit():
        return int(text)
    
    # Cek pemetaan teks
    val = mapping.get(text.lower().strip())
    if val:
        return val
        
    # Fallback jika tidak ditemukan (default ke 0 untuk validasi nanti)
    return 0

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timeout", description="Men-timeout user")
    @app_commands.describe(member="User yang akan di-timeout", reason="Alasan")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        duration = datetime.timedelta(minutes=10)
        try:
            await member.timeout(duration, reason=reason)
            embed = discord.Embed(title="Timeout", description=f"**{member}** di-timeout.", color=discord.Color.orange())
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="kick", description="Menendang user")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"**{member}** ditendang.")
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="Mem-ban user")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"**{member}** di-ban.")
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    @app_commands.command(name="lock", description="Mengunci channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        try:
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
            special_role = interaction.guild.get_role(1480002092251742229)
            if special_role:
                await channel.set_permissions(special_role, send_messages=False)
            await interaction.response.send_message(f"🔒 {channel.mention} dikunci.")
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}", ephemeral=True)

    # --- Purge Group Command ---
    purge = app_commands.Group(name="purge", description="Menghapus pesan secara massal dengan berbagai filter", default_permissions=discord.Permissions(manage_messages=True))

    async def do_purge(self, interaction: discord.Interaction, count_input: str, check_func=None):
        try:
            # 1. Selalu defer di awal agar interaksi tidak timeout
            await interaction.response.defer(ephemeral=True)

            # 2. Parsing input
            count = text_to_int(str(count_input))
            if count <= 0:
                await interaction.followup.send("❌ Masukkan jumlah yang valid (1-100).", ephemeral=True)
                return
            
            count = min(count, 100)
            
            # 3. Purge
            channel = interaction.channel
            if channel and hasattr(channel, 'purge'):
                # Pastikan limit adalah integer
                scan_limit = int(count) if check_func is None else 100
                
                logger.info(f"Starting purge: count={count}, scan_limit={scan_limit}, has_check={check_func is not None}")
                
                # Perbaikan Kritis: Jangan lewatkan check=None karena dapat memicu TypeError di beberapa versi discord.py
                purge_kwargs = {
                    "limit": scan_limit,
                    "before": interaction.created_at
                }
                if check_func is not None:
                    purge_kwargs["check"] = check_func
                
                deleted = await channel.purge(**purge_kwargs)
                await interaction.followup.send(f"✅ Berhasil menghapus **{len(deleted)}** pesan.", ephemeral=True)
            else:
                await interaction.followup.send("❌ Fitur ini tidak didukung di channel ini.", ephemeral=True)

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            logger.error(f"Purge Critical Error:\n{error_msg}")
            try:
                await interaction.followup.send(f"❌ Terjadi kesalahan kritis: {e}", ephemeral=True)
            except:
                pass

    @purge.command(name="message", description="Hapus semua pesan")
    @app_commands.describe(count="Jumlah pesan (angka atau teks, misal: 10 atau 'sepuluh')")
    async def purge_message(self, interaction: discord.Interaction, count: str):
        await self.do_purge(interaction, count)

    @purge.command(name="embed", description="Hapus pesan yang mengandung embed")
    @app_commands.describe(count="Jumlah pesan (angka atau teks)")
    async def purge_embed(self, interaction: discord.Interaction, count: str):
        await self.do_purge(interaction, count, check_func=lambda m: len(m.embeds) > 0)

    @purge.command(name="links", description="Hapus pesan yang mengandung link/URL")
    @app_commands.describe(count="Jumlah pesan (angka atau teks)")
    async def purge_links(self, interaction: discord.Interaction, count: str):
        url_regex = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        await self.do_purge(interaction, count, check_func=lambda m: re.search(url_regex, m.content))

    @purge.command(name="bot", description="Hapus pesan yang dikirim oleh bot")
    @app_commands.describe(count="Jumlah pesan (angka atau teks)")
    async def purge_bot(self, interaction: discord.Interaction, count: str):
        await self.do_purge(interaction, count, check_func=lambda m: m.author.bot)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
