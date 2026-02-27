#!/usr/bin/env -S minesploit -s
"""Stratum V1 Mining Client Example"""

import asyncio

from minesploit.protocols.stratum.client import StratumClient


async def main():
    client = StratumClient(
        host="127.0.0.1",
        port=3333,
        worker_name="worker1",
        worker_password="x",
        verbosity="debug",
    )

    try:
        if not await client.connect():
            print("Failed to connect")
            return

        if not await client.subscribe():
            print("Failed to subscribe")
            await client.close()
            return

        if not await client.authorize():
            print("Failed to authorize")
            await client.close()
            return

        print("Connected, subscribed, and authorized!")

        for _ in range(5):
            await asyncio.sleep(3)
            if client.current_job:
                print(f"Job received: {client.current_job['job_id']}")
            else:
                print("Waiting for job...")

        print("Completed test")

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        await client.close()

    print("Client shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
