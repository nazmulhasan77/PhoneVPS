import paramiko
import os

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

os.makedirs("src/public", exist_ok=True)
os.makedirs("src/config", exist_ok=True)

files_to_pull = [
    ("/data/data/com.termux/files/home/phonevps/server.js", "src/server.js"),
    ("/data/data/com.termux/files/home/phonevps/package.json", "src/package.json"),
    ("/data/data/com.termux/files/home/phonevps/start.sh", "src/start.sh"),
    ("/data/data/com.termux/files/home/phonevps/stop.sh", "src/stop.sh"),
    ("/data/data/com.termux/files/home/phonevps/status.sh", "src/status.sh"),
    ("/data/data/com.termux/files/home/phonevps/public/index.html", "src/public/index.html"),
    ("/data/data/com.termux/files/home/phonevps/public/files.html", "src/public/files.html"),
    ("/data/data/com.termux/files/usr/etc/nginx/nginx.conf", "src/config/nginx.conf"),
]

for remote_p, local_p in files_to_pull:
    try:
        sftp.get(remote_p, local_p)
        print(f"Pulled: {remote_p} -> {local_p}")
    except Exception as e:
        print(f"Error pulling {remote_p}: {e}")

client.close()
