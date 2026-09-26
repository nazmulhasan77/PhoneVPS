import paramiko
import time

HOST = "192.168.0.145"
PORT = 8022
USER = "u0_a123"
PASS = "123456"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=PORT, username=USER, password=PASS)

def run(cmd, timeout=30):
    print(f"\n[RUN] {cmd[:80]}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if out: print("[OUT]:", out)
    if err and "Deprecated" not in err: print("[ERR]:", err[:300])
    return out, err

# 1. Update TrustProxies.php
print("--- 1. Updating TrustProxies.php ---")
trust_proxies_code = """<?php

namespace App\Http\Middleware;

use Illuminate\Http\Middleware\TrustProxies as Middleware;
use Illuminate\Http\Request;

class TrustProxies extends Middleware
{
    /**
     * The trusted proxies for this application.
     *
     * @var array<int, string>|string|null
     */
    protected $proxies = '*';

    /**
     * The headers that should be used to detect proxies.
     *
     * @var int
     */
    protected $headers =
        Request::HEADER_X_FORWARDED_FOR |
        Request::HEADER_X_FORWARDED_HOST |
        Request::HEADER_X_FORWARDED_PORT |
        Request::HEADER_X_FORWARDED_PROTO |
        Request::HEADER_X_FORWARDED_AWS_ELB;
}
"""

sftp = client.open_sftp()
with sftp.open("/data/data/com.termux/files/home/phonevps/inventory/inventory/app/Http/Middleware/TrustProxies.php", "w") as f:
    f.write(trust_proxies_code)
print("TrustProxies.php updated.")

# 2. Update AppServiceProvider.php to forceScheme('https') and forceRootUrl('https://vps.shokherpolli.com/inventory')
print("--- 2. Updating AppServiceProvider.php ---")
with sftp.open("/data/data/com.termux/files/home/phonevps/inventory/inventory/app/Providers/AppServiceProvider.php", "r") as f:
    content = f.read().decode('utf-8')

# Insert URL::forceScheme and URL::forceRootUrl at top of boot()
if "URL::forceScheme('https')" not in content:
    boot_pos = content.find("public function boot()")
    if boot_pos != -1:
        brace_pos = content.find("{", boot_pos)
        injection = """
        \\Illuminate\\Support\\Facades\\URL::forceScheme('https');
        if (!empty(config('app.url'))) {
            \\Illuminate\\Support\\Facades\\URL::forceRootUrl(config('app.url'));
        }
"""
        content = content[:brace_pos+1] + injection + content[brace_pos+1:]
        with sftp.open("/data/data/com.termux/files/home/phonevps/inventory/inventory/app/Providers/AppServiceProvider.php", "w") as f:
            f.write(content)
        print("AppServiceProvider.php updated with forceRootUrl.")
    else:
        print("Could not find boot() in AppServiceProvider.php")
else:
    print("AppServiceProvider.php already has forceScheme.")

sftp.close()

# 3. Clear Laravel Cache
print("--- 3. Clearing Laravel Cache ---")
run("cd ~/phonevps/inventory/inventory && php artisan optimize:clear")

# 4. Test what URL route('login') and asset(...) produce
test_php = """
require __DIR__ . '/vendor/autoload.php';
$app = require_once __DIR__ . '/bootstrap/app.php';
$kernel = $app->make(Illuminate\\Contracts\\Http\\Kernel::class);
$response = $kernel->handle(
    $request = Illuminate\\Http\\Request::capture()
);
echo 'App URL: ' . config('app.url') . PHP_EOL;
echo 'Route Login: ' . route('login') . PHP_EOL;
echo 'Asset Test: ' . asset('css/app.css') . PHP_EOL;
"""
run(f"cd ~/phonevps/inventory/inventory && php -r \"{test_php}\"")

# 5. Restart Services
print("--- 5. Restarting Services ---")
run("bash ~/phonevps/start.sh")
time.sleep(3)

# 6. Test login page HTML output
print("--- 6. Testing /inventory/login HTML ---")
run("curl -s -L http://127.0.0.1:8080/inventory/login | grep -i 'form action' || curl -s -L http://127.0.0.1:8080/inventory/login | head -n 30")

client.close()
