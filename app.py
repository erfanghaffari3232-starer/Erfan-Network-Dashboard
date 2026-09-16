from flask import Flask, jsonify, render_template, request
import ipaddress
import platform
import socket
import subprocess
import concurrent.futures
from datetime import datetime

app = Flask(__name__)


def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("1.1.1.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def ping(ip):
    windows = platform.system().lower() == "windows"
    cmd = ["ping", "-n", "1", "-w", "600", ip] if windows else ["ping", "-c", "1", "-W", "1", ip]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
        if p.returncode:
            return None
        import re
        m = re.search(r"(?:time[=<]\s*)([0-9.]+)\s*ms", p.stdout, re.I)
        return float(m.group(1)) if m else 0
    except (OSError, subprocess.SubprocessError):
        return None


def scan_network():
    ip = local_ip()
    net = ipaddress.ip_network(f"{ip}/24", strict=False)
    hosts = [str(x) for x in net.hosts()]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as pool:
        jobs = {pool.submit(ping, host): host for host in hosts}
        for job in concurrent.futures.as_completed(jobs):
            host = jobs[job]
            latency = job.result()
            if latency is None:
                continue
            try:
                name = socket.gethostbyaddr(host)[0]
            except (socket.herror, socket.gaierror):
                name = "Unknown device"
            results.append({"ip": host, "hostname": name, "ping": latency, "online": True})
    results.sort(key=lambda x: tuple(map(int, x["ip"].split("."))))
    return results


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/network")
def network():
    ip = local_ip()
    return jsonify({
        "local_ip": ip,
        "network": str(ipaddress.ip_network(f"{ip}/24", strict=False)),
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "checked_at": datetime.now().strftime("%H:%M:%S")
    })


@app.get("/api/scan")
def scan():
    return jsonify({"devices": scan_network()})


@app.post("/api/action")
def action():
    data = request.get_json(silent=True) or {}
    action_name = data.get("action")
    ip = data.get("ip", "")
    allowed = {"open-router", "ping", "copy-ip"}
    if action_name not in allowed:
        return jsonify({"ok": False, "message": "Action is not available in this version."}), 400
    if action_name == "open-router":
        return jsonify({"ok": True, "url": f"http://{ip}"})
    if action_name == "ping":
        result = ping(ip)
        return jsonify({"ok": result is not None, "ping": result})
    return jsonify({"ok": True, "ip": ip})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
