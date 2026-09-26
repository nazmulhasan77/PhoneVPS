# 📱 Complete Step-by-Step Guide: Turn Any Android Phone into a 24/7 Cloud VPS Server

This guide provides a comprehensive, beginner-friendly, and production-ready tutorial for transforming any Android smartphone into a high-performance **Cloud Linux VPS** running **Node.js, MariaDB/MySQL, official phpMyAdmin, Nginx Reverse Proxy, Web File Explorer, and Cloudflare Named Tunnels** with a custom domain and SSL.

---

## 📑 Table of Contents

1. [Hardware & Software Prerequisites](#1-hardware--software-prerequisites)
2. [Step 1: Termux & SSH Setup on Android](#step-1-termux--ssh-setup-on-android)
3. [Step 2: Core Packages Installation](#step-2-core-packages-installation)
4. [Step 3: MariaDB (MySQL) Database Configuration](#step-3-mariadb-mysql-database-configuration)
5. [Step 4: Node.js API Server & Hardware Telemetry](#step-4-nodejs-api-server--hardware-telemetry)
6. [Step 5: Web File Explorer & Storage Manager](#step-5-web-file-explorer--storage-manager)
7. [Step 6: Official phpMyAdmin 5.2.1 Setup](#step-6-official-phpmyadmin-521-setup)
8. [Step 7: Nginx Reverse Proxy Configuration](#step-7-nginx-reverse-proxy-configuration)
9. [Step 8: Cloudflare Zero Trust Tunnel & Custom Domain](#step-8-cloudflare-zero-trust-tunnel--custom-domain)
10. [Step 9: Automation Scripts & Quick Aliases](#step-9-automation-scripts--quick-aliases)
11. [Step 10: 24/7 Background Running & Battery Optimizations](#step-10-247-background-running--battery-optimizations)
12. [Troubleshooting & Maintenance](#troubleshooting--maintenance)

---

## 1. Hardware & Software Prerequisites

- Any Android smartphone (Android 7.0+ recommended).
- Wi-Fi or Mobile Data connection.
- Termux installed from [F-Droid](https://f-droid.org/packages/com.termux/) (Do NOT use Google Play Store version as it is deprecated).
- Free [Cloudflare](https://dash.cloudflare.com) account.
- A custom domain (e.g. from Spaceship, Namecheap, etc.).

---

## Step 1: Termux & SSH Setup on Android

Open Termux on your phone and run:

```bash
# 1. Acquire Wake Lock so Termux never sleeps
termux-wake-lock

# 2. Grant storage access
termux-setup-storage

# 3. Update all core packages
pkg update -y && pkg upgrade -y

# 4. Install OpenSSH
pkg install -y openssh

# 5. Set a password for your Termux user
passwd

# 6. Check your device IP address and username
whoami
ifconfig wlan0 | grep "inet "

# 7. Start SSH server
sshd
```

> **Connect via PC (Optional but convenient):**
> ```bash
> ssh <username>@<phone_ip> -p 8022
> ```

---

## Step 2: Core Packages Installation

Install the entire server stack in one command:

```bash
pkg install -y nodejs-lts mariadb php nginx cloudflared git tar curl
```

Verify installed versions:
```bash
node -v
mariadb --version
php -v
nginx -v
cloudflared --version
```

---

## Step 3: MariaDB (MySQL) Database Configuration

### 1. Initialize MariaDB data directory
```bash
mariadb-install-db
```

### 2. Start MariaDB server
```bash
mariadbd-safe --nowatch
```

### 3. Create Project Database & Tables
Log in to MySQL terminal:
```bash
mariadb -u root
```

Execute the following SQL commands:
```sql
CREATE DATABASE IF NOT EXISTS phonevps_db;
USE phonevps_db;

-- Table for system statistics & key-values
CREATE TABLE IF NOT EXISTS server_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(100) UNIQUE,
    key_value VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Table for guestbook & live CRUD demo
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial sample records
INSERT INTO server_stats (key_name, key_value) VALUES 
('device_type', 'Android Phone VPS'),
('engine', 'Node.js + MariaDB + Nginx + Cloudflare Tunnel'),
('status', 'Online & Operational')
ON DUPLICATE KEY UPDATE key_value=VALUES(key_value);

INSERT INTO messages (name, message) VALUES 
('Admin', 'Welcome to PhoneVPS! Running natively on Android Termux.');

EXIT;
```

---

## Step 4: Node.js API Server & Hardware Telemetry

### 1. Setup Project Directory & Dependencies
```bash
mkdir -p ~/phonevps/public ~/phonevps/logs ~/phonevps/storage
cd ~/phonevps

# Initialize package.json
cat << 'EOF' > package.json
{
  "name": "phonevps-server",
  "version": "1.0.0",
  "description": "PhoneVPS API & Web Server",
  "main": "server.js",
  "dependencies": {
    "cors": "^2.8.5",
    "express": "^4.19.2",
    "multer": "^1.4.5-lts.1",
    "mysql2": "^3.9.7"
  }
}
EOF

npm install
```

### 2. Build Server Backend (`server.js`)
Create `~/phonevps/server.js` with live CPU load calculations across all 8 cores, storage metrics from `df`, and MariaDB connection pool:

```javascript
const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');
const os = require('os');
const path = require('path');
const fs = require('fs');
const { execSync } = require('child_process');
const multer = require('multer');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const BASE_STORAGE_DIR = path.resolve(process.env.HOME || '/data/data/com.termux/files/home');

// Multer Storage Configuration
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        let reqPath = req.query.path || '';
        let targetDir = path.resolve(BASE_STORAGE_DIR, reqPath.replace(/^[\\/]+/, ''));
        if (!targetDir.startsWith(BASE_STORAGE_DIR)) targetDir = BASE_STORAGE_DIR;
        if (!fs.existsSync(targetDir)) fs.mkdirSync(targetDir, { recursive: true });
        cb(null, targetDir);
    },
    filename: function (req, file, cb) {
        cb(null, file.originalname);
    }
});
const upload = multer({ storage: storage, limits: { fileSize: 500 * 1024 * 1024 } });

// Database Connection Pool
const dbPool = mysql.createPool({
    host: '127.0.0.1',
    user: 'root',
    password: '',
    database: 'phonevps_db',
    waitForConnections: true,
    connectionLimit: 10
});

// Live CPU Load Sampler
let cpuPercent = 0;
let prevCpuTimes = getCpuTimes();

function getCpuTimes() {
    const cpus = os.cpus();
    let idle = 0, total = 0;
    if (!cpus || cpus.length === 0) return { idle: 100, total: 100 };
    cpus.forEach(cpu => {
        for (const type in cpu.times) total += cpu.times[type];
        idle += cpu.times.idle;
    });
    return { idle, total };
}

setInterval(() => {
    try {
        const current = getCpuTimes();
        const idleDiff = current.idle - prevCpuTimes.idle;
        const totalDiff = current.total - prevCpuTimes.total;
        if (totalDiff > 0) {
            cpuPercent = Math.max(0, Math.min(100, Math.round((1 - idleDiff / totalDiff) * 100)));
        }
        prevCpuTimes = current;
    } catch (e) {}
}, 1000);

function getAndroidInfo() {
    let model = 'moto g pure', brand = 'motorola', androidVer = '12', chip = 'MediaTek MT6765';
    let storageTotal = '23.0 GB', storageUsed = '10.0 GB', storageFree = '13.0 GB', storagePercent = 44;
    try {
        model = execSync('getprop ro.product.model 2>/dev/null').toString().trim() || model;
        brand = execSync('getprop ro.product.manufacturer 2>/dev/null').toString().trim() || brand;
        androidVer = execSync('getprop ro.build.version.release 2>/dev/null').toString().trim() || androidVer;
        chip = execSync('getprop ro.board.platform 2>/dev/null').toString().trim() || chip;
    } catch(e) {}

    try {
        const dfOut = execSync('df -k /data 2>/dev/null').toString().trim().split('\n');
        if (dfOut.length > 1) {
            const parts = dfOut[1].trim().split(/\s+/);
            if (parts.length >= 5) {
                const totalK = parseInt(parts[1], 10), usedK = parseInt(parts[2], 10), freeK = parseInt(parts[3], 10);
                storageTotal = (totalK / (1024 * 1024)).toFixed(1) + ' GB';
                storageUsed = (usedK / (1024 * 1024)).toFixed(1) + ' GB';
                storageFree = (freeK / (1024 * 1024)).toFixed(1) + ' GB';
                storagePercent = Math.round((usedK / totalK) * 100);
            }
        }
    } catch(e) {}

    return {
        device: `${brand.toUpperCase()} ${model}`,
        model, brand,
        android_version: `Android ${androidVer}`,
        chipset: chip,
        cpu_cores: os.cpus().length || 8,
        storage: { total: storageTotal, used: storageUsed, free: storageFree, percent: storagePercent }
    };
}

// System Status API
app.get('/api/status', async (req, res) => {
    let dbStatus = 'Disconnected', dbStatsCount = 0;
    try {
        const [rows] = await dbPool.query('SELECT COUNT(*) as count FROM server_stats');
        dbStatus = 'Connected (MariaDB)';
        dbStatsCount = rows[0].count;
    } catch (err) {
        dbStatus = 'Error: ' + err.message;
    }

    const totalMem = (os.totalmem() / (1024 * 1024)).toFixed(1);
    const freeMem = (os.freemem() / (1024 * 1024)).toFixed(1);
    const usedMem = (totalMem - freeMem).toFixed(1);

    res.json({
        success: true,
        server: {
            name: 'PhoneVPS Android Engine',
            phone: getAndroidInfo(),
            platform: os.platform(),
            arch: os.arch(),
            hostname: os.hostname(),
            uptime_formatted: formatUptime(os.uptime()),
            node_version: process.version,
            cpu_load: { cores: os.cpus().length, usage_percent: cpuPercent },
            memory: { total_mb: totalMem, free_mb: freeMem, used_mb: usedMem, usage_percent: Math.round((usedMem / totalMem) * 100) },
            database: { status: dbStatus, stats_rows: dbStatsCount }
        }
    });
});

// Messages API
app.get('/api/messages', async (req, res) => {
    try {
        const [rows] = await dbPool.query('SELECT * FROM messages ORDER BY id DESC LIMIT 50');
        res.json({ success: true, messages: rows });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/messages', async (req, res) => {
    const { name, message } = req.body;
    if (!name || !message) return res.status(400).json({ success: false, error: 'Name and message required' });
    try {
        const [result] = await dbPool.query('INSERT INTO messages (name, message) VALUES (?, ?)', [name.slice(0, 100), message.slice(0, 1000)]);
        res.json({ success: true, insertId: result.insertId });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// File Management APIs
app.get('/api/files/list', (req, res) => {
    try {
        const reqPath = (req.query.path || '').replace(/^[\\/]+/, '');
        const targetDir = path.resolve(BASE_STORAGE_DIR, reqPath);
        if (!targetDir.startsWith(BASE_STORAGE_DIR) || !fs.existsSync(targetDir)) {
            return res.status(404).json({ success: false, error: 'Directory not found' });
        }
        const entries = fs.readdirSync(targetDir, { withFileTypes: true });
        const items = entries.map(entry => {
            const fullPath = path.join(targetDir, entry.name);
            let size = 0, mtime = null, isDir = entry.isDirectory();
            try {
                const stat = fs.statSync(fullPath);
                size = stat.size; mtime = stat.mtime; isDir = stat.isDirectory();
            } catch(e) {}
            return {
                name: entry.name, is_dir: isDir, size,
                size_formatted: formatBytes(size), modified: mtime,
                relative_path: path.relative(BASE_STORAGE_DIR, fullPath).replace(/\\/g, '/')
            };
        });
        items.sort((a, b) => (a.is_dir === b.is_dir ? a.name.localeCompare(b.name) : a.is_dir ? -1 : 1));
        res.json({ success: true, current_path: reqPath.replace(/\\/g, '/'), items });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/files/upload', upload.array('files', 20), (req, res) => {
    res.json({ success: true, message: `${req.files ? req.files.length : 0} files uploaded` });
});

app.get('/api/files/download', (req, res) => {
    const reqPath = (req.query.path || '').replace(/^[\\/]+/, '');
    const targetFile = path.resolve(BASE_STORAGE_DIR, reqPath);
    if (!targetFile.startsWith(BASE_STORAGE_DIR) || !fs.existsSync(targetFile)) return res.status(404).send('Not found');
    res.download(targetFile);
});

app.post('/api/files/mkdir', (req, res) => {
    const { current_path, folder_name } = req.body;
    const newDir = path.resolve(BASE_STORAGE_DIR, (current_path || '').replace(/^[\\/]+/, ''), folder_name);
    if (!newDir.startsWith(BASE_STORAGE_DIR) || fs.existsSync(newDir)) return res.status(400).json({ success: false });
    fs.mkdirSync(newDir, { recursive: true });
    res.json({ success: true });
});

app.delete('/api/files/delete', (req, res) => {
    const target = path.resolve(BASE_STORAGE_DIR, (req.query.path || '').replace(/^[\\/]+/, ''));
    if (!target.startsWith(BASE_STORAGE_DIR) || target === BASE_STORAGE_DIR || !fs.existsSync(target)) return res.status(403).json({ success: false });
    fs.statSync(target).isDirectory() ? fs.rmSync(target, { recursive: true, force: true }) : fs.unlinkSync(target);
    res.json({ success: true });
});

app.get('/files*', (req, res) => res.sendFile(path.join(__dirname, 'public', 'files.html')));

function formatUptime(sec) {
    const d = Math.floor(sec / (3600*24)), h = Math.floor(sec % (3600*24) / 3600), m = Math.floor(sec % 3600 / 60), s = Math.floor(sec % 60);
    return `${d}d ${h}h ${m}m ${s}s`;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

app.listen(PORT, '0.0.0.0', () => console.log(`Server running on port ${PORT}`));
```

---

## Step 5: Web File Explorer & Storage Manager

Create `~/phonevps/public/files.html` to provide an interactive single-page file explorer UI for uploading, downloading, and browsing phone storage directly from any web browser. *(See `src/public/files.html` in the repository for full template code)*.

---

## Step 6: Official phpMyAdmin 5.2.1 Setup

### 1. Download & Extract phpMyAdmin
```bash
mkdir -p ~/phonevps/phpmyadmin ~/phonevps/pma_tmp
curl -sL https://files.phpmyadmin.net/phpMyAdmin/5.2.1/phpMyAdmin-5.2.1-all-languages.tar.gz -o ~/phonevps/pma.tar.gz
tar -xzf ~/phonevps/pma.tar.gz -C ~/phonevps/pma_tmp
cp -rf ~/phonevps/pma_tmp/phpMyAdmin-5.2.1-all-languages/* ~/phonevps/phpmyadmin/
rm -rf ~/phonevps/pma_tmp ~/phonevps/pma.tar.gz
mkdir -p ~/phonevps/phpmyadmin/tmp && chmod 777 ~/phonevps/phpmyadmin/tmp
```

### 2. Configure `config.inc.php`
Create `~/phonevps/phpmyadmin/config.inc.php`:
```php
<?php
declare(strict_types=1);

$_SERVER['HTTPS'] = 'on';
$_SERVER['SERVER_PORT'] = '443';

error_reporting(0);
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

/* Directories */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';
$cfg['TempDir'] = __DIR__ . '/tmp';

/* Absolute HTTPS URI */
$cfg['PmaAbsoluteUri'] = 'https://vps.shokherpolli.com/phpmyadmin/';
$cfg['SendErrorReports'] = 'never';
```

---

## Step 7: Nginx Reverse Proxy Configuration

Create or update `/data/data/com.termux/files/usr/etc/nginx/nginx.conf`:

```nginx
worker_processes 1;

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

        # Official phpMyAdmin Route
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
        }
    }
}
```

---

## Step 8: Cloudflare Zero Trust Tunnel & Custom Domain

1. Go to **[Cloudflare Zero Trust Dashboard](https://dash.cloudflare.com/)** ➔ **Networks** ➔ **Tunnels**.
2. Click **Create a Tunnel**, choose **Cloudflared**, name it `phone-vps`, and click **Save**.
3. Under **Install and Run**, copy your tunnel token (`eyJh...`).
4. In the **Published application (Public Hostname)** tab:
   - **Subdomain**: `vps` (or desired name)
   - **Domain**: `yourdomain.com`
   - **Type**: `HTTP`
   - **URL**: `http://127.0.0.1:8080`
5. On your domain registrar (e.g. Spaceship/Namecheap), set the nameservers to your assigned Cloudflare Nameservers (e.g. `dalary.ns.cloudflare.com`, `tate.ns.cloudflare.com`).

---

## Step 9: Automation Scripts & Quick Aliases

### 1. Master Startup Script (`start.sh`)
Create `~/phonevps/start.sh`:

```bash
#!/data/data/com.termux/files/usr/bin/bash

# 1. Start MariaDB (MySQL)
if ! pgrep -f "mariadbd" > /dev/null; then
    mariadbd-safe --nowatch > /dev/null 2>&1
    sleep 2
fi

# 2. Start Official phpMyAdmin
pkill -f "php -S 127.0.0.1:8081" 2>/dev/null
cd /data/data/com.termux/files/home/phonevps/phpmyadmin
nohup php -d error_reporting=0 -d display_errors=0 -d display_startup_errors=0 -S 127.0.0.1:8081 </dev/null >/data/data/com.termux/files/home/phonevps/logs/php.log 2>&1 &
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
nohup cloudflared tunnel run --token "YOUR_CLOUDFLARE_TUNNEL_TOKEN" </dev/null >/data/data/com.termux/files/home/phonevps/logs/cf.log 2>&1 &
disown

echo "All PhoneVPS services started successfully!"
```

### 2. Status Script (`status.sh`)
Create `~/phonevps/status.sh`:

```bash
#!/data/data/com.termux/files/usr/bin/bash
echo "=========================================="
echo "         PhoneVPS Live Status Check       "
echo "=========================================="
echo -n "MariaDB (MySQL)   : "
pgrep -f "mariadbd" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "PHP DB Manager    : "
pgrep -f "php -S" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Node.js Engine    : "
pgrep -f "node server.js" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Nginx Proxy       : "
pgrep -f "nginx" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Cloudflare Tunnel : "
pgrep -f "cloudflared" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo "------------------------------------------"
echo "Custom Domain     : https://vps.shokherpolli.com"
echo "phpMyAdmin URL    : https://vps.shokherpolli.com/phpmyadmin/"
echo "File Manager URL  : https://vps.shokherpolli.com/files"
echo "=========================================="
```

### 3. Stop Script (`stop.sh`)
Create `~/phonevps/stop.sh`:

```bash
#!/data/data/com.termux/files/usr/bin/bash
pkill -f "cloudflared"
pkill -f "nginx"
pkill -f "php -S"
pkill -f "node server.js"
mariadb-admin -u root shutdown 2>/dev/null || pkill -f mariadbd
echo "All PhoneVPS services stopped."
```

Make all scripts executable:
```bash
chmod +x ~/phonevps/*.sh
```

### 4. Setup Convenient Terminal Aliases
Add to `~/.bashrc`:
```bash
cat << 'EOF' >> ~/.bashrc

# --- PhoneVPS Aliases ---
alias vps-start='bash ~/phonevps/start.sh'
alias vps-status='bash ~/phonevps/status.sh'
alias vps-stop='bash ~/phonevps/stop.sh'
EOF
source ~/.bashrc
```

---

## Step 10: 24/7 Background Running & Battery Optimizations

To keep your phone running as an uninterrupted 24/7 server:

1. **Disable Battery Optimization for Termux:**
   - Go to Android **Settings** ➔ **Apps** ➔ **Termux** ➔ **App battery usage** ➔ Select **Unrestricted**.
2. **Lock Termux in Recent Apps:**
   - Open Recent Apps on your phone and tap the "Lock" icon on the Termux app card so Android's task killer does not close it.
3. **Acquire WakeLock in Termux:**
   - Run `termux-wake-lock` (adds persistent foreground notification).
4. **Auto-Start on Phone Reboot (Termux:Boot):**
   - Install `Termux:Boot` from F-Droid.
   - Create `~/.termux/boot/start-vps.sh`:
     ```bash
     mkdir -p ~/.termux/boot
     cat << 'EOF' > ~/.termux/boot/start-vps.sh
     #!/data/data/com.termux/files/usr/bin/bash
     termux-wake-lock
     bash /data/data/com.termux/files/home/phonevps/start.sh
     EOF
     chmod +x ~/.termux/boot/start-vps.sh
     ```

---

## Troubleshooting & Maintenance

| Issue | Solution |
|---|---|
| **DNS not resolving immediately** | Nameserver / CNAME changes take 5-10 minutes to propagate worldwide. Clear DNS cache (`ipconfig /flushdns`) or test with 1.1.1.1. |
| **Error 1033 on Cloudflare** | The `cloudflared` process was restarted or connecting. Check `vps-status` and wait 5 seconds. |
| **MariaDB connection refused** | Run `mariadbd-safe --nowatch` and check `/data/data/com.termux/files/usr/var/lib/mysql/localhost.err`. |
| **phpMyAdmin password prompt** | Default username is `root` with blank (empty) password. |

---

*Enjoy your fully functional, zero-cost, high-performance Android Phone VPS!*
