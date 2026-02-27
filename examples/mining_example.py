#!/usr/bin/env -S minesploit -s
"""Simple mining example - test stratum server hypothesis"""

import asyncio

from minesploit.protocols.stratum.client import StratumClient
from minesploit.protocols.stratum.server import StratumServer


async def main():
    pool = StratumServer(verbosity="debug").start()
    await asyncio.sleep(0.5)
    client = StratumClient(
        host="127.0.0.1", port=3333, worker_name="test.worker", verbosity="debug"
    )
    await client.connect()
    await client.subscribe()
    print(f"Stats: {pool.get_stats()}")
    await client.close()
    pool.stop()


asyncio.run(main())
