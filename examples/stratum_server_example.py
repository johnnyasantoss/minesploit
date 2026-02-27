"""Stratum V1 Mining Server Example - now uses minesploit stratum server"""

import asyncio
import signal

from minesploit.protocols.stratum.server import Colors, StratumServer


async def main():
    server = StratumServer(host="127.0.0.1", port=3333)

    loop = asyncio.get_running_loop()

    def signal_handler():
        print(f"\n{Colors.YELLOW}Received signal, shutting down...{Colors.RESET}")
        asyncio.create_task(server.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await server.start()
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()

    print(f"\n{Colors.CYAN}Final stats: {server.get_stats()}{Colors.RESET}")

    if server.share_log:
        print(f"\n{Colors.CYAN}Share log (last 5):{Colors.RESET}")
        for share in server.share_log[-5:]:
            print(f"  {share['timestamp']} - Worker: {share['worker']}, Job: {share['job_id']}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
