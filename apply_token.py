import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

TOKEN = "eyJhIjoiOWY0YjdjOWU3MTUyZDM1OTIwYWI5YjQ2OWVhMWMwMGYiLCJ0IjoiZDgwY2JiZjktOTYxYy00NjkyLThhYzctYTc1MzhiNTM5N2RlIiwicyI6Ik9UZGtZekZpT1RRdFltRXlNQzAwTmprekxXSmhNR010TURZMVptTTJOekF5WlRGayJ9"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

def run(cmd):
    print(f"--> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print("[OUT]:\n" + out.strip())
    if err:
        print("[ERR]:\n" + err.strip())
    return out, err

# Save token in a file
with sftp.file('/data/data/com.termux/files/home/phonevps/tunnel_token.txt', 'w') as f:
    f.write(TOKEN)

start_sh = f"""#!/data/data/com.termux/files/usr/bin/bash

echo "=== [PhoneVPS] Starting All Services ==="

# 1. Start MariaDB
if ! pgrep -f "mariadbd" > /dev/null; then
    echo "[1/4] Starting MariaDB (MySQL)..."
    mariadbd-safe --nowatch > /dev/null 2>&1
    sleep 3
else
    echo "[1/4] MariaDB is already running."
fi

# 2. Start Node.js API server
pkill -f "node server.js" 2>/dev/null
echo "[2/4] Starting Node.js API Server..."
cd /data/data/com.termux/files/home/phonevps
nohup node server.js > ~/phonevps/logs/node.log 2>&1 &
sleep 2

# 3. Start Nginx
pkill -f "nginx" 2>/dev/null
echo "[3/4] Starting Nginx..."
nginx
sleep 1

# 4. Start Cloudflare Named Tunnel
pkill -f "cloudflared" 2>/dev/null
echo "[4/4] Starting Cloudflare Named Tunnel with Custom Token..."
nohup cloudflared tunnel run --token "{TOKEN}" > ~/phonevps/logs/cf.log 2>&1 &

sleep 3

echo "=================================================="
echo "           PhoneVPS IS FULLY ACTIVE!              "
echo "=================================================="
echo "Local Proxy (Nginx) : http://127.0.0.1:8080"
echo "Node.js API Port    : http://127.0.0.1:3000"
echo "MariaDB MySQL Port  : 3306 (phonevps_db)"
echo "Cloudflare Tunnel   : CONNECTED (Custom Domain Active)"
echo "=================================================="
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/start.sh', 'w') as f:
    f.write(start_sh)

run("chmod +x ~/phonevps/*.sh")
run("pkill -f cloudflared")
run(f'nohup cloudflared tunnel run --token "{TOKEN}" > ~/phonevps/logs/cf.log 2>&1 &')

time.sleep(5)
run("cat ~/phonevps/logs/cf.log | tail -n 25")

client.close()
