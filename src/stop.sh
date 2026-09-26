#!/data/data/com.termux/files/usr/bin/bash
echo "=== Stopping PhoneVPS Services ==="
pkill -f "cloudflared"
pkill -f "nginx"
pkill -f "node server.js"
mariadb-admin -u root shutdown 2>/dev/null || pkill -f mariadbd
echo "All PhoneVPS services have been stopped."
