import discord
from discord import app_commands
from discord.ext import commands
import os
import httpx
from pathlib import Path
from utils.url_parser import extract_video_id
from services.yt_service import get_thumbnail_info
from core.logger_config import logger

class YouTube(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cookies_path = "cookies.txt"

    async def download_image(self, url: str, path: Path) -> tuple[bool, int]:
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    with open(path, "wb") as f:
                        f.write(resp.content)
                    return True, 200
                return False, resp.status_code
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return False, 0

    # Group Command: /yt-thumbnail
    yt_thumbnail_group = app_commands.Group(name="yt-thumbnail", description="Perintah terkait YouTube Thumbnail")

    @yt_thumbnail_group.command(name="download", description="Unduh thumbnail dari YouTube atau YouTube Music")
    @app_commands.describe(url="URL video YouTube atau YouTube Music")
    async def download(self, interaction: discord.Interaction, url: str):
        # 1. Respon awal (ephemeral loading)
        await interaction.response.send_message("🔍 Sedang memproses URL, mohon tunggu...", ephemeral=True)
        
        # 2. Ekstrak Video ID
        video_id = extract_video_id(url)
        if not video_id:
            await interaction.edit_original_response(content="❌ URL tidak valid atau Video ID tidak ditemukan.")
            return

        try:
            # 3. Ambil info thumbnail menggunakan cookies.txt
            # Pastikan path cookies sesuai dengan lokasi cookies.txt di root bot
            cookies_file = self.cookies_path if os.path.exists(self.cookies_path) else None
            
            info = await get_thumbnail_info(video_id, cookiefile=cookies_file)
            metadata = info["metadata"]
            thumbnails = info["thumbnails"]
            
            # 4. Pilih kualitas (maxresdefault, fall back to high)
            img_url = thumbnails.get("max_res") or thumbnails.get("high")
            
            if not img_url:
                await interaction.edit_original_response(content="❌ Thumbnail tidak ditemukan untuk video ini.")
                return

            # Nama file yang aman untuk sistem file
            clean_title = "".join([c if c.isalnum() else "_" for c in metadata['title']])[:50]
            filename = f"{clean_title}_thumbnail.jpg"
            save_path = Path("downloads") / filename
            
            # 5. Unduh thumbnail secara asinkron
            success, status_code = await self.download_image(img_url, save_path)
            
            # Fallback jika max_res gagal (sering terjadi jika video tidak punya resolusi tinggi)
            if not success and thumbnails.get("high") and img_url != thumbnails.get("high"):
                img_url = thumbnails.get("high")
                success, status_code = await self.download_image(img_url, save_path)

            if success:
                logger.info(f"Thumbnail downloaded successfully for video: {video_id}")
                
                # 6. Kirim file ke DM user
                try:
                    await interaction.user.send(
                        content=f"🎬 **Thumbnail Video:** {metadata['title']}\n👤 **Author:** {metadata['author']}",
                        file=discord.File(save_path)
                    )
                    await interaction.edit_original_response(content="✅ Thumbnail telah berhasil dikirim ke DM Anda!")
                except discord.Forbidden:
                    #Jika DM dinonaktifkan
                    await interaction.edit_original_response(content="Please enable ur DMs")
                except Exception as e:
                    logger.error(f"Error sending file to DM: {e}")
                    await interaction.edit_original_response(content=f"❌ Gagal mengirim file ke DM: {str(e)}")
                finally:
                    # 7. Cleanup file lokal
                    if save_path.exists():
                        try:
                            os.remove(save_path)
                        except Exception as e:
                            logger.error(f"Error deleting temp file {save_path}: {e}")
            else:
                await interaction.edit_original_response(content=f"❌ Gagal mengunduh thumbnail (Status: {status_code}).")

        except Exception as e:
            logger.error(f"Error in /yt-thumbnail download command: {e}")
            await interaction.edit_original_response(content=f"❌ Terjadi kesalahan saat memproses permintaan: {str(e)}")

async def setup(bot):
    await bot.add_cog(YouTube(bot))
