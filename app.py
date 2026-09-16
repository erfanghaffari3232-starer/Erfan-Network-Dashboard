from flask import Flask, jsonify, render_template
import ipaddress
import platform
import socket
import subprocess
import concurrent.futures

app = Flask(__name__)


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


def ping_host(ip):
    system = platform.system().lower()
    command = ["ping", "-n", "1", "-w", "700", ip] if system == "windows" else ["ping", "-c", "1", "-W", "1", ip]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=2)
        if result.returncode != 0:
            return None
        output = result.stdout
        import re
        match = re.search(r"(?:time[=<]\s*)([0-9.]+)\s*ms", output, re.I)
        return float(match.group(1)) if match else 0
    except (subprocess.SubprocessError, OSError):
        return None


def scan_network():
    local_ip = get_local_ip()
    try:
        network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
    except ValueError:
        return []

    addresses = [str(ip) for ip in network.hosts()]
    found = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(ping_host, ip): ip for ip in addresses}
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            try:
                ping = future.result()
            except Exception:
                ping = None
            if ping is not None:
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except (socket.herror, socket.gaierror):
                    hostname = "Unknown device"
                found.append({"ip": ip, "hostname": hostname, "ping": ping})

    found.sort(key=lambda item: tuple(int(x) for x in item["ip"].split(".")))
    return found


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/network")
def network_info():
    local_ip = get_local_ip()
    network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
    return jsonify({
        "local_ip": local_ip,
        "network": str(network),
        "hostname": socket.gethostname(),
        "platform": platform.system(),
    })


@app.route("/api/scan")
def scan():
    return jsonify({"devices": scan_network()})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
