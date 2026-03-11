# 🏝️ Oasis Discord Bot & Web Sender

Sistem Discord Bot modular yang dilengkapi dengan fitur AI Gemini, Moderasi, Hot Reload, YouTube Thumbnail Downloader, dan Pengirim Embed berbasis Web.

## ✨ Fitur Utama
- **Discord Bot**: Slash commands (/ping, /timeout, /ban, dll).
- **Discord Context Menus**: Fitur klik kanan pada User/Pesan (Lihat Avatar HD, Translate Text, Member Info & Quote).
- **Moderation & Report**: Pembuatan form pop-up modal untuk melaporkan pengguna dan pesan.
- **YT Thumbnail**: Unduh thumbnail YouTube/YouTube Music langsung ke DM user.
- **Gemini AI**: Integrasi Google Gemini 1.5-flash (@oasis hello).
- **Web Embed Sender**: Antarmuka web modern untuk mengirim rich embed via Webhook.
- **Hot Reload**: Restart otomatis saat kode berubah.
- **Best Phone**: Rekomendasi smartphone terbaik real-time via `/best-phone` dan manual refresh via `/phone-refresh`.
- **TribunNews Auto-Poster**: Secara konstan mengecek API dan mem-posting berita terkini ke channel khusus secara otomatis!
- **Auto-Delete Filter**: Sistem filter pesan otomatis untuk channel `#source-code` dan `#meme` guna menjaga relevansi konten.
- **Advanced Logging**: Log berwarna di terminal dan tersimpan di folder `logs/`.

## 🚀 Persiapan & Instalasi

1. **Clone & Install Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Konfigurasi `.env`**:
   Salin file `.env` dan isi dengan kredensial Anda:
   ```env
   DISCORD_TOKEN=your_bot_token
   GEMINI_API_KEY=your_gemini_key
   SOURCE_CODE_CHANNEL_ID=your_source_code_channel_id
   MEME_CHANNEL_ID=your_meme_channel_id
   REPORT_LOG_CHANNEL_ID=your_admin_log_channel_id
   DISCORD_WEBHOOK_URL=your_webhook_url
   FLASK_SECRET_KEY=generate_a_random_string
   BESTPHONE_API_KEY=your_phone_api_key
   NEWS_CHANNEL_ID=your_news_channel_id
   NEWS_INTERVAL_MINUTES=15
   MAX_NEWS_PER_BATCH=5
   ```

3. **YouTube Cookies (Opsional)**:
   Letakkan file `cookies.txt` (format Netscape) di root direktori jika ingin mengunduh thumbnail dari video yang dibatasi usia.

4. **Menjalankan Program**:
   - **Bot Utama**: `python main.py`
   - **Web Sender**: `python web_sender.py` (Buka http://localhost:5000)

## 🚀 Deployment (Production)

### Opsi A: Docker (Direkomendasikan)
```bash
docker-compose up -d --build
```

### Opsi B: Systemd
1. Salin `oasis-bot.service` ke `/etc/systemd/system/`.
2. Edit path di file service agar sesuai dengan lokasi folder proyek Anda.
3. Jalankan `sudo systemctl enable --now oasis-bot.service`.

### Automasi Update
Tersedia script `./deploy.sh` untuk melakukan penarikan kode dan restart service secara otomatis di Linux VPS.

## 📁 Struktur Folder
- `cogs/`: Modul perintah bot (AI, Moderasi, Utilitas, YouTube, Filter, Phone, Context Menus).
- `core/`: Inti logika sistem (Bot class, Logger, Sender logic).
- `services/`: Layanan eksternal (YouTube Downloader).
- `utils/`: Utilitas pembantu (URL Parser).
- `templates/`: File HTML untuk Web Sender.
- `logs/`: Riwayat aktivitas sistem.

## 🛡️ Keamanan
- Web Sender dilengkapi dengan **Rate Limiter** untuk mencegah spam.
- Perintah moderasi memerlukan izin (Permissions) spesifik di server.
- File `.env` dan `cookies.txt` dilindungi oleh `.gitignore`.
