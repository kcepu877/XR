pkg update && pkg upgrade -y
pkg install git -y
git clone https://github.com/kcepu877/xr
cd XR
bash setup.sh
python main.py
