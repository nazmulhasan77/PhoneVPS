# 📱 Complete Step-by-Step Setup Guide: Android PhoneVPS

A clean, step-by-step practical guide to turn any Android smartphone into a 24/7 Cloud Linux Server with **Node.js, MariaDB/MySQL, Official phpMyAdmin, Nginx Reverse Proxy, Web File Manager, and Cloudflare Named Tunnels** on a Custom Domain.

---

## 📋 Overview of the Setup Flow

```
Step 1: Termux & SSH Setup on Phone
   ⬇
Step 2: Install Server Packages (Node, MySQL, PHP, Nginx, Cloudflared)
   ⬇
Step 3: Setup MariaDB Database
   ⬇
Step 4: Clone / Setup Server Files & Web Dashboard
   ⬇
Step 5: Setup Official phpMyAdmin
   ⬇
Step 6: Configure Nginx Reverse Proxy
   ⬇
Step 7: Connect Cloudflare Named Tunnel & Custom Domain
   ⬇
Step 8: Setup Startup Scripts & Auto-Boot
   ⬇
Step 9: Android 24/7 Battery Optimizations
```

---

## 🛠️ Step 1: Install & Prepare Termux

1. **Install Termux** from [F-Droid](https://f-droid.org/packages/com.termux/) *(Never use the Play Store version)*.
2. Open Termux on your phone and run the following commands:
   ```bash
   # Prevent Android from killing Termux when the screen is locked
   termux-wake-lock

   # Grant storage permission
   termux-setup-storage

   # Update package repositories
   pkg update -y && pkg upgrade -y
   ```

3. **Enable SSH Access (Optional, to control phone from PC):**
   ```bash
   # Install OpenSSH
   pkg install -y openssh

   # Set a password for your Termux account
   passwd

   # Start the SSH daemon on port 8022
   sshd
   ```

---

## 📦 Step 2: Install All Server Packages

Run a single command in Termux to install all required services:

```bash
pkg install -y nodejs-lts mariadb php nginx cloudflared git tar curl
```

---

## 🗄️ Step 3: Configure MariaDB (MySQL)

1. **Initialize the database directory:**
   ```bash
   mariadb-install-db
   ```

2. **Start MariaDB in the background:**
   ```bash
   mariadbd-safe --nowatch
   ```

3. **Create the Project Database & Tables:**
   Open MySQL terminal:
   ```bash
   mariadb -u root
   ```
   Paste the following SQL commands:
   ```sql
   CREATE DATABASE IF NOT EXISTS phonevps_db;
   USE phonevps_db;

   -- Guestbook / Live Messages Table
   CREATE TABLE IF NOT EXISTS messages (
       id INT AUTO_INCREMENT PRIMARY KEY,
       name VARCHAR(100) NOT NULL,
       message TEXT NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );

   -- Server Info / Stats Table
   CREATE TABLE IF NOT EXISTS server_stats (
       id INT AUTO_INCREMENT PRIMARY KEY,
       key_name VARCHAR(100) UNIQUE,
       key_value VARCHAR(255),
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
   );

   INSERT INTO server_stats (key_name, key_value) VALUES 
   ('device_type', 'Android Phone VPS'),
   ('status', 'Online & Operational')
   ON DUPLICATE KEY UPDATE key_value=VALUES(key_value);

   EXIT;
   ```

---

## 🌐 Step 4: Setup Project Code & Node.js Engine

1. **Clone this repository onto your phone:**
   ```bash
   cd ~
   git clone https://github.com/nazmulhasan77/PhoneVPS.git phonevps
   cd ~/phonevps
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

   *(This installs `express`, `cors`, `mysql2`, and `multer` for the API and Web File Manager)*.

---

## 🗃️ Step 5: Setup Official phpMyAdmin (v5.2.1)

1. **Download and extract official phpMyAdmin:**
   ```bash
   mkdir -p ~/phonevps/phpmyadmin ~/phonevps/pma_tmp
   curl -sL https://files.phpmyadmin.net/phpMyAdmin/5.2.1/phpMyAdmin-5.2.1-all-languages.tar.gz -o ~/phonevps/pma.tar.gz
   tar -xzf ~/phonevps/pma.tar.gz -C ~/phonevps/pma_tmp
   cp -rf ~/phonevps/pma_tmp/phpMyAdmin-5.2.1-all-languages/* ~/phonevps/phpmyadmin/
   rm -rf ~/phonevps/pma_tmp ~/phonevps/pma.tar.gz
   mkdir -p ~/phonevps/phpmyadmin/tmp && chmod 777 ~/phonevps/phpmyadmin/tmp
   ```

2. **Create phpMyAdmin configuration (`config.inc.php`):**
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

   $cfg['Servers'][$i]['auth_type'] = 'cookie';
   $cfg['Servers'][$i]['host'] = '127.0.0.1';
   $cfg['Servers'][$i]['port'] = '3306';
   $cfg['Servers'][$i]['connect_type'] = 'tcp';
   $cfg['Servers'][$i]['compress'] = false;
   $cfg['Servers'][$i]['AllowNoPassword'] = true;
   $cfg['Servers'][$i]['hide_db'] = '^(information_schema|performance_schema|sys)$';

   $cfg['UploadDir'] = '';
   $cfg['SaveDir'] = '';
   $cfg['TempDir'] = __DIR__ . '/tmp';
   $cfg['PmaAbsoluteUri'] = 'https://vps.shokherpolli.com/phpmyadmin/';
   $cfg['SendErrorReports'] = 'never';
   ```

---

## 🔀 Step 6: Configure Nginx Reverse Proxy

Copy the pre-configured Nginx config to Termux Nginx directory:

```bash
cp ~/phonevps/src/config/nginx.conf /data/data/com.termux/files/usr/etc/nginx/nginx.conf
```

**What this Nginx configuration does:**
- Listens on Port `8080`.
- Routes `/phpmyadmin/` to PHP built-in server on Port `8081`.
- Routes all other traffic (`/`, `/api`, `/files`) to Node.js server on Port `3000`.

---

## ☁️ Step 7: Cloudflare Zero Trust Tunnel & Custom Domain

To make your phone accessible globally over HTTPS without port forwarding:

1. **Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)**:
   - Go to **Zero Trust** ➔ **Networks** ➔ **Tunnels**.
   - Click **Add a Tunnel** ➔ Select **Cloudflared** ➔ Name it (e.g. `phone-vps`).
   - Copy your tunnel token (`eyJh...`).

2. **Add a Public Hostname (Route):**
   - Click **Add route** ➔ Choose **Published application**.
   - **Subdomain**: `vps` (or leave blank for root domain).
   - **Domain**: Select your domain (e.g. `shokherpolli.com`).
   - **Service Type**: `HTTP`
   - **Service URL**: `http://127.0.0.1:8080`
   - Click **Save**.

3. **Set Nameservers at your Domain Registrar (Spaceship / Namecheap):**
   - Change your domain's nameservers to Cloudflare's 2 assigned nameservers (e.g. `dalary.ns.cloudflare.com`, `tate.ns.cloudflare.com`).

4. **Add the Token on your Phone:**
   - In `~/phonevps/src/start.sh`, paste your token inside `cloudflared tunnel run --token "YOUR_TOKEN"`.

---

## 🚀 Step 8: Start Services & Terminal Shortcuts

1. **Make scripts executable and copy to root:**
   ```bash
   chmod +x ~/phonevps/src/*.sh
   cp ~/phonevps/src/*.sh ~/phonevps/
   ```

2. **Add Quick Aliases to `~/.bashrc`:**
   ```bash
   cat << 'EOF' >> ~/.bashrc

   # --- PhoneVPS Aliases ---
   alias vps-start='bash ~/phonevps/start.sh'
   alias vps-status='bash ~/phonevps/status.sh'
   alias vps-stop='bash ~/phonevps/stop.sh'
   EOF
   source ~/.bashrc
   ```

3. **Start the VPS:**
   ```bash
   vps-start
   ```

4. **Check Live Status:**
   ```bash
   vps-status
   ```

---

## 🔋 Step 9: Android 24/7 Battery & Background Optimizations

To ensure Android does not kill your server in the background:

1. **Battery Unrestricted Mode:**
   - Android **Settings** ➔ **Apps** ➔ **Termux** ➔ **App battery usage** ➔ Choose **Unrestricted**.
2. **Lock App in Memory:**
   - Open Recent Apps on phone ➔ Tap the 🔒 **Lock** icon on the Termux card.
3. **Keep CPU Awake:**
   - Run `termux-wake-lock` in Termux.
4. **Auto-Start on Phone Reboot (Termux:Boot):**
   - Install **Termux:Boot** from F-Droid.
   - Run:
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

## 🎯 Live Access Summary

| Service | Address |
|---|---|
| **Web Dashboard & Live Telemetry** | `https://vps.shokherpolli.com` |
| **Web File Manager** | `https://vps.shokherpolli.com/files` |
| **Official phpMyAdmin** | `https://vps.shokherpolli.com/phpmyadmin/` |
| **MariaDB Default Login** | User: `root`, Password: *(blank)* |

---

## 🛠️ Handy Commands Cheat Sheet

| Task | Command |
|---|---|
| Start all services | `vps-start` |
| Check live status | `vps-status` |
| Stop all services | `vps-stop` |
| View Node.js logs | `tail -f ~/phonevps/logs/node.log` |
| View Cloudflare logs | `tail -f ~/phonevps/logs/cf.log` |
| View PHP logs | `tail -f ~/phonevps/logs/php.log` |
