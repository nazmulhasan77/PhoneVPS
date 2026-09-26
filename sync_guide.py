import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS, timeout=10)
sftp = client.open_sftp()

sftp.put("SETUP_GUIDE.md", "/data/data/com.termux/files/home/SETUP_GUIDE.md")
print("Uploaded SETUP_GUIDE.md to phone.")
client.close()
