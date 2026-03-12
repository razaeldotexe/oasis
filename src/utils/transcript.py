import discord
import chat_exporter
import io

from core.logger_config import logger


async def generate_transcript(channel: discord.TextChannel) -> discord.File | None:
    """Hasilkan file transkrip HTML dari riwayat pesan channel tiket.

    Menggunakan library chat-exporter untuk men-generate file HTML
    yang rapi dan siap dikirim sebagai attachment Discord.

    Returns:
        discord.File jika berhasil, None jika gagal.
    """
    try:
        transcript = await chat_exporter.export(
            channel,
            limit=None,
            bot=channel.guild.me,
        )

        if transcript is None:
            logger.warning(f"Transkrip kosong untuk channel {channel.name}")
            return None

        file = discord.File(
            io.BytesIO(transcript.encode()),
            filename=f"transcript-{channel.name}.html",
        )
        return file

    except Exception as e:
        logger.error(f"Gagal membuat transkrip untuk {channel.name}: {e}")
        return None
