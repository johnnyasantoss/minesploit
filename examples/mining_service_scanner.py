#!/usr/bin/env -S minesploit -s
"""Scan for mining services"""

from minesploit.utils import MiningServiceScanner

scanner = MiningServiceScanner("192.168.1.100")
results = scanner.scan()

for port, info in results.items():
    if info["open"]:
        print(f"[+] {port} - {info['service']}")
