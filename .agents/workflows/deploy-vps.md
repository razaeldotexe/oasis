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

4. **Menjalankan Bot (Dua Opsi)**

   ### Opsi A: Menggunakan Systemd Service (Direkomendasikan)
   Aktifkan bot menggunakan systemd yang telah dikonfigurasi:
   ```bash
   sudo systemctl start oasis-bot
   ```

   ### Opsi B: Menggunakan PM2 (Alternatif)
   Kami telah menyediakan `ecosystem.config.js` agar PM2 menggunakan virtual environment yang benar:
   ```bash
   # Hapus proses lama yang error jika ada
   pm2 delete all
   
   # Jalankan bot dengan konfigurasi ecosystem
   pm2 start ecosystem.config.js
   
   # Simpan agar otomatis jalan saat VPS restart
   pm2 save
   ```

5. **Monitoring dan Log**
   - **Systemd**: `journalctl -u oasis-bot -f` atau `tail -f logs/bot.log`
   - **PM2**: `pm2 logs oasis-bot`

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
