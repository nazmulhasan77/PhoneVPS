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

# 1. Update phpMyAdmin config.inc.php
print("--- 1. Updating phpMyAdmin config.inc.php ---")
pma_config = """<?php
declare(strict_types=1);

$_SERVER['HTTPS'] = 'on';
$_SERVER['SERVER_PORT'] = '443';
$_SERVER['HTTP_HOST'] = 'vps.shokherpolli.com';
$_SERVER['SERVER_NAME'] = 'vps.shokherpolli.com';

error_reporting(0);
ini_set('display_errors', '0');
ini_set('upload_max_filesize', '500M');
ini_set('post_max_size', '500M');
ini_set('memory_limit', '512M');
ini_set('max_execution_time', '600');
ini_set('max_input_time', '600');

$cfg['blowfish_secret'] = 'phonevps-pma-super-secret-key-32-chars-long!';

$i = 0;
$i++;

/* Authentication type */
$cfg['Servers'][$i]['auth_type'] = 'cookie';
$cfg['Servers'][$i]['host'] = '127.0.0.1';
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['connect_type'] = 'tcp';
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = true;
$cfg['Servers'][$i]['hide_db'] = '^(information_schema|performance_schema|sys)$';

/* Directories */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';
$cfg['TempDir'] = __DIR__ . '/tmp';

/* HTTPS and URL configuration */
$cfg['PmaAbsoluteUri'] = 'https://vps.shokherpolli.com/phpmyadmin/';
$cfg['ExecTimeLimit'] = 600;
$cfg['SendErrorReports'] = 'never';
"""

sftp = client.open_sftp()
with sftp.open("/data/data/com.termux/files/home/phonevps/phpmyadmin/config.inc.php", "w") as f:
    f.write(pma_config)
print("phpMyAdmin config.inc.php updated.")

# 2. Update Nginx configuration
print("--- 2. Updating Nginx config ---")
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
    
    port_in_redirect off;
    absolute_redirect off;

    server {
        listen 8080;
        server_name _;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;

        # phpMyAdmin redirect for non-trailing slash
        location = /phpmyadmin {
            return 301 /phpmyadmin/;
        }

        # phpMyAdmin
        location /phpmyadmin/ {
            client_max_body_size 500M;
            proxy_pass http://127.0.0.1:8081/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port 443;
            proxy_redirect http://127.0.0.1:8081/ /phpmyadmin/;
            proxy_redirect http://127.0.0.1:8080/phpmyadmin/ /phpmyadmin/;
            proxy_read_timeout 600s;
            proxy_send_timeout 600s;
            proxy_connect_timeout 60s;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }

        # Laravel Inventory redirect for non-trailing slash
        location = /inventory {
            return 301 /inventory/;
        }

        # Laravel Inventory
        location /inventory/ {
            rewrite ^/inventory/(.*)$ /$1 break;
            proxy_pass http://127.0.0.1:8082;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port 443;
            proxy_set_header X-Forwarded-Prefix /inventory;
            proxy_redirect http://127.0.0.1:8082/ /inventory/;
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

with sftp.open("/data/data/com.termux/files/usr/etc/nginx/nginx.conf", "w") as f:
    f.write(nginx_conf)
sftp.close()
print("Nginx configuration updated.")

# 3. Restart services
print("--- 3. Restarting Services ---")
run("bash ~/phonevps/start.sh")
time.sleep(2)

# 4. Test redirects with curl
print("--- 4. Testing Endpoints & Redirects ---")
run("curl -s -I -H 'Host: vps.shokherpolli.com' http://127.0.0.1:8080/phpmyadmin")
run("curl -s -I -H 'Host: vps.shokherpolli.com' http://127.0.0.1:8080/phpmyadmin/")
run("curl -s -I -H 'Host: vps.shokherpolli.com' http://127.0.0.1:8080/inventory")
run("curl -s -I -H 'Host: vps.shokherpolli.com' http://127.0.0.1:8080/inventory/")

client.close()
