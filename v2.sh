#!/bin/bash

# Update dan upgrade system
sudo apt update -y && sudo apt upgrade -y

# Install dependensi
sudo apt install git python3.8 python3.8-venv python3.8-dev python3-pip -y
cd /usr/local/sbin
# Clone repository
sudo git clone https://github.com/kcepu877/XR /usr/local/sbin/XR
python3.8 -m venv venv

# Aktifkan virtual environment
source venv/bin/activate
# Masuk ke direktori
cd XR || exit

# Buat virtual environment dengan Python 3.8


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

# Buat script untuk fix semua Union types
cat > fix_union_types.py << 'EOF'
import os
import re

def fix_union_types_in_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern untuk menemukan type hints dengan |
    # Contoh: str | None, int | str, etc.
    patterns = [
        (r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*None', r': Optional[\1]'),
        (r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|\s*([a-zA-Z_][a-zA-Z0-9_]*)', r': Union[\1, \2]'),
        (r'Optional\[([^]]+)\]', r'Optional[\1]'),  # Sudah Optional
    ]
    
    original = content
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Tambah import typing jika belum ada
    if 'Union' in content or 'Optional' in content:
        if 'from typing import' not in content and 'import typing' not in content:
            # Cari baris pertama setelah docstring atau import
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    # Masukkan setelah import
                    lines.insert(i+1, 'from typing import Union, Optional')
                    break
                elif line.strip() and not line.startswith('#'):
                    # Masukkan di awal
                    lines.insert(0, 'from typing import Union, Optional')
                    lines.insert(1, '')
                    break
            content = '\n'.join(lines)
    
    if content != original:
        print(f"Fixed: {filepath}")
        with open(filepath, 'w') as f:
            f.write(content)
        return True
    return False

# Scan semua file Python
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            fix_union_types_in_file(filepath)
EOF

# Jalankan fix script
python fix_union_types.py

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
