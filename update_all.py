import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

TOKEN = "eyJhIjoiOWY0YjdjOWU3MTUyZDM1OTIwYWI5YjQ2OWVhMWMwMGYiLCJ0IjoiZDgwY2JiZjktOTYxYy00NjkyLThhYzctYTc1MzhiNTM5N2RlIiwicyI6Ik9UZGtZekZpT1RRdFltRXlNQzAwTmprekxXSmhNR010TURZMVptTTJOekF5WlRGayJ9"
DOMAIN = "https://vps.shokherpolli.com"

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

# 1. Update start.sh
start_sh = f"""#!/data/data/com.termux/files/usr/bin/bash

echo "=================================================="
echo "          [PhoneVPS] Starting All Services         "
echo "=================================================="

# 1. Start MariaDB (MySQL)
if ! pgrep -f "mariadbd" > /dev/null; then
    echo "[1/4] Starting MariaDB (MySQL)..."
    mariadbd-safe --nowatch > /dev/null 2>&1
    sleep 3
else
    echo "[1/4] MariaDB is already running."
fi

# 2. Start Node.js API Server
pkill -f "node server.js" 2>/dev/null
echo "[2/4] Starting Node.js Server..."
cd /data/data/com.termux/files/home/phonevps
nohup node server.js > ~/phonevps/logs/node.log 2>&1 &
sleep 2

# 3. Start Nginx
pkill -f "nginx" 2>/dev/null
echo "[3/4] Starting Nginx..."
nginx
sleep 1

# 4. Start Cloudflare Tunnel
pkill -f "cloudflared" 2>/dev/null
echo "[4/4] Starting Cloudflare Named Tunnel..."
nohup cloudflared tunnel run --token "{TOKEN}" > ~/phonevps/logs/cf.log 2>&1 &

sleep 3

echo "=================================================="
echo "         PhoneVPS IS LIVE AND OPERATIONAL!        "
echo "=================================================="
echo "Local Nginx Proxy    : http://127.0.0.1:8080"
echo "Node.js API Server   : http://127.0.0.1:3000"
echo "MariaDB / MySQL Port : 3306 (phonevps_db)"
echo "Public Custom Domain : {DOMAIN}"
echo "=================================================="
"""

# 2. Update status.sh
status_sh = f"""#!/data/data/com.termux/files/usr/bin/bash
echo "=========================================="
echo "         PhoneVPS Live Status Check       "
echo "=========================================="
echo -n "MariaDB (MySQL)   : "
pgrep -f "mariadbd" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Node.js Engine    : "
pgrep -f "node server.js" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Nginx Proxy       : "
pgrep -f "nginx" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo -n "Cloudflare Tunnel : "
pgrep -f "cloudflared" >/dev/null && echo "[RUNNING]" || echo "[STOPPED]"
echo "------------------------------------------"
echo "Custom Domain     : {DOMAIN}"
echo "=========================================="
"""

# 3. Update stop.sh
stop_sh = """#!/data/data/com.termux/files/usr/bin/bash
echo "=== Stopping PhoneVPS Services ==="
pkill -f "cloudflared"
pkill -f "nginx"
pkill -f "node server.js"
mariadb-admin -u root shutdown 2>/dev/null || pkill -f mariadbd
echo "All PhoneVPS services have been stopped."
"""

