import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

def run(cmd, timeout=300):
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print(out)
    if err: print("[ERR]", err)
    return out, err

# Step 1: Create database
print("=== Creating database butterf3_ims ===")
run("mariadb -u root -e 'CREATE DATABASE IF NOT EXISTS butterf3_ims CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'")

# Step 2: Import SQL
print("\n=== Importing SQL (18MB)... ===")
out, err = run(
    "mariadb -u root butterf3_ims < /data/data/com.termux/files/home/phonevps/inventory/butterf3_ims.sql && echo IMPORT_SUCCESS",
    timeout=300
)

if "IMPORT_SUCCESS" in out:
    print("\n✅ Import successful!")
else:
    print("\n[RESULT]", out, err)

# Step 3: Show tables
print("\n=== Tables in butterf3_ims ===")
run("mariadb -u root butterf3_ims -e 'SHOW TABLES;'")

client.close()
