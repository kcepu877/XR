#!/bin/bash

# Update dan upgrade system
sudo apt update -y && sudo apt upgrade -y

# Install dependensi
sudo apt install git python3.8 python3.8-venv python3.8-dev python3-pip -y

# Clone repository
sudo git clone https://github.com/kcepu877/XR /usr/local/sbin/XR

# Masuk ke direktori
cd /usr/local/sbin/XR || exit

# Buat virtual environment dengan Python 3.8
python3.8 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install system packages (jika diperlukan)
sudo apt install python3-pil python3-pil.imagetk -y  # Untuk Pillow system package

# Install Python dependencies
pip install --upgrade rich
pip install Pillow  # Nama package yang benar

# Install dari requirements.txt jika ada
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

# Fix untuk Python 3.8: Tambahkan future imports ke semua file Python
echo "Memperbaiki file Python untuk kompatibilitas Python 3.8..."

# Gunakan find dengan path lengkap
find /usr/local/sbin/XR -name "*.py" -type f | while read -r file; do
    # Cek jika file ada dan bisa dibaca
    if [ -f "$file" ] && [ -r "$file" ]; then
        # Cek jika belum ada __future__ import
        if ! head -5 "$file" | grep -q "from __future__ import"; then
            # Backup file
            cp "$file" "${file}.backup"
            # Tambahkan future import di baris pertama
            sed -i '1s/^/from __future__ import annotations, print_function\n/' "$file"
            echo "✓ Diperbaiki: $file"
        fi
    fi
done

echo "Setup selesai!"
echo "Virtual environment aktif di: /usr/local/sbin/XR/venv"
echo "Untuk mengaktifkan: source /usr/local/sbin/XR/venv/bin/activate"
