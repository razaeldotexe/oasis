import discord
import os
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from google import genai
import time
import sys
import logging
import colorlog
from collections import defaultdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Konfigurasi Logging Berwarna ---
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }
))

logger = colorlog.getLogger('oasis')
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Memuat variabel lingkungan dari file .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# Konfigurasi Gemini AI
client = None
if GEMINI_KEY:
    client = genai.Client(api_key=GEMINI_KEY)

# Sistem Limitasi Penggunaan (Simple Rate Limiting)
# Key: User ID, Value: Timestamp terakhir menggunakan AI
user_cooldowns = defaultdict(float)
COOLDOWN_SECONDS = 10 # Batasan 1 pesan per 10 detik per pengguna

class MyBot(commands.Bot):
    def __init__(self):
        # Menentukan intents (izin) yang diperlukan bot
        intents = discord.Intents.default()
        intents.message_content = True # Diperlukan untuk membaca pesan jika diperlukan
        
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sinkronisasi slash commands ke Discord
        await self.tree.sync()
        logger.info(f"Slash commands berhasil disinkronisasi untuk {self.user}")

    async def on_ready(self):
        logger.info(f'Bot berhasil login sebagai {self.user} (ID: {self.user.id})')
        logger.info('Sistem siap digunakan!')

    async def on_message(self, message):
        # Jangan merespon bot sendiri
        if message.author.bot:
            return

        # Logging pesan masuk
        logger.debug(f"Pesan dari {message.author}: {message.content}")

        # Mengecek apakah bot di-tag dan pesan mengandung 'hello'
        content = message.content.lower()
        is_mentioned = self.user in message.mentions
        
        if is_mentioned and 'hello' in content:
            logger.info(f"Trigger '@oasis hello' terdeteksi dari {message.author}")
            
            # Cek Rate Limit
            current_time = time.time()
            if current_time - user_cooldowns[message.author.id] < COOLDOWN_SECONDS:
                remaining = int(COOLDOWN_SECONDS - (current_time - user_cooldowns[message.author.id]))
                logger.warning(f"Rate limit aktif untuk {message.author}. Sisa {remaining}s")
                await message.reply(f"Wait, {message.author.name}! Tunggu {remaining} detik lagi sebelum bertanya lagi. ⏳")
                return

            if not GEMINI_KEY:
                logger.error("GAGAL: GEMINI_API_KEY tidak ditemukan di .env")
                await message.reply("Maaf, API Key Gemini belum dikonfigurasi oleh pemilik bot. ❌")
                return

            # Ambil sisa teks setelah tag hello
            try:
                if 'hello ' in content:
                    prompt = message.content.lower().split('hello', 1)[1].strip()
                else:
                    prompt = "Halo! Bagaimana hari Anda?"

                logger.info(f"Mengirim prompt ke Gemini ({message.author}): {prompt[:50]}...")

                async with message.channel.typing():
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt
                    )
                    await message.reply(response.text)
                
                user_cooldowns[message.author.id] = current_time
                logger.info(f"Respons Gemini dikirim ke {message.author}")

            except Exception as e:
                logger.error(f"Kesalahan Gemini: {e}")
                await message.reply("Maaf, terjadi kesalahan saat menghubungi otak AI saya. 🧠💥")

        await self.process_commands(message)

bot = MyBot()

# Contoh Slash Command sederhana: /ping
@bot.tree.command(name="ping", description="Memeriksa latensi bot")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f'🏓 Pong! Latensi: {latency}ms')

# Contoh Slash Command dengan parameter: /echo
@bot.tree.command(name="echo", description="Mengulangi pesan yang Anda masukkan")
@app_commands.describe(pesan="Pesan yang ingin diulangi")
async def echo(interaction: discord.Interaction, pesan: str):
    await interaction.response.send_message(f'Anda mengatakan: {pesan}')

# Penanganan Restart Otomatis (Hot Reload)
class RestartHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.endswith((".py", ".env")):
            logger.warning(f"PERUBAHAN TERDETEKSI: {event.src_path}. Memulai ulang sistem...")
            os.execv(sys.executable, ['python'] + sys.argv)

def start_watcher():
    event_handler = RestartHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.daemon = True
    observer.start()
    logger.info("Realtime File Watcher diaktifkan.")

# Menjalankan bot
if __name__ == "__main__":
    if TOKEN == "MASUKKAN_TOKEN_ANDA_DISINI" or TOKEN is None:
        logger.critical("Token Discord tidak ditemukan di file .env!")
    else:
        start_watcher()
        logger.info("Memulai bot...")
        bot.run(TOKEN, log_handler=None) # Menggunakan handler kustom kita
