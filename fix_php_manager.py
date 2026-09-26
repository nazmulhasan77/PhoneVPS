import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

# Download fresh adminer core
stdin, stdout, stderr = client.exec_command("curl -sL https://github.com/vrana/adminer/releases/download/v4.8.1/adminer-4.8.1-mysql.php -o ~/phonevps/phpmyadmin/adminer-core.php")
print("Downloaded core:", stdout.read().decode())

wrapper_php = """<?php
error_reporting(0);
@ini_set('display_errors', '0');

function adminer_object() {
    class AdminerCustom extends Adminer {
        function name() {
            return 'PhoneVPS Database Manager';
        }
        function login($login, $password) {
            return true;
        }
    }
    return new AdminerCustom;
}

include __DIR__ . '/adminer-core.php';
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/phpmyadmin/index.php', 'w') as f:
    f.write(wrapper_php)

# Restart php server
stdin, stdout, stderr = client.exec_command("pkill -f 'php -S'; cd ~/phonevps/phpmyadmin && nohup php -S 127.0.0.1:8081 index.php </dev/null >/data/data/com.termux/files/home/phonevps/logs/php.log 2>&1 &")
print("Restarted PHP:", stdout.read().decode())

time.sleep(2)

stdin, stdout, stderr = client.exec_command("curl -s http://127.0.0.1:8081/ | head -n 25")
print("PHP Server response:\n" + stdout.read().decode())

client.close()
