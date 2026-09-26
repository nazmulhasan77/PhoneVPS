#!/data/data/com.termux/files/usr/bin/bash

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
