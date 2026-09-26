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

# 1. Update php.ini
php_ini = """[PHP]
upload_max_filesize = 500M
post_max_size = 500M
memory_limit = 512M
max_execution_time = 600
max_input_time = 600
error_reporting = E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING
display_errors = Off
display_startup_errors = Off
"""
with sftp.file('/data/data/com.termux/files/usr/etc/php.ini', 'w') as f:
    f.write(php_ini)

# 2. Update config.inc.php with ExecTimeLimit
config_inc = """<?php
declare(strict_types=1);

$_SERVER['HTTPS'] = 'on';
$_SERVER['SERVER_PORT'] = '443';

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
with sftp.file('/data/data/com.termux/files/home/phonevps/phpmyadmin/config.inc.php', 'w') as f:
    f.write(config_inc)

# 3. Update Nginx configuration with client_max_body_size 500M
nginx_conf = """worker_processes 1;

events {
    worker_connections 1024;
}

http {
    include /data/data/com.termux/files/usr/etc/nginx/mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    client_max_body_size 500M;

    server {
        listen 8080;
        server_name localhost;
        client_max_body_size 500M;

        # Official phpMyAdmin
        location /phpmyadmin/ {
            proxy_pass http://127.0.0.1:8081/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header HTTPS on;
            proxy_read_timeout 600s;
            proxy_connect_timeout 600s;
            proxy_send_timeout 600s;
            client_max_body_size 500M;
        }

        location = /phpmyadmin {
            return 301 /phpmyadmin/;
        }

        # Main App & Node.js Engine Route
        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_read_timeout 600s;
            client_max_body_size 500M;
        }
    }
}
"""
with sftp.file('/data/data/com.termux/files/usr/etc/nginx/nginx.conf', 'w') as f:
    f.write(nginx_conf)

# 4. Update start.sh with explicit 500M flags for PHP and MariaDB
start_sh = f"""#!/data/data/com.termux/files/usr/bin/bash

# 1. Start MariaDB (MySQL) with 500M max_allowed_packet
if ! pgrep -f "mariadbd" > /dev/null; then
    mariadbd-safe --nowatch --max_allowed_packet=500M > /dev/null 2>&1
    sleep 2
fi

# 2. Start Official phpMyAdmin with 500MB upload limits
pkill -f "php -S 127.0.0.1:8081" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps/phpmyadmin
nohup php -d error_reporting=0 -d display_errors=0 -d upload_max_filesize=500M -d post_max_size=500M -d memory_limit=512M -d max_execution_time=600 -d max_input_time=600 -S 127.0.0.1:8081 </dev/null >/data/data/com.termux/files/home/phonevps/logs/php.log 2>&1 &
disown

# 3. Start Node.js Server
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

echo "All PhoneVPS services restarted with 500MB upload limit."
"""
with sftp.file('/data/data/com.termux/files/home/phonevps/start.sh', 'w') as f:
    f.write(start_sh)

# Also sync local nginx.conf & start.sh
try:
    with open("src/config/nginx.conf", "w") as f:
        f.write(nginx_conf)
    with open("src/start.sh", "w") as f:
        f.write(start_sh)
except:
    pass

stdin, stdout, stderr = client.exec_command("chmod +x ~/phonevps/*.sh && bash ~/phonevps/start.sh")
print(stdout.read().decode())

time.sleep(3)
client.close()
