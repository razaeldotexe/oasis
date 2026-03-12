import discord
from discord import ui


class TicketPanelView(ui.View):
    """Tombol persistent '📩 Open Ticket' yang ditampilkan di panel tiket.

    View ini bersifat persistent (timeout=None) sehingga tetap aktif
    meskipun bot di-restart. Callback sebenarnya ditangani oleh cog ticket.
    """

    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(
        label="Open Ticket",
        emoji="📩",
        style=discord.ButtonStyle.blurple,
        custom_id="open_ticket",
    )
    async def open_ticket_button(
        self, interaction: discord.Interaction, button: ui.Button
    ):
        # Import di sini untuk menghindari circular import
        from views.ticket_modal import TicketModal

        modal = TicketModal()
        await interaction.response.send_modal(modal)
