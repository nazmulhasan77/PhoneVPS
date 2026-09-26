# PhoneVPS 📱⚡

> Transform any Android smartphone into a complete, powerful 24/7 Cloud Linux VPS Server with Node.js, MariaDB/MySQL, PHP, Nginx, official phpMyAdmin, Web File Explorer, and free global HTTPS access via Cloudflare Named Tunnels.

---

## 🌟 Key Features

- 🟢 **Node.js Express Engine**: High-performance REST API and dynamic backend server (Port `3000`).
- 🗄️ **MariaDB / MySQL Server**: Native relational database server (Port `3306`) with connection pooling.
- 🗃️ **Official phpMyAdmin (v5.2.1)**: Full-featured graphical database management interface at `/phpmyadmin/`.
- 📁 **Web File Explorer & Storage**: Web-based file manager at `/files` for downloading, uploading, creating folders, and deleting files.
- 🌐 **Nginx Reverse Proxy**: High-speed reverse proxy handling routing and static assets (Port `8080`).
- ☁️ **Cloudflare Tunnel (Zero Trust)**: Global secure HTTPS domain routing (`https://vps.shokherpolli.com`) without port forwarding or static public IPs.
- ⚡ **Real-Time Hardware & Telemetry Dashboard**: Live CPU Load (%) across all cores, RAM usage meter, internal storage metrics, and phone hardware specs.

---

## 🏗️ Architecture Overview

```
                          Internet (HTTPS)
                                 │
                    ┌────────────▼────────────┐
                    │ Cloudflare Edge Network │
                    │  (SSL / Anycast Proxy)  │
                    └────────────┬────────────┘
                                 │ Cloudflare Tunnel (QUIC)
                    ┌────────────▼────────────┐
                    │ Android Smartphone VPS  │
                    │      (Termux Linux)     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    Nginx Proxy (8080)   │
                    └──────┬────────────┬─────┘
                           │            │
             ┌─────────────▼────┐  ┌────▼──────────────┐
             │ Node.js API (3000)│  │ PHP Engine (8081) │
             │ & Web Dashboard  │  │ & phpMyAdmin      │
             └─────────────┬────┘  └────┬──────────────┘
                           │            │
                    ┌──────▼────────────▼─────┐
                    │     MariaDB (3306)      │
                    │      (phonevps_db)      │
                    └─────────────────────────┘
```

---

## 📱 Hardware & Specifications

- **Device**: Motorola moto g pure
- **CPU**: MediaTek Helio MT6765 (Octa-Core @ 2.0 GHz)
- **Architecture**: ARMv7 (32-bit Linux)
- **RAM**: 3 GB LPDDR4
- **Operating System**: Android 12 (Linux Kernel 4.19)
- **Storage**: 23 GB Internal Storage

---

## 🚀 Live Endpoints & Routes

| URL / Route | Description |
|---|---|
| `https://vps.shokherpolli.com/` | Main Interactive Server Dashboard & Telemetry |
| `https://vps.shokherpolli.com/files` | Web Storage & File Explorer |
| `https://vps.shokherpolli.com/phpmyadmin/` | Official phpMyAdmin Database Manager |
| `https://vps.shokherpolli.com/api/status` | System Telemetry & Phone Hardware JSON API |
| `https://vps.shokherpolli.com/api/messages` | MariaDB Database CRUD Demo API |
| `https://vps.shokherpolli.com/api/files/list` | File Explorer Storage JSON API |

---

## 🛠️ Service Management Commands (Termux)

Inside your Termux terminal on the phone:

```bash
# Start all VPS services
bash ~/phonevps/start.sh
# or quick alias:
vps-start

# Check live status & public URLs
bash ~/phonevps/status.sh
# or quick alias:
vps-status

# Stop all services
bash ~/phonevps/stop.sh
# or quick alias:
vps-stop
```

---

## 📂 Project Structure

```
├── src/
│   ├── server.js              # Node.js Express server & API endpoints
│   ├── package.json           # Node dependencies
│   ├── start.sh               # Complete service startup script
│   ├── stop.sh                # Service termination script
│   ├── status.sh              # Live status inspection script
│   ├── config/
│   │   └── nginx.conf         # Nginx reverse proxy configuration
│   └── public/
│       ├── index.html         # Main modern VPS Dashboard & Telemetry UI
│       └── files.html         # Web File Explorer SPA
├── deploy.py                  # Remote deployment automation helper
└── README.md
```

---

## 📜 License
MIT License &bull; Created with ❤️ for Android VPS Development.
