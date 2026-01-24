#!/usr/bin/env bash
set -e

echo "[*] Update system & install Python 3.10..."
sudo apt update
sudo apt install -y python3.10 python3.10-venv git

cd /usr/local/sbin

# Buat venv di /usr/local/sbin
if [ ! -d "venv" ]; then
    echo "[*] Membuat virtual environment (Python 3.10)..."
    python3.10 -m venv venv
fi

echo "[*] Aktifkan virtual environment..."
source venv/bin/activate

# Clone repo XR
if [ ! -d "XR" ]; then
    echo "[*] Clone repository XR..."
    git clone https://github.com/kcepu877/XR
else
    echo "[*] Repo XR sudah ada, skip clone"
fi

echo "[*] Masuk ke XR..."
cd XR

echo "[*] Upgrade pip..."
pip install --upgrade pip

echo "[*] Install dependency..."
pip install rich
pip install -r requirements.txt

echo "[✓] Setup selesai"
echo
echo "[*] Untuk menjalankan:"
echo "cd /usr/local/sbin"
echo "source venv/bin/activate"
echo "cd XR"
echo "python main.py"
