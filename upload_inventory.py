import paramiko
import os

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

LOCAL_FILE = r"C:\Users\miaso\OneDrive\Desktop\inventory\inventory.zip"
REMOTE_PATH = "/data/data/com.termux/files/home/phonevps/inventory.zip"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

sftp = client.open_sftp()

file_size = os.path.getsize(LOCAL_FILE)
print(f"Uploading: {LOCAL_FILE}")
print(f"File size: {file_size / (1024*1024):.2f} MB")
print(f"Destination: {REMOTE_PATH}")

uploaded = [0]

def progress(transferred, total):
    pct = (transferred / total) * 100
    print(f"\rProgress: {transferred/(1024*1024):.1f} MB / {total/(1024*1024):.1f} MB ({pct:.1f}%)", end="", flush=True)

sftp.put(LOCAL_FILE, REMOTE_PATH, callback=progress)
print("\nUpload complete!")

sftp.close()
client.close()
