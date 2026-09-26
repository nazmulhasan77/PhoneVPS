import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=15)
sftp = client.open_sftp()

def run(cmd):
    print(f"--> {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print("[OUT]:\n" + out.strip())
    if err:
        print("[ERR]:\n" + err.strip())
    return out, err

server_js = """const express = require('express');
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

// Multer setup
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        let reqPath = req.query.path || '';
        let targetDir = path.resolve(BASE_STORAGE_DIR, reqPath.replace(/^[\\\\/]+/, ''));
        if (!targetDir.startsWith(BASE_STORAGE_DIR)) {
            targetDir = BASE_STORAGE_DIR;
        }
        if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
        }
        cb(null, targetDir);
    },
    filename: function (req, file, cb) {
        cb(null, file.originalname);
    }
});
const upload = multer({ storage: storage, limits: { fileSize: 500 * 1024 * 1024 } });

// Database Pool
const dbPool = mysql.createPool({
    host: '127.0.0.1',
    user: 'root',
    password: '',
    database: 'phonevps_db',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// Live CPU Load Sampler
let cpuPercent = 0;
let prevCpuTimes = getCpuTimes();

function getCpuTimes() {
    const cpus = os.cpus();
    let idle = 0;
    let total = 0;
    if (!cpus || cpus.length === 0) {
        return { idle: 100, total: 100 };
    }
    cpus.forEach(cpu => {
        for (const type in cpu.times) {
            total += cpu.times[type];
        }
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
            cpuPercent = Math.max(1, Math.min(100, Math.round((1 - idleDiff / totalDiff) * 100)));
        }
        prevCpuTimes = current;
    } catch (e) {}
}, 1000);

function getAndroidInfo() {
    let model = 'moto g pure';
    let brand = 'motorola';
    let androidVer = '12';
    let chip = 'MediaTek MT6765 (Helio)';
    let storageTotal = '23.0 GB';
    let storageUsed = '10.0 GB';
    let storageFree = '13.0 GB';
    let storagePercent = 44;
    
    try {
        model = execSync('getprop ro.product.model 2>/dev/null').toString().trim() || model;
        brand = execSync('getprop ro.product.manufacturer 2>/dev/null').toString().trim() || brand;
        androidVer = execSync('getprop ro.build.version.release 2>/dev/null').toString().trim() || androidVer;
        chip = execSync('getprop ro.board.platform 2>/dev/null').toString().trim() || chip;
    } catch(e) {}

    try {
        const dfOut = execSync('df -k /data 2>/dev/null').toString().trim().split('\\n');
        if (dfOut.length > 1) {
            const parts = dfOut[1].trim().split(/\\s+/);
            if (parts.length >= 5) {
                const totalK = parseInt(parts[1], 10);
                const usedK = parseInt(parts[2], 10);
                const freeK = parseInt(parts[3], 10);
                storageTotal = (totalK / (1024 * 1024)).toFixed(1) + ' GB';
                storageUsed = (usedK / (1024 * 1024)).toFixed(1) + ' GB';
                storageFree = (freeK / (1024 * 1024)).toFixed(1) + ' GB';
                storagePercent = Math.round((usedK / totalK) * 100);
            }
        }
    } catch(e) {}

    return {
        device: `${brand.toUpperCase()} ${model}`,
        model: model,
        brand: brand,
        android_version: `Android ${androidVer}`,
        chipset: chip,
        cpu_cores: os.cpus().length || 8,
        storage: {
            total: storageTotal,
            used: storageUsed,
            free: storageFree,
            percent: storagePercent
        }
    };
}

// Status API
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
    const phoneHardware = getAndroidInfo();

    res.json({
        success: true,
        server: {
            name: 'PhoneVPS Android Engine',
            phone: phoneHardware,
            platform: os.platform(),
            arch: os.arch(),
            hostname: os.hostname(),
            uptime_seconds: Math.floor(os.uptime()),
            uptime_formatted: formatUptime(os.uptime()),
            node_version: process.version,
            cpu_load: {
                cores: phoneHardware.cpu_cores,
                usage_percent: cpuPercent
            },
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

// File Manager APIs
app.get('/api/files/list', (req, res) => {
    try {
        const reqPath = (req.query.path || '').replace(/^[\\\\/]+/, '');
        const targetDir = path.resolve(BASE_STORAGE_DIR, reqPath);
        if (!targetDir.startsWith(BASE_STORAGE_DIR) || !fs.existsSync(targetDir)) {
            return res.status(404).json({ success: false, error: 'Directory not found.' });
        }
        const entries = fs.readdirSync(targetDir, { withFileTypes: true });
        const items = entries.map(entry => {
            const fullPath = path.join(targetDir, entry.name);
            let size = 0;
            let mtime = null;
            let isDir = entry.isDirectory();
            try {
                const stat = fs.statSync(fullPath);
                size = stat.size;
                mtime = stat.mtime;
                isDir = stat.isDirectory();
            } catch(e) {}
            return {
                name: entry.name,
                is_dir: isDir,
                size: size,
                size_formatted: formatBytes(size),
                modified: mtime,
                relative_path: path.relative(BASE_STORAGE_DIR, fullPath).replace(/\\\\/g, '/')
            };
        });
        items.sort((a, b) => (a.is_dir === b.is_dir ? a.name.localeCompare(b.name) : a.is_dir ? -1 : 1));
        res.json({ success: true, current_path: reqPath.replace(/\\\\/g, '/'), items });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.post('/api/files/upload', upload.array('files', 20), (req, res) => {
    try {
        const filesCount = req.files ? req.files.length : 0;
        res.json({ success: true, message: `${filesCount} file(s) uploaded successfully!` });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.get('/api/files/download', (req, res) => {
    try {
        const reqPath = (req.query.path || '').replace(/^[\\\\/]+/, '');
        const targetFile = path.resolve(BASE_STORAGE_DIR, reqPath);
        if (!targetFile.startsWith(BASE_STORAGE_DIR) || !fs.existsSync(targetFile)) {
            return res.status(404).send('File not found');
        }
        res.download(targetFile);
    } catch (err) {
        res.status(500).send('Download error: ' + err.message);
    }
});

app.post('/api/files/mkdir', (req, res) => {
    try {
        const { current_path, folder_name } = req.body;
        if (!folder_name || /[\\\\/:*?"<>|]/.test(folder_name)) {
            return res.status(400).json({ success: false, error: 'Invalid folder name' });
        }
        const cleanPath = (current_path || '').replace(/^[\\\\/]+/, '');
        const newDirPath = path.resolve(BASE_STORAGE_DIR, cleanPath, folder_name);
        if (!newDirPath.startsWith(BASE_STORAGE_DIR)) {
            return res.status(403).json({ success: false, error: 'Permission denied' });
        }
        fs.mkdirSync(newDirPath, { recursive: true });
        res.json({ success: true, message: 'Folder created successfully' });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.delete('/api/files/delete', (req, res) => {
    try {
        const reqPath = (req.query.path || '').replace(/^[\\\\/]+/, '');
        const targetPath = path.resolve(BASE_STORAGE_DIR, reqPath);
        if (!targetPath.startsWith(BASE_STORAGE_DIR) || targetPath === BASE_STORAGE_DIR) {
            return res.status(403).json({ success: false, error: 'Cannot delete root directory.' });
        }
        const stat = fs.statSync(targetPath);
        if (stat.isDirectory()) {
            fs.rmSync(targetPath, { recursive: true, force: true });
        } else {
            fs.unlinkSync(targetPath);
        }
        res.json({ success: true, message: 'Deleted successfully' });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.get('/files', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'files.html'));
});

function formatUptime(sec) {
    const d = Math.floor(sec / (3600*24));
    const h = Math.floor(sec % (3600*24) / 3600);
    const m = Math.floor(sec % 3600 / 60);
    const s = Math.floor(sec % 60);
    return `${d}d ${h}h ${m}m ${s}s`;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

app.listen(PORT, '0.0.0.0', () => {
    console.log(`PhoneVPS Server running on port ${PORT}`);
});
"""

# Update index.html with live CPU load meter
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhoneVPS - Android Smartphone VPS Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0a0e17;
            --bg-card: rgba(18, 26, 42, 0.85);
            --border-color: rgba(99, 102, 241, 0.25);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --accent: #06b6d4;
            --accent-glow: rgba(6, 182, 212, 0.4);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.3);
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 24px 16px;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.18) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.18) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(15, 23, 42, 0.6) 0px, transparent 100%);
            background-attachment: fixed;
        }

        .container {
            max-width: 1100px;
            width: 100%;
        }

        header {
            text-align: center;
            margin-bottom: 28px;
            position: relative;
        }

        .badge-live {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(16, 185, 129, 0.12);
            border: 1px solid rgba(16, 185, 129, 0.3);
            color: #34d399;
            padding: 6px 16px;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 14px;
            box-shadow: 0 0 20px var(--success-glow);
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

        .top-action-bar {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-top: 14px;
            margin-bottom: 8px;
        }

        .btn-files {
            background: linear-gradient(135deg, #3b82f6, #06b6d4);
            color: #fff;
            padding: 10px 22px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.95rem;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 20px rgba(6, 182, 212, 0.3);
            transition: transform 0.15s, box-shadow 0.2s;
        }
        .btn-files:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(6, 182, 212, 0.5);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }

        .card {
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
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

        .icon { font-size: 1.3rem; }

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
            font-size: 1.2rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #38bdf8;
        }

        .progress-bar-bg {
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            margin-top: 6px;
            overflow: hidden;
        }

        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #06b6d4);
            border-radius: 999px;
            transition: width 0.4s ease;
        }

        .meter-block {
            margin-top: 14px;
        }

        .meter-label {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-dim);
        }

        .form-group { margin-bottom: 12px; }

        input, textarea {
            width: 100%;
            padding: 12px 14px;
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
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            font-size: 0.95rem;
            transition: transform 0.1s, opacity 0.2s;
        }

        .message-feed {
            max-height: 240px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 16px;
            padding-right: 4px;
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
                PHONE VPS ONLINE &bull; vps.shokherpolli.com
            </div>
            <h1>Android Smartphone VPS</h1>
            <p class="subtitle">Complete Linux server running natively on Android with Node.js, MariaDB, Nginx &amp; Cloudflare Tunnel.</p>
            <div class="top-action-bar">
                <a href="/files" class="btn-files">
                    <span>📁 Open File Manager &amp; Storage</span>
                </a>
            </div>
        </header>

        <!-- Phone Hardware Specs & Telemetry Grid -->
        <div class="grid">
            <!-- Hardware Spec Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">📱</span> Smartphone Hardware</div>
                    <span id="devBrandBadge" class="stack-status" style="color: #a5b4fc; background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.3);">Motorola</span>
                </div>
                <div class="stat-group">
                    <div class="stat-box">
                        <div class="stat-label">Model</div>
                        <div class="stat-value" id="valDevModel">moto g pure</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">OS Version</div>
                        <div class="stat-value" id="valDevOS">Android 12</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">CPU Cores</div>
                        <div class="stat-value" id="valDevCores">8 Cores</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Architecture</div>
                        <div class="stat-value" id="valArch">ARMv7 (32-bit)</div>
                    </div>
                </div>

                <div class="meter-block">
                    <div class="meter-label">
                        <span>Internal Storage (<span id="valStorageText">-- / --</span>)</span>
                        <span id="valStoragePercent">0%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div id="storageFill" class="progress-bar-fill" style="width: 0%; background: linear-gradient(90deg, #10b981, #06b6d4);"></div>
                    </div>
                </div>
            </div>

            <!-- Live Telemetry Card -->
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">⚡</span> Live System Telemetry</div>
                    <span id="uptimeBadge" class="stack-status">Loading...</span>
                </div>
                <div class="stat-group">
                    <div class="stat-box">
                        <div class="stat-label">CPU Utilization</div>
                        <div class="stat-value" id="valCpuLoad" style="color: #f59e0b;">-- %</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">RAM Usage</div>
                        <div class="stat-value" id="valRam">-- MB</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">MariaDB</div>
                        <div class="stat-value" id="valDb" style="color: #34d399;">Active</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label">Node Engine</div>
                        <div class="stat-value" id="valNode">--</div>
                    </div>
                </div>

                <!-- CPU Load Meter -->
                <div class="meter-block">
                    <div class="meter-label">
                        <span>CPU Load (8 Cores)</span>
                        <span id="cpuPercentLabel">0%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div id="cpuFill" class="progress-bar-fill" style="width: 0%; background: linear-gradient(90deg, #f59e0b, #ef4444);"></div>
                    </div>
                </div>

                <!-- RAM Meter -->
                <div class="meter-block">
                    <div class="meter-label">
                        <span>RAM Utilization</span>
                        <span id="ramPercent">0%</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div id="ramFill" class="progress-bar-fill" style="width: 0%;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Infrastructure & Guestbook Grid -->
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">🚀</span> Server Infrastructure</div>
                </div>
                <div class="stack-list">
                    <div class="stack-item">
                        <div class="stack-name">🌐 Nginx Proxy</div>
                        <div class="stack-status">Port 8080</div>
                    </div>
                    <div class="stack-item">
                        <div class="stack-name">🟢 Node.js API</div>
                        <div class="stack-status">Port 3000</div>
                    </div>
                    <div class="stack-item">
                        <div class="stack-name">🗄️ MariaDB / MySQL</div>
                        <div class="stack-status">Port 3306</div>
                    </div>
                    <div class="stack-item">
                        <div class="stack-name">📁 Web File Explorer</div>
                        <div class="stack-status" style="color: #38bdf8; background: rgba(56,189,248,0.1); border-color: rgba(56,189,248,0.3);"><a href="/files" style="color: inherit; text-decoration: none;">/files</a></div>
                    </div>
                    <div class="stack-item">
                        <div class="stack-name">☁️ Cloudflare Tunnel</div>
                        <div class="stack-status" style="color: #f59e0b; background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.3);">Custom Domain SSL</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">💬</span> MySQL Live Guestbook</div>
                </div>
                <form id="msgForm" onsubmit="postMessage(event)">
                    <div class="form-group">
                        <input type="text" id="authorInput" placeholder="Your Name or Handle" required>
                    </div>
                    <div class="form-group">
                        <textarea id="messageInput" rows="2" placeholder="Write a note to MariaDB..." required></textarea>
                    </div>
                    <button type="submit" class="btn" id="submitBtn">Save to MySQL</button>
                </form>

                <div class="message-feed" id="messageList">
                    <div style="color: var(--text-dim); font-size: 0.85rem;">Loading messages...</div>
                </div>
            </div>
        </div>

        <footer>
            <p>PhoneVPS &bull; Motorola moto g pure &bull; <a href="/files" style="color: #38bdf8; text-decoration: none;">Access File Manager (/files)</a></p>
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

                    if (s.cpu_load) {
                        const cpu = s.cpu_load.usage_percent;
                        document.getElementById('valCpuLoad').innerText = `${cpu}%`;
                        document.getElementById('cpuPercentLabel').innerText = `${cpu}%`;
                        document.getElementById('cpuFill').style.width = `${cpu}%`;
                    }

                    if (s.phone) {
                        document.getElementById('valDevModel').innerText = s.phone.model;
                        document.getElementById('devBrandBadge').innerText = s.phone.brand.toUpperCase();
                        document.getElementById('valDevOS').innerText = s.phone.android_version;
                        document.getElementById('valDevCores').innerText = `${s.phone.cpu_cores} Cores`;
                        if (s.phone.storage) {
                            document.getElementById('valStorageText').innerText = `${s.phone.storage.used} / ${s.phone.storage.total}`;
                            document.getElementById('valStoragePercent').innerText = `${s.phone.storage.percent}% Used`;
                            document.getElementById('storageFill').style.width = `${s.phone.storage.percent}%`;
                        }
                    }
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
                    list.innerHTML = '<div style="color: var(--text-dim); font-size: 0.85rem;">No messages yet.</div>';
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
            btn.innerText = 'Saving...';

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
                btn.innerText = 'Save to MySQL';
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.innerText = text || '';
            return div.innerHTML;
        }

        fetchTelemetry();
        fetchMessages();
        setInterval(fetchTelemetry, 2000);
        setInterval(fetchMessages, 5000);
    </script>
</body>
</html>
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/server.js', 'w') as f:
    f.write(server_js)

with sftp.file('/data/data/com.termux/files/home/phonevps/public/index.html', 'w') as f:
    f.write(index_html)

run("pkill -f 'node server.js'")
run("cd ~/phonevps && nohup node server.js > ~/phonevps/logs/node.log 2>&1 &")

time.sleep(2)
run("bash ~/phonevps/status.sh")

client.close()
