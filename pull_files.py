import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

def run(cmd):
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print("[ERR]", err)

# Pull latest files from phone
files = {
    "~/phonevps/start.sh": "src/start.sh",
    "~/phonevps/stop.sh": "src/stop.sh",
    "~/phonevps/status.sh": "src/status.sh",
    "/data/data/com.termux/files/usr/etc/nginx/nginx.conf": "src/config/nginx.conf",
}

sftp = client.open_sftp()
import os

for remote, local in files.items():
    remote_path = remote.replace("~", "/data/data/com.termux/files/home")
    os.makedirs(os.path.dirname(local), exist_ok=True)
    try:
        sftp.get(remote_path, local)
        print(f"Pulled: {local}")
    except Exception as e:
        print(f"Failed {local}: {e}")

sftp.close()
client.close()
print("\nDone pulling files.")
