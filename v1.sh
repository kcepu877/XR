sudo apt update && sudo apt install python3.10 python3.10-venv -y
python3.10 -m venv venv
source venv/bin/activate

cd /usr/local/sbin
git clone https://github.com/kcepu877/XR

cd XR
pip install --upgrade pip
pip install rich
pip install -r requirements.txt


