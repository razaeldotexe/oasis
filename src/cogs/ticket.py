import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from datetime import datetime

from core.logger_config import logger
from utils.colors import Oasis
from utils.db import (
    init_db,
    create_ticket,
    get_active_ticket,
    get_ticket_by_channel,
    claim_ticket,
    close_ticket,
    update_ticket,
    set_ticket_rating,
)
from utils.transcript import generate_transcript
from views.ticket_button import TicketPanelView
from views.ticket_controls import TicketControlsView

STAFF_ROLE_ID = int(os.getenv("TICKET_STAFF_ROLE_ID", "0"))
CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))
LOG_CHANNEL_ID = int(os.getenv("TICKET_LOG_CHANNEL_ID", "0"))

# Peta emoji untuk prioritas
PRIORITY_EMOJI = {
    "Low": "🟢",
    "Medium": "🟡",
    "High": "🔴",
}

# Peta warna embed berdasarkan status
STATUS_COLOR = {
    "OPEN": Oasis.SUCCESS,
    "IN_PROGRESS": Oasis.WARNING,
    "CLOSED": Oasis.ERROR,
}


class Ticket(commands.Cog):
    """Cog utama untuk sistem tiket support."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        """Dipanggil saat cog dimuat — inisialisasi database."""
        await init_db()
        logger.info("Ticket system database initialized.")

    # ───────────────────────────────────────────────
    # Slash Command: /setup-ticket
    # ───────────────────────────────────────────────

    @app_commands.command(
        name="setup-ticket",
        description="Kirim panel tiket dengan tombol 'Open Ticket' ke channel ini",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎫 Pusat Bantuan",
            description=(
                "Butuh bantuan? Klik tombol di bawah untuk membuka tiket baru.\n\n"
                "**Panduan:**\n"
                "• Jelaskan masalahmu secara detail\n"
                "• Pilih kategori yang sesuai\n"
                "• Tim support kami akan segera merespons\n\n"
                "💡 *Satu pengguna hanya bisa memiliki satu tiket aktif.*"
            ),
            color=Oasis.PRIMARY,
        )
        embed.set_footer(text="Oasis Support System")
        embed.timestamp = datetime.now()

        view = TicketPanelView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message(
            "✅ Panel tiket berhasil dikirim!", ephemeral=True
        )

    # ───────────────────────────────────────────────
    # Event: on_ticket_submit (dari TicketModal)
    # ───────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ticket_submit(
        self,
        interaction: discord.Interaction,
        judul: str,
        deskripsi: str,
        kategori: str,
        prioritas: str,
    ):
        guild = interaction.guild
        user = interaction.user

        # Validasi prioritas
        if prioritas not in ("Low", "Medium", "High"):
            prioritas = "Low"

        # Cek tiket aktif
        active = await get_active_ticket(str(user.id), str(guild.id))
        if active:
            await interaction.response.send_message(
                f"❌ Kamu sudah punya tiket aktif di <#{active['channel_id']}>.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True)

        # Cari atau buat kategori
        category = guild.get_channel(CATEGORY_ID)
        if category is None:
            # Buat kategori baru kalau belum ada
            category = await guild.create_category("🎫 Tickets")

        # Buat channel privat
        staff_role = guild.get_role(STAFF_ROLE_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, attach_files=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True, manage_channels=True
            ),
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            )

        # Buat nama channel sementara, ticket_id ditambahkan setelah insert DB
        channel = await guild.create_text_channel(
            name=f"ticket-{user.name}",
            category=category,
            overwrites=overwrites,
            reason=f"Tiket baru dibuka oleh {user}",
        )

        # Simpan ke database
        ticket_id = await create_ticket(
            guild_id=str(guild.id),
            channel_id=str(channel.id),
            user_id=str(user.id),
            judul=judul,
            deskripsi=deskripsi,
            kategori=kategori,
            prioritas=prioritas,
        )

        # Ubah nama channel dengan ticket_id
        await channel.edit(name=f"ticket-{user.name}-{ticket_id}")

        # Kirim embed info tiket ke channel baru
        priority_emoji = PRIORITY_EMOJI.get(prioritas, "🟢")
        embed = discord.Embed(
            title=f"🎫 Tiket #{ticket_id} — {judul}",
            description=deskripsi,
            color=STATUS_COLOR["OPEN"],
        )
        embed.add_field(name="📂 Kategori", value=kategori, inline=True)
        embed.add_field(
            name="📊 Prioritas", value=f"{priority_emoji} {prioritas}", inline=True
        )
        embed.add_field(name="📌 Status", value="🟢 Open", inline=True)
        embed.add_field(
            name="👤 Dibuat oleh", value=user.mention, inline=True
        )
        embed.set_footer(text=f"Ticket ID: {ticket_id}")
        embed.timestamp = datetime.now()

        controls = TicketControlsView()
        await channel.send(embed=embed, view=controls)

        # Mention staff
        if staff_role:
            ping_msg = await channel.send(
                f"{staff_role.mention} — Tiket baru telah dibuat!"
            )
            await asyncio.sleep(3)
            await ping_msg.delete()

        # Kirim log
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(
                title="📋 Tiket Baru Dibuka",
                color=Oasis.PRIMARY,
            )
            log_embed.add_field(
                name="🆔 ID Tiket", value=f"#{ticket_id}", inline=True
            )
            log_embed.add_field(
                name="👤 Pengguna", value=f"{user.mention}", inline=True
            )
            log_embed.add_field(
                name="📂 Kategori", value=kategori, inline=True
            )
            log_embed.add_field(
                name="📊 Prioritas",
                value=f"{priority_emoji} {prioritas}",
                inline=True,
            )
            log_embed.add_field(
                name="📍 Channel", value=channel.mention, inline=True
            )
            log_embed.timestamp = datetime.now()
            await log_channel.send(embed=log_embed)

        # Balas ke pengguna
        await interaction.followup.send(
            f"✅ Tiket berhasil dibuat! Silakan cek {channel.mention}.",
            ephemeral=True,
        )

    # ───────────────────────────────────────────────
    # Event: on_ticket_claim (dari TicketControlsView)
    # ───────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ticket_claim(
        self, interaction: discord.Interaction, staff: discord.Member
    ):
        ticket = await get_ticket_by_channel(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message(
                "❌ Tiket tidak ditemukan.", ephemeral=True
            )
            return

        if ticket["status"] != "OPEN":
            await interaction.response.send_message(
                "❌ Tiket ini sudah diklaim atau ditutup.", ephemeral=True
            )
            return

        await claim_ticket(ticket["ticket_id"], str(staff.id))

        # Perbarui embed utama
        await self._update_ticket_embed(
            interaction.channel,
            ticket["ticket_id"],
            status_text="🟡 In Progress",
            status_key="IN_PROGRESS",
            extra_fields={"🛠️ Diklaim oleh": staff.mention},
        )

        await interaction.response.send_message(
            f"📌 Tiket diklaim oleh {staff.mention}!", ephemeral=False
        )

        # Kirim log
        await self._send_log(
            interaction.guild,
            f"📌 Tiket #{ticket['ticket_id']} diklaim oleh {staff.mention}",
        )

    # ───────────────────────────────────────────────
    # Event: on_ticket_close_confirm
    # ───────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ticket_close_confirm(self, interaction: discord.Interaction):
        ticket = await get_ticket_by_channel(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message(
                "❌ Tiket tidak ditemukan.", ephemeral=True
            )
            return

        if ticket["status"] == "CLOSED":
            await interaction.response.send_message(
                "❌ Tiket ini sudah ditutup.", ephemeral=True
            )
            return

        await interaction.response.edit_message(
            content="✅ Tiket akan ditutup. Menghasilkan transkrip...", view=None
        )

        channel = interaction.channel
        guild = interaction.guild

        # Generate transkrip
        transcript_file = await generate_transcript(channel)

        # Tutup di database
        await close_ticket(ticket["ticket_id"], str(interaction.user.id))

        # Buat embed ringkasan
        opener = guild.get_member(int(ticket["user_id"]))
        summary_embed = discord.Embed(
            title=f"🔒 Tiket #{ticket['ticket_id']} Ditutup",
            description=f"**Judul:** {ticket['judul']}",
            color=STATUS_COLOR["CLOSED"],
        )
        summary_embed.add_field(
            name="👤 Dibuka oleh",
            value=f"<@{ticket['user_id']}>",
            inline=True,
        )
        summary_embed.add_field(
            name="🔒 Ditutup oleh",
            value=interaction.user.mention,
            inline=True,
        )
        summary_embed.add_field(
            name="📂 Kategori", value=ticket["kategori"] or "-", inline=True
        )
        created_at = ticket.get("created_at", "Tidak diketahui")
        summary_embed.add_field(
            name="📅 Durasi",
            value=f"Dibuat: {created_at}",
            inline=False,
        )
        summary_embed.timestamp = datetime.now()

        # Kirim transkrip ke #ticket-logs
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            kwargs = {"embed": summary_embed}
            if transcript_file:
                kwargs["file"] = transcript_file
            await log_channel.send(**kwargs)

        # Kirim transkrip ke DM pengguna
        if opener:
            try:
                dm_embed = discord.Embed(
                    title=f"🔒 Tiket #{ticket['ticket_id']} Ditutup",
                    description=(
                        f"Tiket kamu **{ticket['judul']}** di **{guild.name}** "
                        "telah ditutup.\n\nTerima kasih sudah menghubungi kami!"
                    ),
                    color=STATUS_COLOR["CLOSED"],
                )
                dm_kwargs = {"embed": dm_embed}

                # Re-generate transkrip jika sudah terkirim ke log (file hanya bisa dipakai sekali)
                if transcript_file:
                    dm_transcript = await generate_transcript(channel)
                    if dm_transcript:
                        dm_kwargs["file"] = dm_transcript

                await opener.send(**dm_kwargs)

                # Kirim rating setelah DM ringkasan
                await self._send_rating_dm(opener, ticket["ticket_id"], guild)

            except discord.Forbidden:
                logger.warning(
                    f"Tidak bisa mengirim DM ke {opener} (DM tertutup)."
                )

        # Countdown & hapus channel
        await channel.send("🔒 Tiket ditutup. Channel akan dihapus dalam **5 detik**...")
        await asyncio.sleep(5)
        await channel.delete(reason=f"Tiket #{ticket['ticket_id']} ditutup")

    # ───────────────────────────────────────────────
    # Event: on_ticket_priority_change
    # ───────────────────────────────────────────────

    @commands.Cog.listener()
    async def on_ticket_priority_change(
        self, interaction: discord.Interaction, new_priority: str
    ):
        ticket = await get_ticket_by_channel(str(interaction.channel.id))
        if not ticket:
            await interaction.response.send_message(
                "❌ Tiket tidak ditemukan.", ephemeral=True
            )
            return

        await update_ticket(ticket["ticket_id"], prioritas=new_priority)

        priority_emoji = PRIORITY_EMOJI.get(new_priority, "🟢")

        # Perbarui embed utama
        await self._update_ticket_embed(
            interaction.channel,
            ticket["ticket_id"],
            priority_override=f"{priority_emoji} {new_priority}",
        )

        await interaction.response.edit_message(
            content=f"✅ Prioritas diubah ke **{priority_emoji} {new_priority}**.",
            view=None,
        )

    # ───────────────────────────────────────────────
    # Metode utilitas internal
    # ───────────────────────────────────────────────

    async def _update_ticket_embed(
        self,
        channel: discord.TextChannel,
        ticket_id: int,
        status_text: str | None = None,
        status_key: str | None = None,
        extra_fields: dict | None = None,
        priority_override: str | None = None,
    ):
        """Perbarui embed tiket pertama di channel."""
        async for message in channel.history(oldest_first=True, limit=5):
            if message.author == self.bot.user and message.embeds:
                embed = message.embeds[0]
                new_embed = discord.Embed(
                    title=embed.title,
                    description=embed.description,
                    color=STATUS_COLOR.get(status_key, embed.color) if status_key else embed.color,
                )
                new_embed.timestamp = embed.timestamp
                new_embed.set_footer(text=f"Ticket ID: {ticket_id}")

                # Salin field yang sudah ada, dengan modifikasi
                for field in embed.fields:
                    if field.name == "📌 Status" and status_text:
                        new_embed.add_field(
                            name="📌 Status", value=status_text, inline=True
                        )
                    elif field.name == "📊 Prioritas" and priority_override:
                        new_embed.add_field(
                            name="📊 Prioritas",
                            value=priority_override,
                            inline=True,
                        )
                    else:
                        new_embed.add_field(
                            name=field.name,
                            value=field.value,
                            inline=field.inline,
                        )

                # Tambahkan field baru jika ada
                if extra_fields:
                    for name, value in extra_fields.items():
                        new_embed.add_field(name=name, value=value, inline=True)

                await message.edit(embed=new_embed)
                break

    async def _send_log(self, guild: discord.Guild, message: str):
        """Kirim pesan log singkat ke channel log tiket."""
        log_channel = guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                description=message,
                color=Oasis.SECONDARY,
                timestamp=datetime.now(),
            )
            await log_channel.send(embed=embed)

    async def _send_rating_dm(
        self, user: discord.Member, ticket_id: int, guild: discord.Guild
    ):
        """Kirim DM rating ⭐ ke pengguna setelah tiket ditutup."""
        view = RatingView(ticket_id)
        try:
            await user.send(
                f"💬 Bagaimana pengalaman support kamu di **{guild.name}**?",
                view=view,
            )
        except discord.Forbidden:
            pass


class RatingView(discord.ui.View):
    """Tombol rating ⭐ 1-5 untuk menilai pengalaman support."""

    def __init__(self, ticket_id: int):
        super().__init__(timeout=300)
        self.ticket_id = ticket_id

        for i in range(1, 6):
            button = discord.ui.Button(
                label=str(i),
                emoji="⭐",
                style=discord.ButtonStyle.secondary,
                custom_id=f"rating_{ticket_id}_{i}",
            )
            button.callback = self._make_callback(i)
            self.add_item(button)

    def _make_callback(self, rating: int):
        async def callback(interaction: discord.Interaction):
            await set_ticket_rating(self.ticket_id, rating)
            labels = {
                1: "Sangat Buruk",
                2: "Buruk",
                3: "Cukup",
                4: "Baik",
                5: "Sangat Baik",
            }
            await interaction.response.edit_message(
                content=f"Terima kasih atas penilaianmu! {'⭐' * rating} — **{labels[rating]}**",
                view=None,
            )

        return callback


async def setup(bot):
    await bot.add_cog(Ticket(bot))
