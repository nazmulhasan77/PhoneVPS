#!/data/data/com.termux/files/usr/bin/bash

check() {
    if pgrep -f "$1" > /dev/null; then
        printf "%-22s: [RUNNING]\n" "$2"
    else
        printf "%-22s: [STOPPED]\n" "$2"
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
