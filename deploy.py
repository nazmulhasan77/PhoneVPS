import paramiko
import os
import sys

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

def get_ssh_sftp():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
    sftp = client.open_sftp()
    return client, sftp

def run_cmd(client, cmd):
    print(f"--> [CMD]: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    if out:
        print("[OUT]:\n" + out.strip())
    if err:
        print("[ERR]:\n" + err.strip())
    return out, err

def upload_text(sftp, remote_path, content):
    with sftp.file(remote_path, 'w') as f:
        f.write(content)
    print(f"Uploaded -> {remote_path}")

if __name__ == "__main__":
    client, sftp = get_ssh_sftp()
    if len(sys.argv) > 1:
        run_cmd(client, " ".join(sys.argv[1:]))
    client.close()
