import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

LARAVEL_DIR = "/data/data/com.termux/files/home/phonevps/inventory/inventory"
LOGS_DIR = "/data/data/com.termux/files/home/phonevps/logs"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

def run(cmd, timeout=60):
    print(f"\n[EXEC] {cmd[:100]}...")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print("[OUT]:", out)
    if err: print("[ERR]:", err[:300])
    return out, err

# Step 1: Update .env for Laravel
print("=== 1. Updating Laravel .env ===")
# Note: DB_PASSWORD="" because Termux MariaDB root has no password.
# APP_URL="https://vps.shokherpolli.com/inventory"
run(f"""cat << 'EOF' > {LARAVEL_DIR}/.env
APP_NAME="Butterfly Devs"
APP_TITLE="Butterfly Devs"
APP_ENV="production"
APP_KEY=base64:W8UqtE9LHZW+gRag78o4BCbN1M0w4HdaIFdLqHJ/9PA=
APP_DEBUG="false"
APP_LOG_LEVEL=debug
APP_URL="https://vps.shokherpolli.com/inventory"
APP_LOCALE=en
APP_TIMEZONE="Asia/Dhaka"

ADMINISTRATOR_USERNAMES=butterflydevs
ALLOW_REGISTRATION=true

LOG_CHANNEL=daily

DB_CONNECTION=mysql
DB_HOST="127.0.0.1"
DB_PORT="3306"
DB_DATABASE="butterf3_ims"
DB_USERNAME="root"
DB_PASSWORD=""

BROADCAST_DRIVER=log
CACHE_DRIVER=file
SESSION_DRIVER=file
QUEUE_CONNECTION=sync

REDIS_HOST=127.0.0.1
REDIS_PASSWORD=null
REDIS_PORT=6379

MAIL_MAILER="log"

FILESYSTEM_DISK=local
BACKUP_DISK="local"
ENABLE_RECAPTCHA="false"
EOF
""")

# Step 2: Storage permissions & clear cache
print("\n=== 2. Permissions & Cache Clear ===")
run(f"chmod -R 777 {LARAVEL_DIR}/storage {LARAVEL_DIR}/bootstrap/cache")
run(f"cd {LARAVEL_DIR} && php artisan storage:link 2>/dev/null || true")
run(f"cd {LARAVEL_DIR} && php artisan optimize:clear")

# Step 3: Test MariaDB connection from artisan
print("\n=== 3. Testing DB Connection ===")
run(f"cd {LARAVEL_DIR} && php artisan db:show || php -r \"new PDO('mysql:host=127.0.0.1;dbname=butterf3_ims', 'root', ''); echo 'DB connected successfully\n';\"")

# Step 4: Configure Nginx
print("\n=== 4. Updating Nginx Configuration ===")
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
sftp.close()

run("nginx -t")

# Step 5: Update start.sh, stop.sh, status.sh
print("\n=== 5. Updating Service Scripts ===")

start_sh = """#!/data/data/com.termux/files/usr/bin/bash

# 1. Start MariaDB (MySQL) with 500M max_allowed_packet
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

echo "All PhoneVPS services started successfully."
"""

stop_sh = """#!/data/data/com.termux/files/usr/bin/bash

pkill -9 -f "cloudflared" 2>/dev/null
pkill -9 -f "nginx" 2>/dev/null
pkill -9 -f "node server.js" 2>/dev/null
pkill -9 -f "php -S 127.0.0.1:8081" 2>/dev/null
pkill -9 -f "php -S 127.0.0.1:8082" 2>/dev/null
pkill -9 -f "mariadbd" 2>/dev/null

echo "All PhoneVPS services stopped."
"""

status_sh = """#!/data/data/com.termux/files/usr/bin/bash

check() {
    if pgrep -f "$1" > /dev/null; then
        printf "%-20s: [RUNNING]\\n" "$2"
    else
        printf "%-20s: [STOPPED]\\n" "$2"
    fi
}

echo "=========================================="
echo "         PhoneVPS Live Status Check       "
echo "=========================================="
check "mariadbd" "MariaDB (MySQL)"
check "127.0.0.1:8081" "phpMyAdmin (8081)"
check "127.0.0.1:8082" "Laravel IMS (8082)"
check "node server.js" "Node.js Engine"
check "nginx" "Nginx Proxy"
check "cloudflared" "Cloudflare Tunnel"
echo "------------------------------------------"
echo "Custom Domain     : https://vps.shokherpolli.com"
echo "phpMyAdmin URL    : https://vps.shokherpolli.com/phpmyadmin/"
echo "Inventory URL     : https://vps.shokherpolli.com/inventory"
echo "File Manager URL  : https://vps.shokherpolli.com/files"
echo "=========================================="
"""

sftp = client.open_sftp()
with sftp.open("/data/data/com.termux/files/home/phonevps/start.sh", "w") as f:
    f.write(start_sh)
with sftp.open("/data/data/com.termux/files/home/phonevps/stop.sh", "w") as f:
    f.write(stop_sh)
with sftp.open("/data/data/com.termux/files/home/phonevps/status.sh", "w") as f:
    f.write(status_sh)
sftp.close()

run("chmod +x ~/phonevps/*.sh")

# Step 6: Start/Restart all services
print("\n=== 6. Restarting All Services ===")
run("bash ~/phonevps/start.sh")
time.sleep(3)

# Step 7: Check Status & Test endpoints
print("\n=== 7. Live Service Check ===")
run("bash ~/phonevps/status.sh")

print("\n=== 8. HTTP Test (Local curl) ===")
run("curl -s -I http://127.0.0.1:8081/ | head -n 5")
run("curl -s -I http://127.0.0.1:8082/ | head -n 5")
run("curl -s -I http://127.0.0.1:8080/phpmyadmin/ | head -n 5")
run("curl -s -I http://127.0.0.1:8080/inventory | head -n 5")

client.close()