# 4. Update index.html with custom domain display & modern branding
index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PhoneVPS - Android Smartphone VPS</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-base: #0a0e17;
            --bg-card: rgba(18, 26, 42, 0.8);
            --bg-card-hover: rgba(28, 40, 65, 0.9);
            --border-color: rgba(99, 102, 241, 0.25);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.4);
            --accent: #06b6d4;
            --accent-glow: rgba(6, 182, 212, 0.4);
            --success: #10b981;
            --success-glow: rgba(16, 185, 129, 0.3);
            --text-main: #f8fafc;
            --text-dim: #94a3b8;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 28px 16px;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.18) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.18) 0px, transparent 50%),
                radial-gradient(at 50% 50%, rgba(15, 23, 42, 0.6) 0px, transparent 100%);
            background-attachment: fixed;
        }}

        .container {{
            max-width: 1100px;
            width: 100%;
        }}

        header {{
            text-align: center;
            margin-bottom: 36px;
            position: relative;
        }}

        .badge-live {{
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
            margin-bottom: 16px;
            box-shadow: 0 0 20px var(--success-glow);
        }}

        .pulse-dot {{
            width: 8px;
            height: 8px;
            background-color: #10b981;
            border-radius: 50%;
            animation: pulse 1.8s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}

        h1 {{
            font-size: 2.6rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        .domain-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.4);
            color: #a5b4fc;
            padding: 6px 14px;
            border-radius: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            font-weight: 600;
            margin-bottom: 12px;
        }}

        .subtitle {{
            color: var(--text-dim);
            font-size: 1.05rem;
            max-width: 650px;
            margin: 0 auto;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}

        .card {{
            background: var(--bg-card);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--border-color);
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            transition: all 0.3s ease;
        }}

        .card:hover {{
            border-color: var(--primary);
            box-shadow: 0 12px 40px var(--primary-glow);
        }}

        .card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 18px;
        }}

        .card-title {{
            font-size: 1.15rem;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #fff;
        }}

        .icon {{
            font-size: 1.3rem;
        }}

        .stack-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .stack-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            background: rgba(15, 23, 42, 0.6);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .stack-name {{
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .stack-status {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
            padding: 4px 10px;
            border-radius: 6px;
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }}

        .stat-group {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }}

        .stat-box {{
            background: rgba(15, 23, 42, 0.6);
            padding: 14px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }}

        .stat-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-dim);
            margin-bottom: 4px;
        }}

        .stat-value {{
            font-size: 1.25rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            color: #38bdf8;
        }}

        .progress-bar-bg {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            margin-top: 10px;
            overflow: hidden;
        }}

        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, #6366f1, #06b6d4);
            border-radius: 999px;
            transition: width 0.5s ease;
        }}

        .form-group {{
            margin-bottom: 12px;
        }}

        input, textarea {{
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
        }}

        input:focus, textarea:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 10px var(--accent-glow);
        }}

        button.btn {{
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
        }}

        button.btn:active {{
            transform: scale(0.98);
        }}

        .message-feed {{
            max-height: 240px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-top: 16px;
            padding-right: 4px;
        }}

        .message-feed::-webkit-scrollbar {{
            width: 4px;
        }}
        .message-feed::-webkit-scrollbar-thumb {{
            background: var(--border-color);
            border-radius: 4px;
        }}

        .msg-bubble {{
            background: rgba(15, 23, 42, 0.7);
            border-left: 3px solid var(--accent);
            padding: 10px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
        }}

        .msg-author {{
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 2px;
            display: flex;
            justify-content: space-between;
        }}

        .msg-time {{
            font-size: 0.7rem;
            color: var(--text-dim);
            font-weight: normal;
        }}

        footer {{
            margin-top: 30px;
            text-align: center;
            color: var(--text-dim);
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="badge-live">
                <div class="pulse-dot"></div>
                PHONE VPS ONLINE &amp; SYNCED
            </div>
            <h1>Android Smartphone VPS</h1>
            <div class="domain-pill">🔒 {DOMAIN.replace('https://', '')}</div>
            <p class="subtitle">Full-stack server environment powered by Node.js, MariaDB, Nginx, and Cloudflare Named Tunnel running natively on Android.</p>
        </header>

        <div class="grid">
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
                        <div class="stack-name">☁️ Cloudflare Named Tunnel</div>
                        <div class="stack-status" style="color: #38bdf8; border-color: rgba(56,189,248,0.3); background: rgba(56,189,248,0.1);">Custom Domain</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid" style="grid-template-columns: 1fr;">
            <div class="card">
                <div class="card-header">
                    <div class="card-title"><span class="icon">💬</span> Live Database Guestbook (MariaDB + API Test)</div>
                </div>
                <p style="color: var(--text-dim); font-size: 0.9rem; margin-bottom: 16px;">
                    Write a message below to test real-time write and read operations on your phone's native MariaDB database through your custom domain!
                </p>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                    <form id="msgForm" onsubmit="postMessage(event)">
                        <div class="form-group">
                            <input type="text" id="authorInput" placeholder="Your Name or Handle" required>
                        </div>
                        <div class="form-group">
                            <textarea id="messageInput" rows="3" placeholder="Write a note (e.g. 'Hello from custom domain!')..." required></textarea>
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
            <p>PhoneVPS &bull; Hosted on Android Device &bull; {DOMAIN}</p>
        </footer>
    </div>

    <script>
        async function fetchTelemetry() {{
            try {{
                const res = await fetch('/api/status');
                const data = await res.json();
                if (data.success) {{
                    const s = data.server;
                    document.getElementById('uptimeBadge').innerText = 'UP: ' + s.uptime_formatted;
                    document.getElementById('valArch').innerText = s.arch;
                    document.getElementById('valRam').innerText = `${{s.memory.used_mb}} / ${{s.memory.total_mb}} MB`;
                    document.getElementById('valNode').innerText = s.node_version;
                    document.getElementById('ramPercent').innerText = `${{s.memory.usage_percent}}%`;
                    document.getElementById('ramFill').style.width = `${{s.memory.usage_percent}}%`;
                    document.getElementById('valDb').innerText = s.database.status.startsWith('Connected') ? 'Online' : 'Error';
                }}
            }} catch (e) {{
                console.error("Status fetch error", e);
            }}
        }}

        async function fetchMessages() {{
            try {{
                const res = await fetch('/api/messages');
                const data = await res.json();
                const list = document.getElementById('messageList');
                if (data.success && data.messages.length > 0) {{
                    list.innerHTML = data.messages.map(m => `
                        <div class="msg-bubble">
                            <div class="msg-author">
                                <span>${{escapeHtml(m.name)}}</span>
                                <span class="msg-time">${{new Date(m.created_at).toLocaleTimeString()}}</span>
                            </div>
                            <div>${{escapeHtml(m.message)}}</div>
                        </div>
                    `).join('');
                }} else {{
                    list.innerHTML = '<div style="color: var(--text-dim); font-size: 0.85rem;">No messages yet. Be the first to write!</div>';
                }}
            }} catch (e) {{
                console.error("Messages fetch error", e);
            }}
        }}

        async function postMessage(e) {{
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const name = document.getElementById('authorInput').value.trim();
            const message = document.getElementById('messageInput').value.trim();
            if (!name || !message) return;

            btn.disabled = true;
            btn.innerText = 'Saving to Database...';

            try {{
                const res = await fetch('/api/messages', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name, message }})
                }});
                const result = await res.json();
                if (result.success) {{
                    document.getElementById('messageInput').value = '';
                    await fetchMessages();
                }} else {{
                    alert('Error: ' + result.error);
                }}
            }} catch (err) {{
                alert('Network error: ' + err.message);
            }} finally {{
                btn.disabled = false;
                btn.innerText = 'Send to MySQL Database';
            }}
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.innerText = text || '';
            return div.innerHTML;
        }}

        fetchTelemetry();
        fetchMessages();
        setInterval(fetchTelemetry, 3000);
        setInterval(fetchMessages, 5000);
    </script>
