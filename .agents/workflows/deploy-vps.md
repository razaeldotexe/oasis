---
description: Panduan deploy bot Oasis ke VPS Linux (Production Ready)
---

# Deployment ke VPS Linux

Ikuti langkah-langkah ini untuk menjalankan bot Oasis di VPS Linux Anda.

## Prasyarat
- VPS dengan sistem operasi Linux (Ubuntu/Debian direkomendasikan).
- Akses SSH ke VPS.
- Token Discord Bot yang valid.

## Langkah-langkah Deployment

1. **Clone Repositori**
   Masuk ke VPS dan clone proyek Anda:
   ```bash
   git clone <url-repo-anda> oasis
   cd oasis
   ```

2. **Jalankan Script Setup**
   Kami telah menyediakan script untuk otomasi instalasi:
   ```bash
   bash scripts/setup_vps.sh
   ```
   Script ini akan:
   - Menginstal Python dan venv.
   - Mengatur virtual environment dan menginstal dependensi.
   - Menyiapkan file `.env`.
   - Mendaftarkan bot sebagai systemd service.

3. **Konfigurasi API Token**
   Edit file `.env` dan masukkan token bot Anda:
   ```bash
   nano .env
   ```
   Cari baris `DISCORD_TOKEN=` dan isi dengan token dari Discord Developer Portal.

4. **Menjalankan Bot**
   Aktifkan bot menggunakan systemd:
   ```bash
   sudo systemctl start oasis-bot
   ```

5. **Monitoring dan Log**
   - Cek status: `systemctl status oasis-bot`
   - Cek log bot: `tail -f logs/bot.log`
   - Cek log error: `tail -f logs/error.log`

6. **Menghentikan Bot**
   ```bash
   sudo systemctl stop oasis-bot
   ```

7. **Update Bot**
   Jika ada perubahan kode baru:
   ```bash
   git pull
   pip install -r requirements.txt
   sudo systemctl restart oasis-bot
   ```
