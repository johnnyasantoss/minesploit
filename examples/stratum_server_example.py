#!/usr/bin/env -S minesploit -s
"""Stratum V1 Mining Server Example"""

import asyncio

from minesploit.protocols.stratum.server import StratumServer


async def main():
    print("=== RAII Pattern (context manager) ===")
    async with StratumServer(host="127.0.0.1", port=3333, verbosity="debug") as server:
        print("Server started")
        await asyncio.sleep(5)
        stats = server.get_stats()
        print(f"Stats: {stats}")
    print("Server stopped (auto-cleanup)")

    print("\n=== Fluent Pattern ===")
    server = StratumServer(host="127.0.0.1", port=3334, verbosity="debug")
    server.start()
    print("Server started")
    await asyncio.sleep(5)
    stats = server.get_stats()
    print(f"Stats: {stats}")
    server.stop()
    print("Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
