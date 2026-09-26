import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

LARAVEL_PATH = "/data/data/com.termux/files/home/phonevps/inventory/inventory"
PHP_LOG = "/data/data/com.termux/files/home/phonevps/logs"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

def run(cmd, timeout=60):
    print(f"\n>>> {cmd[:80]}...")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err and "Deprecated" not in err and "deprecated" not in err:
        print(f"[ERR] {err[:300]}")
    return out, err

print("=" * 60)
print("STEP 1: Fix phpMyAdmin (restart PHP on 8081)")
print("=" * 60)
run("pkill -9 -f 'php -S 127.0.0.1:8081' 2>/dev/null; sleep 1")
run(f"cd /data/data/com.termux/files/home/phonevps/phpmyadmin && nohup php -d error_reporting=0 -d display_errors=0 -d upload_max_filesize=500M -d post_max_size=500M -d memory_limit=512M -d max_execution_time=600 -d max_input_time=600 -S 127.0.0.1:8081 </dev/null >{PHP_LOG}/php.log 2>&1 & disown")
time.sleep(2)
out, _ = run("pgrep -f 'php -S 127.0.0.1:8081' && echo PMA_OK")
print("phpMyAdmin PHP:", "RUNNING OK" if "PMA_OK" in out else "FAILED")

print("\n" + "=" * 60)
print("STEP 2: Create Laravel .env")
print("=" * 60)

env_content = """APP_NAME="Inventory System"
APP_ENV=production
APP_KEY=
APP_DEBUG=false
APP_URL=https://vps.shokherpolli.com

LOG_CHANNEL=stack

DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=butterf3_ims
DB_USERNAME=root
DB_PASSWORD=

BROADCAST_DRIVER=log
CACHE_DRIVER=file
QUEUE_CONNECTION=sync
SESSION_DRIVER=file
SESSION_LIFETIME=120

MAIL_MAILER=smtp
MAIL_HOST=smtp.mailtrap.io
MAIL_PORT=2525
MAIL_USERNAME=null
MAIL_PASSWORD=null
MAIL_ENCRYPTION=null

FILESYSTEM_DISK=local
"""

run(f"cat > {LARAVEL_PATH}/.env << 'ENVEOF'\n{env_content}\nENVEOF")

print("\n" + "=" * 60)
print("STEP 3: Generate App Key")
print("=" * 60)
run(f"cd {LARAVEL_PATH} && php artisan key:generate --force", timeout=30)
run(f"grep APP_KEY {LARAVEL_PATH}/.env")

print("\n" + "=" * 60)
print("STEP 4: Storage & Permissions")
print("=" * 60)
run(f"cd {LARAVEL_PATH} && php artisan storage:link --force 2>/dev/null || true", timeout=30)
run(f"chmod -R 775 {LARAVEL_PATH}/storage {LARAVEL_PATH}/bootstrap/cache 2>/dev/null || true")
run(f"cd {LARAVEL_PATH} && php artisan config:clear 2>/dev/null; php artisan cache:clear 2>/dev/null; php artisan view:clear 2>/dev/null", timeout=30)

print("\n" + "=" * 60)
print("STEP 5: Start Laravel PHP server on port 8082")
print("=" * 60)
run("pkill -9 -f 'php -S 127.0.0.1:8082' 2>/dev/null; sleep 1")
run(f"cd {LARAVEL_PATH}/public && nohup php -d error_reporting=0 -d display_errors=0 -d upload_max_filesize=100M -d post_max_size=100M -d memory_limit=256M -S 127.0.0.1:8082 </dev/null >{PHP_LOG}/laravel.log 2>&1 & disown")
time.sleep(2)
out, _ = run("pgrep -f 'php -S 127.0.0.1:8082' && echo LARAVEL_OK")
print("Laravel PHP:", "RUNNING OK" if "LARAVEL_OK" in out else "FAILED")

print("\n" + "=" * 60)
print("STEP 6: Update Nginx config")
print("=" * 60)

nginx_conf = r"""worker_processes 1;

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
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-Content-Type-Options "nosniff";

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
            proxy_pass http://127.0.0.1:8082;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header X-Forwarded-Prefix /inventory;
            proxy_read_timeout 120s;
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

# Write nginx config
sftp = client.open_sftp()
with sftp.open("/data/data/com.termux/files/usr/etc/nginx/nginx.conf", "w") as f:
    f.write(nginx_conf)
sftp.close()
print("Nginx config written OK")

run("nginx -t 2>&1")
run("pkill -f nginx 2>/dev/null; sleep 1; nginx && echo NGINX_OK")

print("\n" + "=" * 60)
print("FINAL STATUS")
print("=" * 60)
run("bash /data/data/com.termux/files/home/phonevps/status.sh")

print("\nURLs:")
print("  phpMyAdmin : https://vps.shokherpolli.com/phpmyadmin/")
print("  Inventory  : https://vps.shokherpolli.com/inventory")

client.close()
