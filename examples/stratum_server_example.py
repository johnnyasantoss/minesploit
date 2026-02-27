"""Stratum V1 Mining Server Example"""

import asyncio

from minesploit.protocols.stratum.server import Colors, StratumServer


async def main():
    print(f"{Colors.CYAN}=== RAII Pattern (context manager) ==={Colors.RESET}")
    async with StratumServer(host="127.0.0.1", port=3333) as server:
        print(f"{Colors.GREEN}Server started{Colors.RESET}")
        await asyncio.sleep(5)
        stats = server.get_stats()
        print(f"{Colors.BLUE}Stats: {stats}{Colors.RESET}")
    print(f"{Colors.YELLOW}Server stopped (auto-cleanup){Colors.RESET}")

    print(f"\n{Colors.CYAN}=== Fluent Pattern ==={Colors.RESET}")
    server = StratumServer(host="127.0.0.1", port=3334)
    server.start()
    print(f"{Colors.GREEN}Server started{Colors.RESET}")
    await asyncio.sleep(5)
    stats = server.get_stats()
    print(f"{Colors.BLUE}Stats: {stats}{Colors.RESET}")
    server.stop()
    print(f"{Colors.YELLOW}Server stopped{Colors.RESET}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
