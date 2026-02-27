"""Example: CPU Mining on a Stratum V1 Pool

This example demonstrates how to use the CPUMiner utility to generate
real hashrate on a Stratum V1 pool. Useful for testing share-stealing
attacks and other CVEs that require actual mining activity.

Usage:
    python -m minesploit.examples.cpu_miner_example --host localhost --port 3333 --user worker.name

Requirements:
    - Docker must be running
    - Network access to the Stratum pool
"""

import argparse
import signal
import sys
import time

from minesploit.utils import CPUMiner, PoolConfig


def main():
    parser = argparse.ArgumentParser(description="CPU Mining on Stratum V1 Pool")
    parser.add_argument(
        "--host",
        default="localhost",
        help="Pool hostname (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=3333,
        help="Pool port (default: 3333)",
    )
    parser.add_argument(
        "--user",
        required=True,
        help="Worker username (e.g., address.worker)",
    )
    parser.add_argument(
        "--password",
        default="x",
        help="Worker password (default: x)",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=2,
        help="Number of CPU threads (default: 2)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Mining duration in seconds (default: 60)",
    )

    args = parser.parse_args()

    pool = PoolConfig(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
    )

    print(f"[*] Starting CPU miner with {args.threads} threads")
    print(f"[*] Pool: {args.host}:{args.port}")
    print(f"[*] User: {args.user}")
    print(f"[*] Duration: {args.duration} seconds")
    print()

    running = True

    def signal_handler(sig, frame):
        nonlocal running
        print("\n[*] Shutting down...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        with CPUMiner(threads=args.threads) as miner:
            miner.mine_at(pool)

            print("[*] Miner started, waiting for stats...\n")

            start_time = time.time()
            while running and (time.time() - start_time) < args.duration:
                stats = miner.get_stats()

                elapsed = int(time.time() - start_time)
                print(
                    f"[{elapsed:3d}s] "
                    f"Hashrate: {stats.get('hashrate_khs', 0):>8.2f} kH/s | "
                    f"Accepted: {stats.get('accepted', 0):>4} | "
                    f"Rejected: {stats.get('rejected', 0):>4}"
                )

                time.sleep(5)

            print("\n[*] Final stats:")
            final_stats = miner.get_stats()
            print(f"    Hashrate: {final_stats.get('hashrate_khs', 0):.2f} kH/s")
            print(f"    Accepted: {final_stats.get('accepted', 0)}")
            print(f"    Rejected: {final_stats.get('rejected', 0)}")

    except KeyboardInterrupt:
        print("\n[*] Interrupted")
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

    print("[*] Done")


if __name__ == "__main__":
    main()
