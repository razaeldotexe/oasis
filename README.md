# 🏝️ Oasis Discord Bot & Web Sender

Sistem Discord Bot modular yang dilengkapi dengan fitur AI Gemini, Moderasi, Hot Reload, YouTube Thumbnail Downloader, dan Pengirim Embed berbasis Web.

## ✨ Fitur Utama
- **Discord Bot**: Slash commands (/ping, /timeout, /ban, dll).
- **YT Thumbnail**: Unduh thumbnail YouTube/YouTube Music langsung ke DM user.
- **Gemini AI**: Integrasi Google Gemini 1.5-flash (@oasis hello).
- **Web Embed Sender**: Antarmuka web modern untuk mengirim rich embed via Webhook.
- **Hot Reload**: Restart otomatis saat kode berubah.
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
   DISCORD_WEBHOOK_URL=your_webhook_url
   FLASK_SECRET_KEY=generate_a_random_string
   ```

3. **YouTube Cookies (Opsional)**:
   Letakkan file `cookies.txt` (format Netscape) di root direktori jika ingin mengunduh thumbnail dari video yang dibatasi usia.

4. **Menjalankan Program**:
   - **Bot Utama**: `python main.py`
   - **Web Sender**: `python web_sender.py` (Buka http://localhost:5000)

## 📁 Struktur Folder
- `cogs/`: Modul perintah bot (AI, Moderasi, Utilitas, YouTube).
- `core/`: Inti logika sistem (Bot class, Logger, Sender logic).
- `services/`: Layanan eksternal (YouTube Downloader).
- `utils/`: Utilitas pembantu (URL Parser).
- `templates/`: File HTML untuk Web Sender.
- `logs/`: Riwayat aktivitas sistem.

## 🛡️ Keamanan
- Web Sender dilengkapi dengan **Rate Limiter** untuk mencegah spam.
- Perintah moderasi memerlukan izin (Permissions) spesifik di server.
- File `.env` dan `cookies.txt` dilindungi oleh `.gitignore`.
