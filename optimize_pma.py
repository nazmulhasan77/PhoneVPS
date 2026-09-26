import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

# 1. Update config.inc.php with error reporting fix & absolute URI for Cloudflare HTTPS
config_inc = """<?php
declare(strict_types=1);

error_reporting(E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING);
ini_set('display_errors', '0');

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

/* Directories for saving/loading files from server */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';
$cfg['TempDir'] = __DIR__ . '/tmp';

/* HTTPS and URL configuration */
$cfg['PmaAbsoluteUri'] = 'https://vps.shokherpolli.com/phpmyadmin/';
$cfg['ForceSSL'] = false;
$cfg['SendErrorReports'] = 'never';
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/phpmyadmin/config.inc.php', 'w') as f:
    f.write(config_inc)

# 2. Update php.ini to suppress E_DEPRECATED
php_ini_content = """[PHP]
error_reporting = E_ALL & ~E_DEPRECATED & ~E_NOTICE & ~E_WARNING
display_errors = Off
display_startup_errors = Off
upload_max_filesize = 128M
post_max_size = 128M
memory_limit = 256M
"""
with sftp.file('/data/data/com.termux/files/usr/etc/php.ini', 'w') as f:
    f.write(php_ini_content)

# 3. Update Nginx configuration with proper proxy headers
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

        # Official phpMyAdmin
        location /phpmyadmin/ {
            proxy_pass http://127.0.0.1:8081/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto https;
            proxy_set_header HTTPS on;
        }

        location = /phpmyadmin {
            return 301 /phpmyadmin/;
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
            proxy_set_header X-Forwarded-Proto https;
        }
    }
}
"""
with sftp.file('/data/data/com.termux/files/usr/etc/nginx/nginx.conf', 'w') as f:
    f.write(nginx_conf)

stdin, stdout, stderr = client.exec_command("chmod +x ~/phonevps/*.sh && bash ~/phonevps/start.sh")
print(stdout.read().decode())

time.sleep(3)
client.close()
