import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

# Move the core file to adminer.php
stdin, stdout, stderr = client.exec_command("mv ~/phonevps/phpmyadmin/index.php ~/phonevps/phpmyadmin/adminer.php 2>/dev/null")

# Create wrapper index.php
index_wrapper = """<?php
error_reporting(0);
ini_set('display_errors', 0);

function adminer_object() {
    class AdminerCustom extends Adminer {
        function login($login, $password) {
            return true; // Allow passwordless root login
        }
        function name() {
            return 'PhoneVPS Database Manager (phpMyAdmin)';
        }
    }
    return new AdminerCustom;
}

include __DIR__ . '/adminer.php';
?>"""

with sftp.file('/data/data/com.termux/files/home/phonevps/phpmyadmin/index.php', 'w') as f:
    f.write(index_wrapper)

client.close()
