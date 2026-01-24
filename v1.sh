sudo apt update && sudo apt install -y git python3.8 python3.8-venv

python3.8 -m venv venv
source venv/bin/activate

cd /usr/local/sbin
git clone https://github.com/kcepu877/XR

cd XR
pip install --upgrade pip
pip install rich
pip install -r requirements.txt


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

# Tambahkan ke SEMUA file Python di project
find  -name "*.py" -type f | while read file; do
    # Cek jika belum ada future import
    if ! head -5 "$file" | grep -q "__future__"; then
        # Backup
        cp "$file" "${file}.backup"
        # Tambahkan di baris pertama
        sed -i '1s/^/from __future__ import annotations\n/' "$file"
        echo "Fixed: $file"
    fi
done

