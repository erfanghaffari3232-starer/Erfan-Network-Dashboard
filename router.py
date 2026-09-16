import os
import socket
from urllib.parse import urlparse


def get_gateway():
    """Best-effort gateway discovery on Windows/Linux without storing credentials."""
    try:
        import subprocess
        out = subprocess.check_output(["route", "print"], text=True, errors="ignore")
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0] == "0.0.0.0" and parts[1] == "0.0.0.0":
                return parts[2]
    except Exception:
        pass
    return os.getenv("ERFAN_GATEWAY", "192.168.1.1")


def router_info():
    gateway = get_gateway()
    candidates = [f"http://{gateway}", f"https://{gateway}"]
    reachable = []
    for url in candidates:
        try:
            host = urlparse(url).hostname
            with socket.create_connection((host, 80 if url.startswith('http:') else 443), timeout=0.5):
                reachable.append(url)
        except OSError:
            continue
    return {"gateway": gateway, "management_urls": reachable or [f"http://{gateway}"]}
