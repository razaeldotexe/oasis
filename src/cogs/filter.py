import discord
from discord.ext import commands
import os
import re
import asyncio
from core.logger_config import logger

class Filter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load Channel IDs from environment variables
        self.source_code_channel_id = int(os.getenv('SOURCE_CODE_CHANNEL_ID', 0))
        self.meme_channel_id = int(os.getenv('MEME_CHANNEL_ID', 0))
        
        # Extension lists
        self.source_code_exts = [
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.cs', '.go', 
            '.rb', '.php', '.html', '.css', '.json', '.xml', '.yaml', 
            '.yml', '.sh', '.kt', '.swift', '.rs'
        ]
        self.meme_image_exts = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        self.meme_video_exts = ['.mp4', '.mov', '.webm']
        
        # Regex for GitHub/GitLab
        self.git_regex = r'(github\.com|gitlab\.com)\/.+'

    async def delete_and_warn(self, message, reason):
        """Hapus pesan dan kirim peringatan sementara."""
        try:
            # Cek permission manage_messages di channel tersebut
            if not message.channel.permissions_for(message.guild.me).manage_messages:
                logger.warning(f"Tidak memiliki izin manage_messages di {message.channel}")
                return

            await message.delete()
            warn_msg = await message.channel.send(
                f"⚠️ {message.author.mention}, pesan Anda dihapus karena: **{reason}**.\n"
                f"Mohon ikuti aturan channel ini. (Pesan ini akan terhapus dalam 5 detik)"
            )
            await asyncio.sleep(5)
            await warn_msg.delete()
        except Exception as e:
            logger.error(f"Error saat menghapus pesan atau mengirim peringatan: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Abaikan bot
        if message.author.bot:
            return

        # --- Filter #source-code ---
        if message.channel.id == self.source_code_channel_id:
            allowed = False
            # Cek attachments
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in self.source_code_exts):
                        allowed = True
                        break
            
            # Cek link GitHub/GitLab
            if not allowed and re.search(self.git_regex, message.content):
                allowed = True
                
            if not allowed:
                await self.delete_and_warn(message, "Channel ini hanya untuk file source code atau link GitHub/GitLab.")
                return # Stop processing after delete

        # --- Filter #meme ---
        elif message.channel.id == self.meme_channel_id:
            allowed = False
            # Cek attachments (Gambar/Video)
            if message.attachments:
                for attachment in message.attachments:
                    filename = attachment.filename.lower()
                    if any(filename.endswith(ext) for ext in self.meme_image_exts + self.meme_video_exts):
                        allowed = True
                        break
            
            # Cek embeds (Link yang memicu embed gambar/video biasanya ada di message.embeds setelah beberapa saat)
            # Namun sesuai spek: "Link tanpa embed gambar/video" dihapus. 
            # Masalah: on_message dipanggil saat link dikirim, embed mungkin belum muncul.
            # Berdasarkan spek: "hanya mengandung link (tanpa embed gambar/video)"
            # Kita akan prioritaskan attachment dahulu.
            
            if not allowed:
                await self.delete_and_warn(message, "Channel ini hanya untuk mengirim meme (Gambar/Video).")
                return # Stop processing after delete

        # Pastikan command tetap berfungsi
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(Filter(bot))
