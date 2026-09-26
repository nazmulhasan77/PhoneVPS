import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

def run(cmd, timeout=30):
    print(f"\n[RUN] {cmd[:80]}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print("[OUT]:", out)
    if err and "Deprecated" not in err: print("[ERR]:", err[:300])
    return out, err

# 1. Update Nginx Config
print("--- 1. Writing Nginx Config ---")
nginx_conf = """worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 500M;

    server {
        listen 8080;
        server_name _;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        # phpMyAdmin
        location /phpmyadmin/ {
            client_max_body_size 500M;
            proxy_pass http://127.0.0.1:8081/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_read_timeout 600s;
            proxy_send_timeout 600s;
            proxy_connect_timeout 60s;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }

        # Laravel Inventory
        location /inventory {
            rewrite ^/inventory/(.*)$ /$1 break;
            rewrite ^/inventory$ / break;
            proxy_pass http://127.0.0.1:8082;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header X-Forwarded-Prefix /inventory;
            proxy_read_timeout 300s;
            client_max_body_size 100M;
        }

        # Node.js main app
        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
        }
    }
}
"""

sftp = client.open_sftp()
with sftp.open("/data/data/com.termux/files/usr/etc/nginx/nginx.conf", "w") as f:
    f.write(nginx_conf)
print("Nginx config written.")

# 2. Update start.sh
start_sh = """#!/data/data/com.termux/files/usr/bin/bash

# 1. Start MariaDB (MySQL)
if ! pgrep -f "mariadbd" > /dev/null; then
    mariadbd-safe --nowatch --max_allowed_packet=500M > /dev/null 2>&1
    sleep 2
fi

# 2. Start Official phpMyAdmin (Port 8081)
pkill -9 -f "php -S 127.0.0.1:8081" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps/phpmyadmin
nohup php -d error_reporting=0 -d display_errors=0 -d upload_max_filesize=500M -d post_max_size=500M -d memory_limit=512M -d max_execution_time=600 -d max_input_time=600 -S 127.0.0.1:8081 </dev/null >/data/data/com.termux/files/home/phonevps/logs/php.log 2>&1 &
disown

# 3. Start Laravel Inventory System (Port 8082)
pkill -9 -f "php -S 127.0.0.1:8082" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps/inventory/inventory/public
nohup php -d error_reporting=0 -d display_errors=0 -d upload_max_filesize=100M -d post_max_size=100M -d memory_limit=512M -d max_execution_time=300 -S 127.0.0.1:8082 </dev/null >/data/data/com.termux/files/home/phonevps/logs/inventory.log 2>&1 &
disown

# 4. Start Node.js Server (Port 3000)
pkill -9 -f "node server.js" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps
nohup node server.js </dev/null >/data/data/com.termux/files/home/phonevps/logs/node.log 2>&1 &
disown

# 5. Start Nginx
pkill -9 -f "nginx" 2>/dev/null
sleep 1
nginx 2>/dev/null

# 6. Start Cloudflare Tunnel
if ! pgrep -f "cloudflared" > /dev/null; then
    nohup cloudflared tunnel run --token "eyJhIjoiOWY0YjdjOWU3MTUyZDM1OTIwYWI5YjQ2OWVhMWMwMGYiLCJ0IjoiZDgwY2JiZjktOTYxYy00NjkyLThhYzctYTc1MzhiNTM5N2RlIiwicyI6Ik9UZGtZekZpT1RRdFltRXlNQzAwTmprekxXSmhNR010TURZMVptTTJOekF5WlRGayJ9" </dev/null >/data/data/com.termux/files/home/phonevps/logs/cf.log 2>&1 &
    disown
fi

echo "All PhoneVPS services restarted."
"""

status_sh = """#!/data/data/com.termux/files/usr/bin/bash

check() {
    if pgrep -f "$1" > /dev/null; then
        printf "%-22s: [RUNNING]\\n" "$2"
    else
        printf "%-22s: [STOPPED]\\n" "$2"
    fi
}

echo "=========================================="
echo "         PhoneVPS Live Status Check       "
echo "=========================================="
check "mariadbd" "MariaDB (MySQL)"
check "127.0.0.1:8081" "phpMyAdmin (8081)"
check "127.0.0.1:8082" "Laravel IMS (8082)"
check "node server.js" "Node.js Engine (3000)"
check "nginx" "Nginx Proxy (8080)"
check "cloudflared" "Cloudflare Tunnel"
echo "------------------------------------------"
echo "Custom Domain     : https://vps.shokherpolli.com"
echo "phpMyAdmin URL    : https://vps.shokherpolli.com/phpmyadmin/"
echo "Inventory URL     : https://vps.shokherpolli.com/inventory"
echo "File Manager URL  : https://vps.shokherpolli.com/files"
echo "=========================================="
"""

with sftp.open("/data/data/com.termux/files/home/phonevps/start.sh", "w") as f:
    f.write(start_sh)
with sftp.open("/data/data/com.termux/files/home/phonevps/status.sh", "w") as f:
    f.write(status_sh)
sftp.close()

# 3. Start everything
print("--- 2. Starting all services ---")
run("bash ~/phonevps/start.sh")
time.sleep(3)

# 4. Check Status
print("--- 3. Checking status ---")
run("bash ~/phonevps/status.sh")

# 5. Test local curls
print("--- 4. Testing Endpoints Locally ---")
run("curl -s -I http://127.0.0.1:8081/ | head -n 5")
run("curl -s -I http://127.0.0.1:8082/ | head -n 5")
run("curl -s -I http://127.0.0.1:8080/phpmyadmin/ | head -n 5")
run("curl -s -I http://127.0.0.1:8080/inventory | head -n 5")

client.close()
