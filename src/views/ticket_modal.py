import discord
from discord import ui


class TicketModal(ui.Modal, title="📩 Buka Tiket Baru"):
    """Modal form untuk membuat tiket baru."""

    judul = ui.TextInput(
        label="Judul / Topik Masalah",
        placeholder="Contoh: Tidak bisa login ke akun saya",
        max_length=100,
        required=True,
    )

    deskripsi = ui.TextInput(
        label="Deskripsi Lengkap",
        placeholder="Jelaskan masalah kamu secara detail...",
        style=discord.TextStyle.long,
        max_length=1000,
        required=True,
    )

    kategori = ui.TextInput(
        label="Kategori",
        placeholder="Bug / Billing / General / Lainnya",
        max_length=50,
        required=True,
    )

    prioritas = ui.TextInput(
        label="Prioritas",
        placeholder="Low / Medium / High",
        max_length=10,
        required=True,
        default="Low",
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Delegasikan pemrosesan ke cog ticket melalui dispatch event
        interaction.client.dispatch(
            "ticket_submit",
            interaction,
            self.judul.value,
            self.deskripsi.value,
            self.kategori.value.strip(),
            self.prioritas.value.strip(),
        )
