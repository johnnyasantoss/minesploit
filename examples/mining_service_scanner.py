#!/usr/bin/env -S minesploit -s
"""Scan for mining services"""

import socket

from minesploit.utils.scanner import MINING_PORTS, MiningServiceScanner


def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


host = get_lan_ip()
print(f"[*] Starting mining service scan on {host}")
print(f"[*] Scanning {len(MINING_PORTS)} ports: {list(MINING_PORTS.keys())}")

scanner = MiningServiceScanner(host)
results = scanner.scan()

open_count = 0
print(
    f"\n[*] Scan complete - found {sum(1 for r in results.values() if r['open'])} open services:\n"
)

for port, info in results.items():
    if info["open"]:
        open_count += 1
        print(f"[+] {port}/tcp - {info['service']}")

print(f"\n[*] Total open: {open_count}/{len(results)}")
