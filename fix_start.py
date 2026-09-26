import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

TOKEN = "eyJhIjoiOWY0YjdjOWU3MTUyZDM1OTIwYWI5YjQ2OWVhMWMwMGYiLCJ0IjoiZDgwY2JiZjktOTYxYy00NjkyLThhYzctYTc1MzhiNTM5N2RlIiwicyI6Ik9UZGtZekZpT1RRdFltRXlNQzAwTmprekxXSmhNR010TURZMVptTTJOekF5WlRGayJ9"
DOMAIN = "https://vps.shokherpolli.com"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

start_sh = f"""#!/data/data/com.termux/files/usr/bin/bash

# 1. Start MariaDB (MySQL)
if ! pgrep -f "mariadbd" > /dev/null; then
    mariadbd-safe --nowatch > /dev/null 2>&1
    sleep 2
fi

# 2. Start Node.js API Server
pkill -f "node server.js" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps
nohup node server.js </dev/null >/data/data/com.termux/files/home/phonevps/logs/node.log 2>&1 &
disown

# 3. Start Nginx
pkill -f "nginx" 2>/dev/null
nginx 2>/dev/null

# 4. Start Cloudflare Tunnel
pkill -f "cloudflared" 2>/dev/null
nohup cloudflared tunnel run --token "{TOKEN}" </dev/null >/data/data/com.termux/files/home/phonevps/logs/cf.log 2>&1 &
disown

echo "Services started successfully."
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/start.sh', 'w') as f:
    f.write(start_sh)

stdin, stdout, stderr = client.exec_command("chmod +x ~/phonevps/*.sh && bash ~/phonevps/start.sh")
print(stdout.read().decode())

time.sleep(3)

stdin, stdout, stderr = client.exec_command("bash ~/phonevps/status.sh")
print(stdout.read().decode())

client.close()
