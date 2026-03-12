#!/bin/bash

# Script to setup Oasis Discord Bot on a Linux VPS
# Usage: bash setup_vps.sh

echo "--- Oasis Discord Bot: VPS Setup ---"

# 1. Update system
echo "[1/6] Memperbarui sistem..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Python and dependencies
echo "[2/6] Menginstal Python 3 dan venv..."
sudo apt-get install -y python3 python3-venv python3-pip git

# 3. Setup Virtual Environment
echo "[3/6] Menyiapkan Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install requirements
echo "[4/6] Menginstal dependensi bot..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Setup Environment File
if [ ! -f .env ]; then
    echo "[5/6] Menyiapkan file .env dari .env.example..."
    cp .env.example .env
    echo "PENTING: Jangan lupa isi DISCORD_TOKEN di file .env!"
else
    echo "[5/6] File .env sudah ada, melewati langkah ini."
fi

# 6. Setup Systemd Service
echo "[6/6] Mengonfigurasi systemd service..."
# Sesuaikan path dalam file service jika user berbeda dari 'administrator'
CURRENT_USER=$(whoami)
SERVICE_FILE="scripts/oasis-bot.service"

if [ "$CURRENT_USER" != "administrator" ]; then
    echo "Menyesuaikan User dan Path di $SERVICE_FILE..."
    sed -i "s/User=administrator/User=$CURRENT_USER/g" $SERVICE_FILE
    sed -i "s/Group=administrator/Group=$CURRENT_USER/g" $SERVICE_FILE
    sed -i "s/\/home\/administrator/\/home\/$CURRENT_USER/g" $SERVICE_FILE
fi

sudo cp $SERVICE_FILE /etc/systemd/system/oasis-bot.service
sudo systemctl daemon-reload
sudo systemctl enable oasis-bot

echo "--- Setup Selesai ---"
echo "Langkah selanjutnya:"
echo "1. Edit file .env dan masukkan token bot Anda."
echo "2. Jalankan bot dengan: sudo systemctl start oasis-bot"
echo "3. Cek status dengan: systemctl status oasis-bot"
echo "4. Cek log dengan: tail -f logs/bot.log"
