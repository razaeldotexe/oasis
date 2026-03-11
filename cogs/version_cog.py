# cogs/version_cog.py

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from utils.colors import Oasis
from core.version import get_version, get_info, bump, git_push_version


class VersionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /version — Tampilkan versi bot ──────────

    @app_commands.command(
        name="version",
        description="Tampilkan versi bot saat ini."
    )
    async def version_cmd(self, interaction: discord.Interaction):
        info = get_info()
        embed = discord.Embed(
            title=info.get("name", "Bot"),
            description=f"```v{info['version']}```",
            color=Oasis.PRIMARY,
        )
        embed.add_field(
            name="Repository",
            value=f"[{info.get('repository', '—')}](https://github.com/{info.get('repository', '')})",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ── /release [patch|minor|major] — Bump & push ──

    @app_commands.command(
        name="release",
        description="Bump versi bot dan push ke GitHub."
    )
    @app_commands.describe(
        part="Bagian versi yang di-bump",
        message="Pesan commit custom (opsional)"
    )
    @app_commands.choices(part=[
        app_commands.Choice(name="patch (1.0.x)", value="patch"),
        app_commands.Choice(name="minor (1.x.0)", value="minor"),
        app_commands.Choice(name="major (x.0.0)", value="major"),
    ])
    @app_commands.default_permissions(administrator=True)
    async def release_cmd(
        self,
        interaction: discord.Interaction,
        part: app_commands.Choice[str],
        message: str = None,
    ):
        old_version = get_version()

        await interaction.response.send_message(
            f"⏳ Bumping `v{old_version}` → **{part.value}**..."
        )

        # Bump version
        new_version = bump(part.value)

        # Git commit + tag + push
        commit_msg = message or f"release: v{new_version}"
        success, output = await asyncio.to_thread(git_push_version, new_version, commit_msg)

        if success:
            embed = discord.Embed(
                title="✅ Release berhasil",
                description=f"`v{old_version}` → `v{new_version}`",
                color=Oasis.SUCCESS,
            )
            embed.add_field(name="Commit", value=f"```{commit_msg}```", inline=False)
            embed.add_field(name="Tag", value=f"`v{new_version}`", inline=True)
            await interaction.edit_original_response(content=None, embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Release gagal",
                description=f"```{output}```",
                color=Oasis.ERROR,
            )
            await interaction.edit_original_response(content=None, embed=embed)

        # Auto-delete setelah 10 detik
        await asyncio.sleep(10)
        await interaction.delete_original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(VersionCog(bot))
