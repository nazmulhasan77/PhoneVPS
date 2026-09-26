#!/data/data/com.termux/files/usr/bin/bash

# 1. Start MariaDB (MySQL)
if ! pgrep -f "mariadbd" > /dev/null; then
    mariadbd-safe --nowatch > /dev/null 2>&1
    sleep 2
fi

# 2. Start Official phpMyAdmin with Clean Zero Errors Flag
pkill -f "php -S 127.0.0.1:8081" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps/phpmyadmin
nohup php -d error_reporting=0 -d display_errors=0 -d display_startup_errors=0 -S 127.0.0.1:8081 </dev/null >/data/data/com.termux/files/home/phonevps/logs/php.log 2>&1 &
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
nohup cloudflared tunnel run --token "eyJhIjoiOWY0YjdjOWU3MTUyZDM1OTIwYWI5YjQ2OWVhMWMwMGYiLCJ0IjoiZDgwY2JiZjktOTYxYy00NjkyLThhYzctYTc1MzhiNTM5N2RlIiwicyI6Ik9UZGtZekZpT1RRdFltRXlNQzAwTmprekxXSmhNR010TURZMVptTTJOekF5WlRGayJ9" </dev/null >/data/data/com.termux/files/home/phonevps/logs/cf.log 2>&1 &
disown

echo "All PhoneVPS services started successfully."
