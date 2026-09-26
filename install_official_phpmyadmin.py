import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

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

# 1. Clean old phpmyadmin and download official phpMyAdmin 5.2.1
print("Downloading official phpMyAdmin...")
run("rm -rf ~/phonevps/phpmyadmin && mkdir -p ~/phonevps/phpmyadmin ~/phonevps/pma_tmp")
run("curl -sL https://files.phpmyadmin.net/phpMyAdmin/5.2.1/phpMyAdmin-5.2.1-all-languages.tar.gz -o ~/phonevps/pma.tar.gz")

print("Extracting official phpMyAdmin...")
run("tar -xzf ~/phonevps/pma.tar.gz -C ~/phonevps/pma_tmp")
run("cp -rf ~/phonevps/pma_tmp/phpMyAdmin-5.2.1-all-languages/* ~/phonevps/phpmyadmin/")
run("rm -rf ~/phonevps/pma_tmp ~/phonevps/pma.tar.gz")
run("mkdir -p ~/phonevps/phpmyadmin/tmp && chmod 777 ~/phonevps/phpmyadmin/tmp")

# 2. Configure config.inc.php for official phpMyAdmin
config_inc = """<?php
declare(strict_types=1);

$cfg['blowfish_secret'] = 'phonevps-pma-super-secret-key-32-chars-long!';

$i = 0;
$i++;

/* Authentication type */
$cfg['Servers'][$i]['auth_type'] = 'cookie';
$cfg['Servers'][$i]['host'] = '127.0.0.1';
$cfg['Servers'][$i]['port'] = '3306';
$cfg['Servers'][$i]['connect_type'] = 'tcp';
$cfg['Servers'][$i]['compress'] = false;
$cfg['Servers'][$i]['AllowNoPassword'] = true;
$cfg['Servers'][$i]['hide_db'] = '^(information_schema|performance_schema|sys)$';

/* Directories for saving/loading files from server */
$cfg['UploadDir'] = '';
$cfg['SaveDir'] = '';
$cfg['TempDir'] = __DIR__ . '/tmp';

/* UI Customizations */
$cfg['ThemeDefault'] = 'pmahomme';
$cfg['NavigationDisplayServers'] = false;
$cfg['SendErrorReports'] = 'never';
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/phpmyadmin/config.inc.php', 'w') as f:
    f.write(config_inc)

print("Official phpMyAdmin configured successfully!")

# 3. Restart services
run("chmod +x ~/phonevps/*.sh && bash ~/phonevps/start.sh")
time.sleep(3)
run("bash ~/phonevps/status.sh")

client.close()
