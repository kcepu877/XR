sudo apt update
sudo apt install -y python3.10 python3.10-venv git
cd /usr/local/sbin
source venv/bin/activate
git clone https://github.com/kcepu877/XR
cd /usr/local/sbin/XR
pip install --upgrade pip
pip install rich
pip install -r requirements.txt
rm -f v1.sh
python main.py
