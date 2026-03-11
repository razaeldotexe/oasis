import discord
from discord import app_commands
from discord.ext import commands
import httpx
import os
from datetime import datetime
from core.logger_config import logger

class PhoneCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.api_key = os.getenv('BESTPHONE_API_KEY')
        self.api_url = "http://38.49.212.111:2081/api/v1/phones/ranking"

    def create_phone_embed(self, phone: dict, last_updated: str):
        """Membangun Discord Embed untuk satu smartphone."""
        # Penanganan jika rank tidak ada di data awal
        rank = phone.get('rank', 1)
        rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉", 4: "4️⃣", 5: "5️⃣"}
        emoji = rank_emoji.get(rank, f"{rank}.")
        
        embed = discord.Embed(
            title=f"{emoji} {phone['name']} — Skor Agregat: {phone['aggregate_score']}/100",
            color=discord.Color.blue(),
            timestamp=datetime.fromisoformat(last_updated.replace('Z', '+00:00')) if last_updated != "N/A" else None
        )
        
        if phone.get('thumbnail_url'):
            embed.set_thumbnail(url=phone['thumbnail_url'])
            
        scores = phone['scores']
        # Mapping skor berdasarkan response API aktual
        antutu = scores.get('antutu', 0)
        geekbench = scores.get('geekbench', scores.get('geekbench_single', 0)) # fallback
        
        benchmark_text = (
            f"AnTuTu: {antutu:,} | "
            f"Geekbench: {geekbench:,}"
        )
        
        embed.add_field(name="📊 Benchmark", value=benchmark_text, inline=False)
        embed.add_field(name="📷 Kamera", value=f"DXOMARK Score: {scores.get('dxomark', 'N/A')}", inline=True)
        embed.add_field(name="🎮 GPU", value=f"3DMark Score: {scores.get('d3dmark', 0):,}", inline=True)
        embed.add_field(name="🔋 SoC", value=f"Nanoreview Score: {scores.get('nanoreview', 'N/A')}/100", inline=True)
        
        price = phone.get('price_usd', 'N/A')
        kimovil = scores.get('kimovil', 'N/A')
        price_text = f"USD ${price} (Value Score: {kimovil}/10)"
        embed.add_field(name="💰 Harga Est.", value=price_text, inline=False)
        
        sources = phone.get('sources', {})
        ref_links = [
            f"[GSMArena]({sources['gsmarena']})" if sources.get('gsmarena') else None,
            f"[Nanoreview]({sources['nanoreview']})" if sources.get('nanoreview') else None,
            f"[Kimovil]({sources['kimovil']})" if sources.get('kimovil') else None
        ]
        ref_text = " ".join([link for link in ref_links if link])
        embed.add_field(name="🔗 Referensi", value=ref_text or "Tidak tersedia", inline=False)
        
        embed.set_footer(text=f"Data per: {last_updated}")
        return embed

    @app_commands.command(name="best-phone", description="Dapatkan rekomendasi Top 5 smartphone terbaik berdasarkan skor agregat.")
    async def best_phone(self, interaction: discord.Interaction):
        if not self.api_key:
            await interaction.response.send_message("⚠️ API Key tidak ditemukan. Hubungi admin bot.", ephemeral=True)
            return

        await interaction.response.send_message("⏳ Mengambil data ranking terbaru...", ephemeral=True)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"X-API-Key": self.api_key}
                params = {"limit": 5}
                response = await client.get(self.api_url, headers=headers, params=params)

                if response.status_code != 200:
                    await interaction.edit_original_response(
                        content=f"⚠️ Server data mengembalikan error {response.status_code}. Coba lagi nanti."
                    )
                    return

                result = response.json()
                if result.get("status") != "success" or "data" not in result:
                    await interaction.edit_original_response(content="⚠️ Format data tidak dikenali. Hubungi admin bot.")
                    return

                phones = result["data"]
                if not phones:
                    await interaction.edit_original_response(content="⚠️ Tidak ada data ranking yang tersedia saat ini.")
                    return

                # Mengirim embed. Karena limit interaction response hanya 1 pesan dengan multiple embeds (max 10),
                # kita akan mengirim semua Top 5 dalam satu response message.
                embeds = []
                for phone in phones[:5]:
                    embeds.append(self.create_phone_embed(phone, result.get("last_updated", "N/A")))

                # Karena interaction.response sudah dipanggil (send_message loading), 
                # kita gunakan follow-up atau edit_original_response untuk mengirim hasil akhir.
                # Namun, edit_original_response meng-overwrite pesan loading.
                # Spesifikasi meminta loading indicator dikirim ephemeral.
                await interaction.edit_original_response(content=None, embeds=embeds)

        except httpx.TimeoutException:
            await interaction.edit_original_response(content="⚠️ Koneksi ke server data timeout. Coba lagi nanti.")
        except Exception as e:
            logger.error(f"Error in /best-phone: {e}")
            await interaction.edit_original_response(content="⚠️ Gagal mengambil data. Coba lagi beberapa saat.")

    @app_commands.command(name="phone-refresh", description="Trigger manual pembaruan cache ranking smartphone di server API.")
    async def best_phone_refresh(self, interaction: discord.Interaction):
        if not self.api_key:
            await interaction.response.send_message("⚠️ API Key tidak ditemukan. Hubungi admin bot.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            refresh_url = f"{self.api_url.replace('/ranking', '/refresh')}"
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"X-API-Key": self.api_key}
                response = await client.post(refresh_url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message", "Cache berhasil diperbarui.")
                    await interaction.followup.send(f"✅ **Sukses:** {message}", ephemeral=True)
                elif response.status_code == 403:
                    await interaction.followup.send("⚠️ **Gagal:** API Key tidak memiliki izin untuk refresh.", ephemeral=True)
                else:
                    await interaction.followup.send(f"⚠️ **Gagal:** Server mengembalikan error {response.status_code}.", ephemeral=True)

        except httpx.TimeoutException:
            await interaction.followup.send("⚠️ **Timeout:** Proses refresh memakan waktu terlalu lama. Coba cek beberapa saat lagi.", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in /phone-refresh: {e}")
            await interaction.followup.send("⚠️ **Error:** Terjadi kesalahan saat mencoba merefresh data.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(PhoneCog(bot))
