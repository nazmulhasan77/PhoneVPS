import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

def setup_phone():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
    sftp = client.open_sftp()

    def run(cmd):
        print(f"\n[EXEC]: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        if out:
            print("[STDOUT]:\n" + out.strip())
        if err:
            print("[STDERR]:\n" + err.strip())
        return out, err

    # 1. Create project dir
    run("mkdir -p ~/phonevps/public ~/phonevps/logs")

    # 2. Setup MySQL database and table
    sql_init = """
CREATE DATABASE IF NOT EXISTS phonevps_db;
USE phonevps_db;
CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS server_stats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    key_name VARCHAR(100) UNIQUE,
    key_value VARCHAR(255),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
INSERT INTO server_stats (key_name, key_value) VALUES 
('device_type', 'Android Phone VPS'),
('engine', 'Node.js + MariaDB + Nginx + Cloudflare Tunnel'),
('status', 'Online & Operational')
ON DUPLICATE KEY UPDATE key_value=VALUES(key_value);

INSERT INTO messages (name, message) 
SELECT 'Admin', 'Welcome to PhoneVPS! Running on Android Termux.' 
WHERE NOT EXISTS (SELECT 1 FROM messages WHERE id=1);
"""
    with sftp.file('/data/data/com.termux/files/home/phonevps/init_db.sql', 'w') as f:
        f.write(sql_init)
    
    run("mariadb -u root < ~/phonevps/init_db.sql")

    # 3. Create package.json and install express & mysql2
    pkg_json = """{
  "name": "phonevps-server",
  "version": "1.0.0",
  "description": "PhoneVPS API & Web Server",
  "main": "server.js",
  "dependencies": {
    "cors": "^2.8.5",
    "express": "^4.19.2",
    "mysql2": "^3.9.7"
  }
}"""
    with sftp.file('/data/data/com.termux/files/home/phonevps/package.json', 'w') as f:
        f.write(pkg_json)

    print("Installing npm dependencies (express, cors, mysql2)...")
    run("cd ~/phonevps && npm install")

    # 4. Create Node.js server.js
    server_js = """const express = require('express');
const mysql = require('mysql2/promise');
const cors = require('cors');
const os = require('os');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const dbPool = mysql.createPool({
    host: '127.0.0.1',
    user: 'root',
    password: '',
    database: 'phonevps_db',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// System Status API
app.get('/api/status', async (req, res) => {
    let dbStatus = 'Disconnected';
    let dbStatsCount = 0;
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
            name: 'PhoneVPS Android Node Engine',
            platform: os.platform(),
            arch: os.arch(),
            hostname: os.hostname(),
            uptime_seconds: Math.floor(os.uptime()),
            uptime_formatted: formatUptime(os.uptime()),
            node_version: process.version,
            cpus: os.cpus().length,
            memory: {
                total_mb: totalMem,
                free_mb: freeMem,
                used_mb: usedMem,
                usage_percent: Math.round((usedMem / totalMem) * 100)
            },
            database: {
                status: dbStatus,
                stats_rows: dbStatsCount
            },
            timestamp: new Date().toISOString()
        }
    });
});

// Messages (Guestbook / CRUD Demo) API
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
    if (!name || !message) {
        return res.status(400).json({ success: false, error: 'Name and message are required' });
    }
    try {
        const [result] = await dbPool.query('INSERT INTO messages (name, message) VALUES (?, ?)', [name.slice(0, 100), message.slice(0, 1000)]);
        res.json({ success: true, insertId: result.insertId, message: 'Message saved to MySQL!' });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

// Database info API
app.get('/api/db-info', async (req, res) => {
    try {
        const [stats] = await dbPool.query('SELECT * FROM server_stats');
        const [countResult] = await dbPool.query('SELECT COUNT(*) as total_msgs FROM messages');
        res.json({ success: true, stats, total_messages: countResult[0].total_msgs });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

function formatUptime(sec) {
    const d = Math.floor(sec / (3600*24));
    const h = Math.floor(sec % (3600*24) / 3600);
    const m = Math.floor(sec % 3600 / 60);
    const s = Math.floor(sec % 60);
    return `${d}d ${h}h ${m}m ${s}s`;
}

app.listen(PORT, '0.0.0.0', () => {
    console.log(`PhoneVPS Node API Server running on port ${PORT}`);
});
"""
    with sftp.file('/data/data/com.termux/files/home/phonevps/server.js', 'w') as f:
        f.write(server_js)

    # 5. Create Beautiful Dashboard Frontend
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhoneVPS - Android VPS Server</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0a0e17;
            --bg-card: rgba(18, 26, 42, 0.75);
            --bg-card-hover: rgba(28, 40, 65, 0.85);
            --border-color: rgba(99, 102, 241, 0.2);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --accent: #06b6d4;
            --accent-glow: rgba(6, 182, 212, 0.4);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.3);
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px 16px;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.15) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(15, 23, 42, 0.5) 0px, transparent 100%);
            background-attachment: fixed;
        }

        .container {
            max-width: 1100px;
            width: 100%;
        }

        /* Header */
        header {
            text-align: center;
            margin-bottom: 36px;
            position: relative;
        }

        .badge-live {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #34d399;
            padding: 6px 14px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 14px;
            box-shadow: 0 0 15px var(--success-glow);
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }

        .subtitle {
            color: var(--text-dim);
            font-size: 1.05rem;
            max-width: 650px;
            margin: 0 auto;
        }

        /* Grid */
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        /* Cards */
        .card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
            transition: all 0.3s ease;
        }

        .card:hover {
            border-color: var(--primary);
            box-shadow: 0 12px 40px var(--primary-glow);
        }

        .card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
        }

        .card-title {
            font-size: 1.15rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #fff;
        }

        .icon {
            font-size: 1.3rem;
        }

        /* Stack items */
        .stack-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .stack-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stack-name {
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .stack-status {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            padding: 4px 10px;
            border-radius: 6px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        /* Stats */
        .stat-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }

        .stat-box {
            background: rgba(15, 23, 42, 0.6);
            padding: 14px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .stat-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-dim);
            margin-bottom: 4px;
        }

        .stat-value {
            font-size: 1.25rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #38bdf8;
        }

        /* Progress Bar */
        .progress-bar-bg {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            margin-top: 10px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #06b6d4);
            border-radius: 999px;
            transition: width 0.5s ease;
        }

        /* Form */
        .form-group {
            margin-bottom: 12px;
        }

        input, textarea {
            width: 100%;
            padding: 10px 14px;
            border-radius: 10px;
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid var(--border-color);
            color: #fff;
            font-family: inherit;
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }

        input:focus, textarea:focus {
            border-color: var(--accent);
            box-shadow: 0 0 10px var(--accent-glow);
        }

        button.btn {
            background: linear-gradient(135deg, var(--primary), var(--accent));
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            font-size: 0.95rem;
            transition: transform 0.1s, opacity 0.2s;
        }

        button.btn:active {
            transform: scale(0.98);
        }

        /* Messages list */
        .message-feed {
            max-height: 220px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 16px;
            padding-right: 4px;
        }

        .message-feed::-webkit-scrollbar {
            width: 4px;
        }
        .message-feed::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 4px;
        }

        .msg-bubble {
            background: rgba(15, 23, 42, 0.7);
            border-left: 3px solid var(--accent);
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
        }

        .msg-author {
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 2px;
            display: flex;
            justify-content: space-between;
        }

        .msg-time {
            font-size: 0.7rem;
            color: var(--text-dim);
            font-weight: normal;
        }

        footer {
            margin-top: 30px;
            text-align: center;
            color: var(--text-dim);
            font-size: 0.85rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="badge-live">
                <div class="pulse-dot"></div>
                PHONE VPS ONLINE & SYNCED
            </div>
            <h1>Android Smartphone VPS</h1>
            <p class="subtitle">Full-stack server environment powered by Node.js, MariaDB, Nginx, and Cloudflare Tunnel running natively on Android Termux.</p>
        </header>

        <div class="grid">
            <!-- System Stats Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">⚡</span> System Telemetry</div>
                    <span id="uptimeBadge" class="stack-status">Loading...</span>
                </div>
                <div class="stat-group">
                    <div class="stat-box">
                        <div class="stat-label">Architecture</div>
                        <div class="stat-value" id="valArch">armv7l</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">RAM Usage</div>
                        <div class="stat-value" id="valRam">-- MB</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Node Engine</div>
                        <div class="stat-value" id="valNode">--</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">DB Status</div>
                        <div class="stat-value" id="valDb" style="color: #34d399;">Active</div>
                    </div>
                </div>
                <div style="margin-top: 16px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--text-dim);">
                        <span>Memory Utilization</span>
                        <span id="ramPercent">0%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div id="ramFill" class="progress-bar-fill" style="width: 0%;"></div>
                    </div>
                </div>
            </div>

            <!-- Server Stack Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">🚀</span> Server Infrastructure</div>
                </div>
                <div class="stack-list">
                    <div class="stack-item">
                        <div class="stack-name">🌐 Nginx Reverse Proxy</div>
                        <div class="stack-status">Port 8080</div>
                    </div>
                    <div class="stack-item">
                        <div class="stack-name">🟢 Node.js API Service</div>
                        <div class="stack-status">Port 3000</div>
                    </div>
                    <div class="stack-item">
                        <div class="stack-name">🗄️ MariaDB / MySQL</div>
                        <div class="stack-status">Port 3306</div>
                    </div>
                    <div class="stack-item">
                        <div class="stack-name">☁️ Cloudflare Tunnel</div>
                        <div class="stack-status" style="color: #f59e0b; border-color: rgba(245,158,11,0.3); background: rgba(245,158,11,0.1);">Global HTTPS</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- MariaDB Guestbook & API Test Section -->
        <div class="grid" style="grid-template-columns: 1fr;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">💬</span> Live Database Guestbook (MariaDB + API Test)</div>
                </div>
                <p style="color: var(--text-dim); font-size: 0.9rem; margin-bottom: 16px;">
                    Write a message below to test real-time write and read operations on your phone's native MariaDB database over the Cloudflare Tunnel!
                </p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                    <form id="msgForm" onsubmit="postMessage(event)">
                        <div class="form-group">
                            <input type="text" id="authorInput" placeholder="Your Name or Handle" required>
                        </div>
                        <div class="form-group">
                            <textarea id="messageInput" rows="3" placeholder="Write a note (e.g. 'Hello from internet!')..." required></textarea>
                        </div>
                        <button type="submit" class="btn" id="submitBtn">Send to MySQL Database</button>
                    </form>

                    <div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-dim); margin-bottom: 8px;">RECENT MESSAGES FROM MARIADB</div>
                        <div class="message-feed" id="messageList">
                            <div style="color: var(--text-dim); font-size: 0.85rem;">Loading messages...</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <footer>
            <p>PhoneVPS &bull; Hosted on Android Device &bull; Accessible Worldwide via Cloudflare Tunnel</p>
        </footer>
    </div>

    <script>
        async function fetchTelemetry() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();
                if (data.success) {
                    const s = data.server;
                    document.getElementById('uptimeBadge').innerText = 'UP: ' + s.uptime_formatted;
                    document.getElementById('valArch').innerText = s.arch;
                    document.getElementById('valRam').innerText = `${s.memory.used_mb} / ${s.memory.total_mb} MB`;
                    document.getElementById('valNode').innerText = s.node_version;
                    document.getElementById('ramPercent').innerText = `${s.memory.usage_percent}%`;
                    document.getElementById('ramFill').style.width = `${s.memory.usage_percent}%`;
                    document.getElementById('valDb').innerText = s.database.status.startsWith('Connected') ? 'Online' : 'Error';
                }
            } catch (e) {
                console.error("Status fetch error", e);
            }
        }

        async function fetchMessages() {
            try {
                const res = await fetch('/api/messages');
                const data = await res.json();
                const list = document.getElementById('messageList');
                if (data.success && data.messages.length > 0) {
                    list.innerHTML = data.messages.map(m => `
                        <div class="msg-bubble">
                            <div class="msg-author">
                                <span>${escapeHtml(m.name)}</span>
                                <span class="msg-time">${new Date(m.created_at).toLocaleTimeString()}</span>
                            </div>
                            <div>${escapeHtml(m.message)}</div>
                        </div>
                    `).join('');
                } else {
                    list.innerHTML = '<div style="color: var(--text-dim); font-size: 0.85rem;">No messages yet. Be the first to write!</div>';
                }
            } catch (e) {
                console.error("Messages fetch error", e);
            }
        }

        async function postMessage(e) {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const name = document.getElementById('authorInput').value.trim();
            const message = document.getElementById('messageInput').value.trim();
            if (!name || !message) return;

            btn.disabled = true;
            btn.innerText = 'Saving to Database...';

            try {
                const res = await fetch('/api/messages', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, message })
                });
                const result = await res.json();
                if (result.success) {
                    document.getElementById('messageInput').value = '';
                    await fetchMessages();
                } else {
                    alert('Error: ' + result.error);
                }
            } catch (err) {
                alert('Network error: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.innerText = 'Send to MySQL Database';
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.innerText = text || '';
            return div.innerHTML;
        }

        fetchTelemetry();
        fetchMessages();
        setInterval(fetchTelemetry, 3000);
        setInterval(fetchMessages, 5000);
    </script>
</body>
</html>
"""
    with sftp.file('/data/data/com.termux/files/home/phonevps/public/index.html', 'w') as f:
        f.write(html_content)

    # 6. Create Nginx Configuration
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

        location / {
            proxy_pass http://127.0.0.1:3000;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
"""
    with sftp.file('/data/data/com.termux/files/usr/etc/nginx/nginx.conf', 'w') as f:
        f.write(nginx_conf)

    # 7. Create start, stop, and status bash scripts
    start_sh = """#!/data/data/com.termux/files/usr/bin/bash

echo "=== [PhoneVPS] Starting All Services ==="

# 1. Start MariaDB
if ! pgrep -x "mariadbd" > /dev/null; then
    echo "Starting MariaDB..."
    mariadbd-safe --nowatch > /dev/null 2>&1
    sleep 3
else
    echo "MariaDB is already running."
fi

# 2. Start Node.js API server
pkill -f "node server.js" 2>/dev/null
echo "Starting Node.js server..."
cd /data/data/com.termux/files/home/phonevps
nohup node server.js > ~/phonevps/logs/node.log 2>&1 &
sleep 2

# 3. Start Nginx
pkill nginx 2>/dev/null
echo "Starting Nginx..."
nginx
sleep 1

# 4. Start Cloudflare Tunnel
pkill -f "cloudflared" 2>/dev/null
echo "Starting Cloudflare Tunnel..."
nohup cloudflared tunnel --url http://127.0.0.1:8080 --logfile ~/phonevps/logs/cloudflared.log > ~/phonevps/logs/cloudflared.out 2>&1 &

echo "Waiting for Cloudflare Tunnel URL..."
sleep 6

CF_URL=$(grep -o 'https://[-a-zA-Z0-9@:%._\+~#=]\+\.trycloudflare\.com' ~/phonevps/logs/cloudflared.log | tail -n 1)

echo "=================================================="
echo "PhoneVPS is UP and RUNNING!"
echo "Local Nginx URL: http://127.0.0.1:8080"
echo "Public Cloudflare Tunnel URL: $CF_URL"
echo "=================================================="
"""
    with sftp.file('/data/data/com.termux/files/home/phonevps/start.sh', 'w') as f:
        f.write(start_sh)

    stop_sh = """#!/data/data/com.termux/files/usr/bin/bash
echo "=== Stopping PhoneVPS Services ==="
pkill -f "cloudflared"
pkill nginx
pkill -f "node server.js"
mariadb-admin -u root shutdown 2>/dev/null || pkill mariadbd
echo "All services stopped."
"""
    with sftp.file('/data/data/com.termux/files/home/phonevps/stop.sh', 'w') as f:
        f.write(stop_sh)

    status_sh = """#!/data/data/com.termux/files/usr/bin/bash
echo "=== PhoneVPS Status ==="
echo -n "MariaDB: "
pgrep -x "mariadbd" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Node.js: "
pgrep -f "node server.js" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Nginx: "
pgrep -x "nginx" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Cloudflare Tunnel: "
pgrep -f "cloudflared" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"

CF_URL=$(grep -o 'https://[-a-zA-Z0-9@:%._\+~#=]\+\.trycloudflare\.com' ~/phonevps/logs/cloudflared.log | tail -n 1)
echo "Public URL: $CF_URL"
"""
    with sftp.file('/data/data/com.termux/files/home/phonevps/status.sh', 'w') as f:
        f.write(status_sh)

    run("chmod +x ~/phonevps/*.sh")
    
    print("\n--- Starting all services via start.sh ---")
    run("bash ~/phonevps/start.sh")

    client.close()

if __name__ == "__main__":
    setup_phone()
