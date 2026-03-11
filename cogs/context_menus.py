import discord
from discord.ext import commands
from discord import app_commands
import os

class ContextMenuCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.context_menu(name="Lihat Avatar HD")
    async def avatar_hd(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=f"Avatar {member.name}", color=discord.Color.blurple())
        embed.set_image(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.context_menu(name="Member Info")
    async def member_info(self, interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(
            title=f"Informasi Member: {member.name}", 
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=str(member.id), inline=True)
        embed.add_field(name="Bergabung di Server", value=discord.utils.format_dt(member.joined_at, "R") if member.joined_at else "Tidak diketahui", inline=True)
        embed.add_field(name="Akun Dibuat", value=discord.utils.format_dt(member.created_at, "R"), inline=False)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles) if roles else "Tidak ada role", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.context_menu(name="Laporkan User")
    async def report_user(self, interaction: discord.Interaction, member: discord.Member):
        await interaction.response.send_modal(UserReportModal(member))

class UserReportModal(discord.ui.Modal, title='Laporkan Pengguna'):
    def __init__(self, member: discord.Member):
        super().__init__()
        self.member = member

    reason = discord.ui.TextInput(
        label='Alasan Laporan',
        style=discord.TextStyle.paragraph,
        placeholder='Tuliskan alasan spesifik Anda melaporkan pengguna ini di sini...',
        required=True,
        max_length=1000,
        min_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f'Terima kasih, laporan Anda untuk **{self.member.name}** telah dikirim ke admin server.',
            ephemeral=True
        )
        
        # Kirim log ke channel khusus jika diset
        log_channel_id = os.getenv('REPORT_LOG_CHANNEL_ID')
        if log_channel_id:
            try:
                channel = interaction.client.get_channel(int(log_channel_id))
                if channel:
                    embed = discord.Embed(title="🚨 Laporan Pengguna Baru", color=discord.Color.red(), timestamp=discord.utils.utcnow())
                    embed.add_field(name="Dilaporkan Oleh", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
                    embed.add_field(name="Pengguna Dilaporkan", value=f"{self.member.mention} ({self.member.id})", inline=False)
                    embed.add_field(name="Alasan", value=self.reason.value, inline=False)
                    await channel.send(embed=embed)
            except Exception as e:
                print(f"Gagal mengirim log report: {e}")

    @app_commands.context_menu(name="Laporkan Pesan")
    async def report_message(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.send_modal(MessageReportModal(message))

    @app_commands.context_menu(name="Translate Message")
    async def translate_message(self, interaction: discord.Interaction, message: discord.Message):
        if not message.content:
            await interaction.response.send_message("❌ Pesan ini tidak berisi teks yang bisa diterjemahkan.", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        try:
            from googletrans import Translator
            translator = Translator()
            # Menerjemahkan otomatis dengan mendeteksi bahasa asal dan target ke bahasa lokal server/Indonesia
            result = translator.translate(message.content, dest='id')
            
            embed = discord.Embed(title="🌐 Hasil Terjemahan (Otomatis -> ID)", description=result.text, color=discord.Color.green())
            embed.set_footer(text=f"Asli: {result.src.upper()} | Diterjemahkan dari pesan {message.author.name}")
            
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ Terjadi kesalahan saat menerjemahkan: {e}")

    @app_commands.context_menu(name="Quote Message")
    async def quote_message(self, interaction: discord.Interaction, message: discord.Message):
        content = message.content or "*[Pesan tidak memiliki teks, mungkin hanya berisi attachment]*"
        embed = discord.Embed(description=content, color=discord.Color.brand_green(), timestamp=message.created_at)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        embed.add_field(name="Sumber", value=f"[Loncat ke pesan]({message.jump_url})")
        
        # Kirim kutipan ke channel saat ini
        await interaction.response.send_message(f"💬 Diutip oleh {interaction.user.mention}", embed=embed)

class MessageReportModal(discord.ui.Modal, title='Laporkan Pesan'):
    def __init__(self, message: discord.Message):
        super().__init__()
        self.message = message

    reason = discord.ui.TextInput(
        label='Alasan Laporan',
        style=discord.TextStyle.paragraph,
        placeholder='Mengapa pesan ini melanggar aturan?...',
        required=True,
        max_length=1000,
        min_length=10
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f'✅ Terima kasih, laporan untuk pesan dari **{self.message.author.name}** telah diteruskan ke admin.',
            ephemeral=True
        )
        
        log_channel_id = os.getenv('REPORT_LOG_CHANNEL_ID')
        if log_channel_id:
            try:
                channel = interaction.client.get_channel(int(log_channel_id))
                if channel:
                    embed = discord.Embed(title="🚩 Laporan Pesan Bermasalah", color=discord.Color.orange(), timestamp=discord.utils.utcnow())
                    embed.add_field(name="Dilaporkan Oleh", value=f"{interaction.user.mention} ({interaction.user.id})", inline=False)
                    embed.add_field(name="Penulis Pesan", value=f"{self.message.author.mention} ({self.message.author.id})", inline=False)
                    embed.add_field(name="Lokasi", value=f"{self.message.channel.mention} - [Loncat ke Pesan]({self.message.jump_url})", inline=False)
                    embed.add_field(name="Konten Pesan", value=self.message.content[:1024] or "*[Tidak ada teks/hanya media]*", inline=False)
                    embed.add_field(name="Alasan Dilaporkan", value=self.reason.value, inline=False)
                    
                    await channel.send(embed=embed)
            except Exception as e:
                print(f"Gagal mengirim log report pesan: {e}")

async def setup(bot):
    await bot.add_cog(ContextMenuCog(bot))