</body>
</html>
"""

# 5. Write all updated files
with sftp.file('/data/data/com.termux/files/home/phonevps/start.sh', 'w') as f:
    f.write(start_sh)

with sftp.file('/data/data/com.termux/files/home/phonevps/status.sh', 'w') as f:
    f.write(status_sh)

with sftp.file('/data/data/com.termux/files/home/phonevps/stop.sh', 'w') as f:
    f.write(stop_sh)

with sftp.file('/data/data/com.termux/files/home/phonevps/public/index.html', 'w') as f:
    f.write(index_html)

# 6. Add handy aliases to ~/.bashrc for quick access
bashrc_additions = """
# --- PhoneVPS Aliases ---
alias vps-start='bash ~/phonevps/start.sh'
alias vps-status='bash ~/phonevps/status.sh'
alias vps-stop='bash ~/phonevps/stop.sh'
"""
try:
    with sftp.file('/data/data/com.termux/files/home/.bashrc', 'r') as f:
        content = f.read().decode('utf-8')
except:
    content = ""

if 'PhoneVPS Aliases' not in content:
    with sftp.file('/data/data/com.termux/files/home/.bashrc', 'w') as f:
        f.write(content + bashrc_additions)

run("chmod +x ~/phonevps/*.sh")

# 7. Restart all services cleanly with start.sh
print("\n--- Executing clean start.sh ---")
run("bash ~/phonevps/start.sh")

time.sleep(3)
run("bash ~/phonevps/status.sh")

client.close()
