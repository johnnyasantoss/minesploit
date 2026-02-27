"""Mining Service Scanner"""

import asyncio

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


class MiningServiceScanner:
    def __init__(self, host: str, ports: list[int] | None = None):
        self.host = host
        self.ports = ports or list(MINING_PORTS.keys())

    def scan(self, timeout: float = 3.0) -> dict[int, dict]:
        open_ports = asyncio.run(scan_ports(self.host, self.ports, timeout=timeout))
        return {
            port: {"open": is_open, "service": MINING_PORTS.get(port, "Unknown")}
            for port, is_open in open_ports.items()
        }
