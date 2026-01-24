sudo apt update -y && sudo apt upgrade -y
sudo apt install git -y
python3.8 -m venv venv
source venv/bin/activate

git clone https://github.com/kcepu877/XR /usr/local/sbin

cd XR
apt update -y
apt install python -y
apt install python-pillow -y
pip install --upgrade rich
pip install -r requirements.txt

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

