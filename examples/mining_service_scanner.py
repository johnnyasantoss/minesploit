"""Mining Service Scanner Example

Scans common Bitcoin mining ports on a target and checks for Stratum
vulnerabilities using the CVE-2016 mass duplicate shares check.

Usage:
    python examples/mining_service_scanner.py 192.168.1.100
    python examples/mining_service_scanner.py 192.168.1.100 --ports 3333,3334,8332
    python examples/mining_service_scanner.py 192.168.1.100 --check
"""

import argparse
import asyncio

from minesploit.exploits.cve_2016_stratum_mass_duplicate import CVE_2016_STRATUM_MASS_DUPLICATE
from minesploit.utils.networking import scan_ports

MINING_PORTS = {
    3333: "Stratum V1 (BTC)",
    3334: "Stratum V1 (alt)",
    3335: "Stratum V1 (alt)",
    3336: "Stratum V1 (alt)",
    8332: "Bitcoin Core RPC",
    8333: "Bitcoin Core P2P",
    8334: "Bitcoin Core (testnet)",
    8335: "Bitcoin Core (testnet)",
    18443: "Bitcoin Core RegTest",
    18444: "Bitcoin Core RegTest",
    8555: "Stratum V2 (TLS)",
    8556: "Stratum V2",
}


async def scan_target(host: str, ports: list[int], run_check: bool = False):
    print(f"\n[~] Scanning {host} for mining services...\n")

    open_ports = await scan_ports(host, ports, timeout=3.0)

    discovered = []
    for port, is_open in open_ports.items():
        if is_open:
            service = MINING_PORTS.get(port, "Unknown")
            print(f"[+] {port}/tcp - {service}")
            discovered.append(port)

    if not discovered:
        print(f"[-] No mining services found on {host}")
        return

    print(f"\n[~] Found {len(discovered)} open port(s). Checking for vulnerabilities...\n")

    exploit = CVE_2016_STRATUM_MASS_DUPLICATE()
    stratus_ports = [p for p in discovered if p in (3333, 3334, 3335, 3336, 8555, 8556)]

    for port in stratus_ports:
        print(f"[*] Checking CVE-2016 mass duplicate on port {port}...")
        result = await exploit.check(target=host, port=port)

        if result.success:
            print(f"[!] VULNERABLE: {host}:{port} - {result.message}")
            if result.details:
                print(f"    Details: {result.details}")
        else:
            print(f"[*] NOT VULNERABLE: {host}:{port} - {result.message}")

    print(f"\n[~] Scan complete for {host}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan target for mining services and check for vulnerabilities"
    )
    parser.add_argument(
        "host",
        help="Target IP address or hostname",
    )
    parser.add_argument(
        "--ports",
        default="3333,3334,8332,8333,8555",
        help="Comma-separated ports to scan (default: 3333,3334,8332,8333,8555)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run vulnerability checks on discovered Stratum ports",
    )

    args = parser.parse_args()

    ports = [int(p.strip()) for p in args.ports.split(",")]

    asyncio.run(scan_target(args.host, ports, args.check))


if __name__ == "__main__":
    main()
