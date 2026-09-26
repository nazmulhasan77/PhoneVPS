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

# 1. Update Nginx configuration
nginx_conf = """worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include /data/data/com.termux/files/usr/etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;

    server {
        listen 8080;
        server_name localhost;

        # phpMyAdmin / Adminer Web DB Manager
        location /phpmyadmin {
            proxy_pass http://127.0.0.1:8081/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Main Web App & Node.js API
        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""
with sftp.file('/data/data/com.termux/files/usr/etc/nginx/nginx.conf', 'w') as f:
    f.write(nginx_conf)

# 2. Update start.sh to launch PHP server
start_sh = f"""#!/data/data/com.termux/files/usr/bin/bash

# 1. Start MariaDB (MySQL)
if ! pgrep -f "mariadbd" > /dev/null; then
    mariadbd-safe --nowatch > /dev/null 2>&1
    sleep 2
fi

# 2. Start PHP Server for phpMyAdmin
pkill -f "php -S 127.0.0.1:8081" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps/phpmyadmin
nohup php -S 127.0.0.1:8081 </dev/null >/data/data/com.termux/files/home/phonevps/logs/php.log 2>&1 &
disown

# 3. Start Node.js API Server
pkill -f "node server.js" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps
nohup node server.js </dev/null >/data/data/com.termux/files/home/phonevps/logs/node.log 2>&1 &
disown

# 4. Start Nginx
pkill -f "nginx" 2>/dev/null
nginx 2>/dev/null

# 5. Start Cloudflare Tunnel
pkill -f "cloudflared" 2>/dev/null
nohup cloudflared tunnel run --token "{TOKEN}" </dev/null >/data/data/com.termux/files/home/phonevps/logs/cf.log 2>&1 &
disown

echo "All PhoneVPS services started successfully."
"""
with sftp.file('/data/data/com.termux/files/home/phonevps/start.sh', 'w') as f:
    f.write(start_sh)

# 3. Update status.sh
status_sh = f"""#!/data/data/com.termux/files/usr/bin/bash
echo "=========================================="
echo "         PhoneVPS Live Status Check       "
echo "=========================================="
echo -n "MariaDB (MySQL)   : "
pgrep -f "mariadbd" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "PHP DB Manager    : "
pgrep -f "php -S" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Node.js Engine    : "
pgrep -f "node server.js" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Nginx Proxy       : "
pgrep -f "nginx" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Cloudflare Tunnel : "
pgrep -f "cloudflared" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo "------------------------------------------"
echo "Custom Domain     : {DOMAIN}"
echo "phpMyAdmin URL    : {DOMAIN}/phpmyadmin"
echo "File Manager URL  : {DOMAIN}/files"
echo "=========================================="
"""
with sftp.file('/data/data/com.termux/files/home/phonevps/status.sh', 'w') as f:
    f.write(status_sh)

# 4. Update index.html top nav to include phpMyAdmin button
try:
    with sftp.file('/data/data/com.termux/files/home/phonevps/public/index.html', 'r') as f:
        html = f.read().decode('utf-8')
    if 'btn-phpmyadmin' not in html:
        old_bar = '<div class="top-action-bar">'
        new_bar = """<div class="top-action-bar">
                <a href="/files" class="btn-files">
                    <span>📁 Storage & Files (/files)</span>
                </a>
                <a href="/phpmyadmin" class="btn-files" style="background: linear-gradient(135deg, #f59e0b, #ea580c); box-shadow: 0 4px 20px rgba(245, 158, 11, 0.3);">
                    <span>🗄️ phpMyAdmin Database GUI</span>
                </a>"""
        html = html.replace(old_bar, new_bar)
        with sftp.file('/data/data/com.termux/files/home/phonevps/public/index.html', 'w') as f:
            f.write(html)
except Exception as e:
    print(f"Error updating index.html: {e}")

run("chmod +x ~/phonevps/*.sh && bash ~/phonevps/start.sh")
time.sleep(3)
run("bash ~/phonevps/status.sh")

client.close()
