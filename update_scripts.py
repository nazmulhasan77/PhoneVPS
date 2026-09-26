import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

start_sh = """#!/data/data/com.termux/files/usr/bin/bash

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

# 4. Start Cloudflare Tunnel
pkill -f "cloudflared" 2>/dev/null
echo "[4/4] Starting Cloudflare Tunnel..."
nohup cloudflared tunnel --url http://127.0.0.1:8080 > ~/phonevps/logs/cf.log 2>&1 &

echo "Waiting for Cloudflare Public Tunnel URL..."
sleep 6

CF_URL=$(grep -o 'https://[a-zA-Z0-9.-]*trycloudflare.com' ~/phonevps/logs/cf.log | tail -n 1)

echo "=================================================="
echo "           PhoneVPS IS FULLY ACTIVE!              "
echo "=================================================="
echo "Local Proxy (Nginx) : http://127.0.0.1:8080"
echo "Node.js API Port    : http://127.0.0.1:3000"
echo "MariaDB MySQL Port  : 3306 (phonevps_db)"
echo "Public Worldwide URL: $CF_URL"
echo "=================================================="
"""

status_sh = """#!/data/data/com.termux/files/usr/bin/bash
echo "=== PhoneVPS Live Status ==="
echo -n "MariaDB: "
pgrep -f "mariadbd" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Node.js: "
pgrep -f "node server.js" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Nginx: "
pgrep -f "nginx" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Cloudflare Tunnel: "
pgrep -f "cloudflared" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"

CF_URL=$(grep -o 'https://[a-zA-Z0-9.-]*trycloudflare.com' ~/phonevps/logs/cf.log | tail -n 1)
echo "----------------------------------------"
echo "Public URL: $CF_URL"
echo "----------------------------------------"
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/start.sh', 'w') as f:
    f.write(start_sh)

with sftp.file('/data/data/com.termux/files/home/phonevps/status.sh', 'w') as f:
    f.write(status_sh)

stdin, stdout, stderr = client.exec_command("chmod +x ~/phonevps/*.sh && bash ~/phonevps/status.sh")
print(stdout.read().decode())
client.close()
