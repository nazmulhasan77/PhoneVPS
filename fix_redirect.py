import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)

# Remove empty static directory public/files if present to prevent redirect
stdin, stdout, stderr = client.exec_command("rm -rf ~/phonevps/public/files")
print(stdout.read().decode())
client.close()
