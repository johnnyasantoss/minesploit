#!/usr/bin/env -S minesploit -s
"""Stratum V1 Mining Server Example"""

from minesploit.protocols.stratum.server import StratumServer

async with StratumServer(port=3333) as server:
    print("Server started")
    await asyncio.sleep(3)
    print(f"Stats: {server.get_stats()}")

print("Server stopped (auto-cleanup)")
