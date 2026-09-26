import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

def run(cmd, timeout=300):
    print(f"Running: {cmd}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print("[OUT]:", out[:500])
    if err: print("[ERR]:", err[:500])
    return out, err

print("Extracting full inventory.zip quietly...")
run("cd /data/data/com.termux/files/home/phonevps && unzip -q -o inventory.zip -d inventory", timeout=300)

print("\nVerifying vendor directory:")
out, _ = run("ls /data/data/com.termux/files/home/phonevps/inventory/inventory/vendor | grep -E 'symfony|vlucas|spatie'")
print("Found packages:\n", out)

client.close()
