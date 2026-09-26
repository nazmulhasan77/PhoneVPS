import paramiko

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

sftp = client.open_sftp()
path = "/data/data/com.termux/files/home/phonevps/inventory/inventory/app/Providers/AppServiceProvider.php"
with sftp.open(path, "r") as f:
    content = f.read().decode('utf-8')

old_part = """        //force https
        $url = parse_url(config('app.url'));

        if ($url['scheme'] == 'https') {
            \\URL::forceScheme('https');
        }"""

new_part = """        //force https and root URL
        \\URL::forceScheme('https');
        if (config('app.url')) {
            \\URL::forceRootUrl(config('app.url'));
        }"""

if old_part in content:
    content = content.replace(old_part, new_part)
    with sftp.open(path, "w") as f:
        f.write(content)
    print("Successfully replaced in AppServiceProvider.php!")
else:
    print("Could not find exact old_part block, checking alternative...")
    # fallback replace
    content = content.replace("if ($url['scheme'] == 'https') {\n            \\URL::forceScheme('https');\n        }", "\\URL::forceScheme('https');\n        if (config('app.url')) { \\URL::forceRootUrl(config('app.url')); }")
    with sftp.open(path, "w") as f:
        f.write(content)
    print("Replaced with fallback!")

sftp.close()

# Clear Laravel caches & restart
def run(cmd):
    print(f">>> {cmd}")
    _, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode().strip())

run("cd ~/phonevps/inventory/inventory && php artisan optimize:clear")
run("bash ~/phonevps/start.sh")

# Test curl HTML output
_, stdout, _ = client.exec_command("curl -s -L http://127.0.0.1:8080/inventory/login")
html = stdout.read().decode()
for line in html.splitlines():
    if "action=" in line or "app.css" in line:
        print("Found in HTML:", line.strip())

client.close()
