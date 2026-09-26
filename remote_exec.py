import paramiko
import sys

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

def run(cmd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
        print(f"=== Running: {cmd} ===")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        if out:
            print("STDOUT:\n" + out)
        if err:
            print("STDERR:\n" + err)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    cmd = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "uname -a; whoami; pwd; which node npm nginx mariadb mysqld cloudflared"
    run(cmd)
