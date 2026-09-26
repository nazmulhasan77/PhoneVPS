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

// Multer setup
const storage = multer.diskStorage({
    destination: function (req, file, cb) {
        let reqPath = req.query.path || '';
        let targetDir = path.resolve(BASE_STORAGE_DIR, reqPath.replace(/^[\\/]+/, ''));
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
        const dfOut = execSync('df -k /data 2>/dev/null').toString().trim().split('\n');
        if (dfOut.length > 1) {
            const parts = dfOut[1].trim().split(/\s+/);
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
        const reqPath = (req.query.path || '').replace(/^[\\/]+/, '');
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
    try {
        const filesCount = req.files ? req.files.length : 0;
        res.json({ success: true, message: `${filesCount} file(s) uploaded successfully!` });
    } catch (err) {
        res.status(500).json({ success: false, error: err.message });
    }
});

app.get('/api/files/download', (req, res) => {
    try {
        const reqPath = (req.query.path || '').replace(/^[\\/]+/, '');
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
        if (!folder_name || /[\\/:*?"<>|]/.test(folder_name)) {
            return res.status(400).json({ success: false, error: 'Invalid folder name' });
        }
        const cleanPath = (current_path || '').replace(/^[\\/]+/, '');
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
        const reqPath = (req.query.path || '').replace(/^[\\/]+/, '');
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
