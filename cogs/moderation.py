import discord
from discord import app_commands
from discord.ext import commands
import datetime
from core.logger_config import logger

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

async def setup(bot):
    await bot.add_cog(Moderation(bot))
