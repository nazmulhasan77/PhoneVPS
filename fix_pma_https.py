import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

config_inc = """<?php
declare(strict_types=1);

$_SERVER['HTTPS'] = 'on';
$_SERVER['SERVER_PORT'] = '443';

error_reporting(0);
ini_set('display_errors', '0');

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

/* HTTPS and URL configuration */
$cfg['PmaAbsoluteUri'] = 'https://vps.shokherpolli.com/phpmyadmin/';
$cfg['SendErrorReports'] = 'never';
"""

with sftp.file('/data/data/com.termux/files/home/phonevps/phpmyadmin/config.inc.php', 'w') as f:
    f.write(config_inc)

client.close()
