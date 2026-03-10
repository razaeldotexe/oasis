import discord
from discord import app_commands
from discord.ext import commands
from core.logger_config import logger

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Memeriksa latensi bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f'🏓 Pong! Latensi: {latency}ms')

    @app_commands.command(name="echo", description="Mengulangi pesan yang Anda masukkan")
    @app_commands.describe(pesan="Pesan yang ingin diulangi")
    async def echo(self, interaction: discord.Interaction, pesan: str):
        await interaction.response.send_message(f'Anda mengatakan: {pesan}')

async def setup(bot):
    await bot.add_cog(Utility(bot))
