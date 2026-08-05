import subprocess as sp
import random
import time

def curl_obtuse(url, method="GET", headers=None, data=None, timeout=10):
    cmd = ["curl", "-s", "-L", "--http1.1", "--compressed",
           "-w", "\nHTTP_CODE:%{http_code}\nSIZE:%{size_download}\nTIME:%{time_total}\nDNS:%{time_namelookup}\nCONN:%{time_connect}\n"]
    cmd += ["-m", str(timeout), "--connect-timeout", "2", "--max-time", str(timeout),
            "--retry", "1", "--retry-delay", "1", "--tcp-nodelay",
            "--dns-timeout", "2", "--speed-time", "3", "--speed-limit", "100"]
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
    ]
    cmd += ["-A", random.choice(uas)]
    cmd += ["-H", "Accept: application/json, text/plain, */*"]
    cmd += ["-H", "Accept-Language: en-US,en;q=0.9"]
    cmd += ["-H", "Accept-Encoding: gzip, deflate, br"]
    cmd += ["-H", "DNT: 1"]
    cmd += ["-H", "Connection: keep-alive"]
    cmd += ["-H", "Upgrade-Insecure-Requests: 1"]
    cmd += ["-H", "Sec-Fetch-Dest: document"]
    cmd += ["-H", "Sec-Fetch-Mode: navigate"]
    cmd += ["-H", "Sec-Fetch-Site: none"]
    cmd += ["-H", "Cache-Control: max-age=0"]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    if method == "POST" and data:
        cmd += ["-X", "POST", "-H", "Content-Type: application/json", "-d", data]
    elif method == "HEAD":
        cmd += ["-I"]
    cmd += [url]
    t0 = time.perf_counter()
    try:
        r = sp.run(cmd, capture_output=True, text=True, timeout=timeout+3)
    except sp.TimeoutExpired:
        return {"body": "", "code": "TIMEOUT", "ms": (time.perf_counter()-t0)*1000, "cmd": " ".join(cmd[:6])}
    elapsed = (time.perf_counter() - t0) * 1000
    body = r.stdout.split("HTTP_CODE:")[0] if "HTTP_CODE:" in r.stdout else r.stdout
    code = "000"
    for line in r.stdout.split("\n"):
        if line.startswith("HTTP_CODE:"):
            code = line.split(":")[1]
    return {"body": body, "code": code, "ms": elapsed, "cmd": " ".join(cmd[:6]) + "..."}
