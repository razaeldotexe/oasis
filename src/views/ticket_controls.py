import discord
from discord import ui
import os

from utils.colors import Oasis

STAFF_ROLE_ID = int(os.getenv("TICKET_STAFF_ROLE_ID", "0"))


class TicketControlsView(ui.View):
    """Tombol aksi dalam channel tiket (persistent, timeout=None).

    Tombol: Close, Claim, Add Member, Ubah Prioritas.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Tutup Tiket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_close",
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        view = ConfirmCloseView()
        await interaction.response.send_message(
            "⚠️ Apakah kamu yakin ingin menutup tiket ini?",
            view=view,
            ephemeral=True,
        )

    @ui.button(
        label="Klaim",
        emoji="📌",
        style=discord.ButtonStyle.success,
        custom_id="ticket_claim",
    )
    async def claim_ticket(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        # Cek apakah pengguna memiliki role Staff
        staff_role = interaction.guild.get_role(STAFF_ROLE_ID)
        if staff_role and staff_role not in interaction.user.roles:
            await interaction.response.send_message(
                "❌ Hanya staff yang bisa mengklaim tiket.", ephemeral=True
            )
            return

        interaction.client.dispatch(
            "ticket_claim", interaction, interaction.user
        )

    @ui.button(
        label="Tambah Member",
        emoji="👥",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_add_member",
    )
    async def add_member(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        modal = AddMemberModal()
        await interaction.response.send_modal(modal)

    @ui.button(
        label="Ubah Prioritas",
        emoji="⚠️",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_priority",
    )
    async def change_priority(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        view = PrioritySelectView()
        await interaction.response.send_message(
            "Pilih prioritas baru:", view=view, ephemeral=True
        )


class ConfirmCloseView(ui.View):
    """Dialog konfirmasi penutupan tiket."""

    def __init__(self):
        super().__init__(timeout=60)

    @ui.button(label="Konfirmasi", emoji="✅", style=discord.ButtonStyle.danger)
    async def confirm(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        self.stop()
        interaction.client.dispatch("ticket_close_confirm", interaction)

    @ui.button(label="Batal", emoji="❌", style=discord.ButtonStyle.secondary)
    async def cancel(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        self.stop()
        await interaction.response.edit_message(
            content="❌ Penutupan tiket dibatalkan.", view=None
        )


class AddMemberModal(ui.Modal, title="👥 Tambah Member ke Tiket"):
    """Modal untuk memasukkan ID atau mention member."""

    member_input = ui.TextInput(
        label="ID atau @mention Member",
        placeholder="Contoh: 123456789012345678",
        max_length=50,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Bersihkan input — ambil angka saja
        raw = self.member_input.value.strip()
        member_id = "".join(c for c in raw if c.isdigit())

        if not member_id:
            await interaction.response.send_message(
                "❌ ID member tidak valid.", ephemeral=True
            )
            return

        try:
            member = await interaction.guild.fetch_member(int(member_id))
        except (discord.NotFound, discord.HTTPException):
            await interaction.response.send_message(
                "❌ Member tidak ditemukan.", ephemeral=True
            )
            return

        # Tambahkan izin untuk member
        await interaction.channel.set_permissions(
            member, read_messages=True, send_messages=True
        )
        await interaction.response.send_message(
            f"✅ {member.mention} berhasil ditambahkan ke tiket ini.",
            ephemeral=False,
        )


class PrioritySelectView(ui.View):
    """Dropdown untuk memilih prioritas baru."""

    def __init__(self):
        super().__init__(timeout=30)

    @ui.select(
        placeholder="Pilih prioritas baru...",
        options=[
            discord.SelectOption(label="Low", emoji="🟢", value="Low"),
            discord.SelectOption(label="Medium", emoji="🟡", value="Medium"),
            discord.SelectOption(label="High", emoji="🔴", value="High"),
        ],
    )
    async def priority_select(
        self, interaction: discord.Interaction, select: ui.Select
    ):
        new_priority = select.values[0]
        self.stop()
        interaction.client.dispatch(
            "ticket_priority_change", interaction, new_priority
        )
