# cogs/github_projects.py

import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import asyncio
import json
import os
from datetime import datetime
from utils.lang_colors import get_color, format_languages

GITHUB_USERNAME = "razaeldotexe"
TARGET_CHANNEL_ID = 1480007576622993482
GITHUB_API = "https://api.github.com"
DATA_FILE = "data/github_projects.json"


class GitHubProjects(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: aiohttp.ClientSession = None
        # repo_name -> message_id mapping
        self.tracked: dict[str, int] = {}
        self.header_msg_id: int = None
        self._load_data()

    def _load_data(self):
        """Load tracked message IDs dari file."""
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.tracked = data.get("repos", {})
                self.header_msg_id = data.get("header")

    def _save_data(self):
        """Save tracked message IDs ke file."""
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump({"header": self.header_msg_id, "repos": self.tracked}, f)

    async def cog_load(self):
        self.session = aiohttp.ClientSession(headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        self.update_loop.start()

    async def cog_unload(self):
        self.update_loop.cancel()
        if self.session:
            await self.session.close()

    # ── GitHub API ──────────────────────────────

    async def fetch_repos(self) -> list[dict]:
        repos, page = [], 1
        while True:
            url = f"{GITHUB_API}/users/{GITHUB_USERNAME}/repos?per_page=100&page={page}&sort=updated&type=public"
            async with self.session.get(url) as r:
                if r.status != 200:
                    break
                data = await r.json()
                if not data:
                    break
                repos.extend(data)
                if len(data) < 100:
                    break
                page += 1
        return repos

    async def fetch_languages(self, repo_name: str) -> dict:
        url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo_name}/languages"
        async with self.session.get(url) as r:
            return await r.json() if r.status == 200 else {}

    # ── Embed Builders ──────────────────────────

    def _build_header(self, count: int) -> discord.Embed:
        embed = discord.Embed(
            title="Our Projects",
            description=(
                f"Daftar repositori publik dari "
                f"[{GITHUB_USERNAME}](https://github.com/{GITHUB_USERNAME})\n"
                f"── **{count}** repositori ditemukan"
            ),
            color=0x2B2D31,
        )
        embed.set_thumbnail(url=f"https://github.com/{GITHUB_USERNAME}.png")
        embed.set_footer(text="Auto-update setiap 10 menit")
        embed.timestamp = discord.utils.utcnow()
        return embed

    def _build_repo(self, repo: dict, languages: dict) -> discord.Embed:
        color = get_color(languages)
        lang_str = format_languages(languages)

        # Format tanggal
        try:
            dt = datetime.strptime(repo.get("updated_at", ""), "%Y-%m-%dT%H:%M:%SZ")
            updated = f"<t:{int(dt.timestamp())}:R>"
        except ValueError:
            updated = "—"

        desc = repo.get("description") or "_Tidak ada deskripsi._"

        embed = discord.Embed(
            title=repo["name"],
            description=desc,
            url=repo["html_url"],
            color=color,
        )

        # Stats dalam satu field yang ringkas
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        embed.add_field(
            name="Info",
            value=f"⭐ {stars}  ·  🍴 {forks}  ·  🕐 {updated}",
            inline=False,
        )

        embed.add_field(name="Bahasa", value=lang_str, inline=False)

        if repo.get("topics"):
            topics = " ".join(f"`{t}`" for t in repo["topics"][:8])
            embed.add_field(name="Topik", value=topics, inline=False)

        return embed

    # ── Core: Kirim / Update embeds ─────────────

    async def _send_all(self, channel: discord.TextChannel):
        """Kirim semua repo embeds (fresh). Hapus pesan lama jika ada."""
        # Hapus semua pesan bot lama di channel
        await self._purge_old_messages(channel)

        repos = await self.fetch_repos()
        if not repos:
            return 0

        # Header
        header = await channel.send(embed=self._build_header(len(repos)))
        self.header_msg_id = header.id
        self.tracked = {}

        # Kirim setiap repo
        for repo in repos:
            languages = await self.fetch_languages(repo["name"])
            embed = self._build_repo(repo, languages)
            msg = await channel.send(embed=embed)
            self.tracked[repo["name"]] = msg.id
            await asyncio.sleep(0.5)

        self._save_data()
        return len(repos)

    async def _update_existing(self, channel: discord.TextChannel):
        """Update embed yang sudah ada, tambah repo baru, hapus yang dihapus."""
        repos = await self.fetch_repos()
        if not repos:
            return

        current_names = {r["name"] for r in repos}
        tracked_names = set(self.tracked.keys())

        # Update header
        if self.header_msg_id:
            try:
                header_msg = await channel.fetch_message(self.header_msg_id)
                await header_msg.edit(embed=self._build_header(len(repos)))
            except discord.NotFound:
                header = await channel.send(embed=self._build_header(len(repos)))
                self.header_msg_id = header.id

        # Update / tambah repo
        for repo in repos:
            languages = await self.fetch_languages(repo["name"])
            embed = self._build_repo(repo, languages)

            if repo["name"] in self.tracked:
                # Edit pesan yang sudah ada
                try:
                    msg = await channel.fetch_message(self.tracked[repo["name"]])
                    await msg.edit(embed=embed)
                except discord.NotFound:
                    # Pesan dihapus, kirim ulang
                    msg = await channel.send(embed=embed)
                    self.tracked[repo["name"]] = msg.id
            else:
                # Repo baru
                msg = await channel.send(embed=embed)
                self.tracked[repo["name"]] = msg.id

            await asyncio.sleep(0.3)

        # Hapus repo yang sudah tidak ada
        removed = tracked_names - current_names
        for name in removed:
            try:
                msg = await channel.fetch_message(self.tracked[name])
                await msg.delete()
            except discord.NotFound:
                pass
            del self.tracked[name]

        self._save_data()

    async def _purge_old_messages(self, channel: discord.TextChannel):
        """Hapus semua pesan bot lama di channel."""
        try:
            async for msg in channel.history(limit=200):
                if msg.author == self.bot.user:
                    await msg.delete()
                    await asyncio.sleep(0.3)
        except Exception:
            pass
        self.tracked = {}
        self.header_msg_id = None

    # ── Background Loop ─────────────────────────

    @tasks.loop(minutes=10)
    async def update_loop(self):
        """Cek update repo setiap 10 menit."""
        channel = self.bot.get_channel(TARGET_CHANNEL_ID)
        if not channel or not self.tracked:
            return
        await self._update_existing(channel)

    @update_loop.before_loop
    async def before_update_loop(self):
        await self.bot.wait_until_ready()

    # ── Slash Command Group: /setup ghp ───────────

    setup_group = app_commands.Group(
        name="setup",
        description="Perintah setup bot.",
        default_permissions=discord.Permissions(administrator=True),
    )

    @setup_group.command(
        name="ghp",
        description="Kirim daftar proyek GitHub ke channel our-projects."
    )
    async def ghp_cmd(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(TARGET_CHANNEL_ID)

        if not channel:
            await interaction.response.send_message(
                f"❌ Channel `{TARGET_CHANNEL_ID}` tidak ditemukan.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "⏳ Mengambil data dari GitHub..."
        )

        count = await self._send_all(channel)

        if count == 0:
            await interaction.edit_original_response(
                content="⚠️ Tidak ada repositori publik ditemukan."
            )
            await asyncio.sleep(5)
        else:
            await interaction.edit_original_response(
                content=f"✅ **{count}** repositori dikirim ke <#{TARGET_CHANNEL_ID}>."
            )
            await asyncio.sleep(3)

        # Hapus pesan sementara
        await interaction.delete_original_response()


async def setup(bot: commands.Bot):
    await bot.add_cog(GitHubProjects(bot))

