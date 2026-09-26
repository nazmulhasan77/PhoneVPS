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
    return out, err

# Check php.ini values
print("=== PHP ini values ===")
out, _ = run("grep -E 'upload_max_filesize|post_max_size|memory_limit' /data/data/com.termux/files/usr/etc/php.ini")
print(out)

# Check nginx client_max_body_size
print("\n=== Nginx config ===")
out, _ = run("grep client_max_body_size /data/data/com.termux/files/usr/etc/nginx/nginx.conf")
print(out)

# Check phpMyAdmin config
print("\n=== phpMyAdmin config.inc.php ===")
out, _ = run("grep -i 'upload\|memory\|max' ~/phonevps/phpmyadmin/config.inc.php")
print(out)

# Check start.sh PHP command
print("\n=== start.sh PHP line ===")
out, _ = run("grep 'php -S' ~/phonevps/start.sh")
print(out)

# Quick PHP runtime check via temp file
print("\n=== PHP runtime values ===")
run("echo '<?php echo ini_get(\"upload_max_filesize\").\"\\n\".ini_get(\"post_max_size\").\"\\n\".ini_get(\"memory_limit\");' > /tmp/chk.php")
out, err = run("php -d upload_max_filesize=500M -d post_max_size=500M -d memory_limit=512M /tmp/chk.php")
print("upload_max_filesize:", out.split("\n")[0] if out else err)
print("post_max_size:", out.split("\n")[1] if len(out.split("\n")) > 1 else "")
print("memory_limit:", out.split("\n")[2] if len(out.split("\n")) > 2 else "")

client.close()
