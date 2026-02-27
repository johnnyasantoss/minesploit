#!/usr/bin/env -S minesploit -s
"""Simple mining example - test stratum server hypothesis"""

import asyncio

from minesploit.protocols.stratum.client import StratumClient


async def test():
    from minesploit.protocols.stratum.server import StratumServer

    pool = StratumServer(verbosity="error").start()
    await asyncio.sleep(0.5)

    client = StratumClient(
        host="127.0.0.1", port=3333, worker_name="test.worker", verbosity="error"
    )
    await client.connect()
    await client.subscribe()
    print(f"Stats: {pool.get_stats()}")
    await client.close()
    pool.stop()


asyncio.run(test())
