# cogs/github_projects.py

import discord
from discord.ext import commands, tasks
import aiohttp
import asyncio
from datetime import datetime
from utils.lang_colors import get_embed_color, get_language_percentages

GITHUB_USERNAME = "razaeldotexe"
TARGET_CHANNEL_ID = 1480007576622993482
GITHUB_API_BASE = "https://api.github.com"


class GitHubProjects(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                # Opsional: tambahkan token jika rate limit
                # "Authorization": "Bearer YOUR_GITHUB_TOKEN",
            }
        )

    async def cog_unload(self):
        if self.session:
            await self.session.close()

    # ─────────────────────────────────────────────
    # Helper: Fetch semua repositori publik
    # ─────────────────────────────────────────────
    async def fetch_repos(self) -> list[dict]:
        """Mengambil semua repositori publik dari GitHub API (dengan pagination)."""
        repos = []
        page = 1

        while True:
            url = (
                f"{GITHUB_API_BASE}/users/{GITHUB_USERNAME}/repos"
                f"?per_page=100&page={page}&sort=updated&type=public"
            )
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    break
                data = await resp.json()
                if not data:
                    break
                repos.extend(data)
                if len(data) < 100:
                    break
                page += 1

        return repos

    # ─────────────────────────────────────────────
    # Helper: Fetch bahasa untuk satu repo
    # ─────────────────────────────────────────────
    async def fetch_languages(self, repo_name: str) -> dict:
        """Mengambil data bahasa pemrograman dari sebuah repositori."""
        url = f"{GITHUB_API_BASE}/repos/{GITHUB_USERNAME}/{repo_name}/languages"
        async with self.session.get(url) as resp:
            if resp.status != 200:
                return {}
            return await resp.json()

    # ─────────────────────────────────────────────
    # Helper: Build embed untuk satu repo
    # ─────────────────────────────────────────────
    def build_repo_embed(self, repo: dict, languages: dict) -> discord.Embed:
        """Membuat objek discord.Embed dari data repositori dan bahasa."""
        color = get_embed_color(languages)
        lang_str = get_language_percentages(languages)

        # Tanggal terakhir update
        updated_at = repo.get("updated_at", "")
        try:
            dt = datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")
            updated_str = dt.strftime("%d %b %Y")
        except ValueError:
            updated_str = updated_at

        embed = discord.Embed(
            title=f"📦 {repo['name']}",
            description=repo.get("description") or "_Tidak ada deskripsi._",
            url=repo["html_url"],
            color=color,
        )

        embed.set_author(
            name=GITHUB_USERNAME,
            url=f"https://github.com/{GITHUB_USERNAME}",
            icon_url=f"https://github.com/{GITHUB_USERNAME}.png",
        )

        embed.add_field(
            name="🌐 Bahasa",
            value=lang_str if lang_str else "—",
            inline=False,
        )

        embed.add_field(
            name="⭐ Stars",
            value=str(repo.get("stargazers_count", 0)),
            inline=True,
        )

        embed.add_field(
            name="🍴 Forks",
            value=str(repo.get("forks_count", 0)),
            inline=True,
        )

        embed.add_field(
            name="🔓 Visibilitas",
            value="Publik" if not repo.get("private") else "Private",
            inline=True,
        )

        embed.add_field(
            name="🕐 Terakhir Diperbarui",
            value=updated_str,
            inline=True,
        )

        if repo.get("topics"):
            embed.add_field(
                name="🏷️ Topik",
                value=" ".join(f"`{t}`" for t in repo["topics"]),
                inline=False,
            )

        embed.set_footer(text=f"github.com/{GITHUB_USERNAME}")
        embed.timestamp = discord.utils.utcnow()

        return embed

    # ─────────────────────────────────────────────
    # Slash Command: /github_projects
    # ─────────────────────────────────────────────
    @discord.app_commands.command(
        name="github_projects",
        description="Mengirimkan daftar proyek GitHub razaeldotexe ke channel target."
    )
    @discord.app_commands.default_permissions(administrator=True)
    async def github_projects_cmd(self, interaction: discord.Interaction):
        """Mengirimkan daftar proyek GitHub razaeldotexe ke channel target."""
        channel = self.bot.get_channel(TARGET_CHANNEL_ID)

        if channel is None:
            await interaction.response.send_message(
                f"❌ Channel dengan ID `{TARGET_CHANNEL_ID}` tidak ditemukan. "
                "Pastikan bot memiliki akses ke channel tersebut.",
                ephemeral=True,
            )
            return

        # Pesan loading (ephemeral)
        await interaction.response.send_message(
            "⏳ Mengambil data dari GitHub, mohon tunggu...",
            ephemeral=True,
        )

        try:
            repos = await self.fetch_repos()
        except aiohttp.ClientError as e:
            await interaction.edit_original_response(
                content=f"❌ Gagal mengambil data GitHub: `{e}`"
            )
            return

        if not repos:
            await interaction.edit_original_response(
                content=f"⚠️ Tidak ada repositori publik ditemukan untuk `{GITHUB_USERNAME}`."
            )
            return

        await interaction.edit_original_response(
            content=f"✅ Ditemukan **{len(repos)}** repositori. Mengirim embed ke <#{TARGET_CHANNEL_ID}>..."
        )

        # Header channel
        header_embed = discord.Embed(
            title=f"🚀 Proyek GitHub — {GITHUB_USERNAME}",
            description=(
                f"Berikut adalah daftar repositori publik dari "
                f"[github.com/{GITHUB_USERNAME}](https://github.com/{GITHUB_USERNAME}).\n"
                f"Total: **{len(repos)}** repositori"
            ),
            color=0x24292F,
        )
        header_embed.set_thumbnail(url=f"https://github.com/{GITHUB_USERNAME}.png")
        header_embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=header_embed)

        # Kirim setiap repo sebagai embed terpisah
        for repo in repos:
            languages = await self.fetch_languages(repo["name"])
            embed = self.build_repo_embed(repo, languages)
            await channel.send(embed=embed)
            # Rate limit: jeda kecil agar tidak kena limit Discord
            await asyncio.sleep(0.5)

        # Footer channel
        footer_embed = discord.Embed(
            description=f"✅ Selesai menampilkan **{len(repos)}** repositori.",
            color=0x2ECC71,
        )
        footer_embed.timestamp = discord.utils.utcnow()
        await channel.send(embed=footer_embed)

        await interaction.edit_original_response(
            content=f"✅ Berhasil mengirim **{len(repos)}** embed ke <#{TARGET_CHANNEL_ID}>."
        )


# ─────────────────────────────────────────────
# Setup function (dipanggil oleh bot.load_extension)
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(GitHubProjects(bot))
