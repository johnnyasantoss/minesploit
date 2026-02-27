#!/usr/bin/env -S minesploit -s
"""Simple mining example - test stratum server hypothesis"""

from minesploit.protocols.stratum.client import StratumClient
from minesploit.protocols.stratum.server import StratumServer

pool = StratumServer().start()
await asyncio.sleep(0.5)

client = StratumClient(host="127.0.0.1", port=3333, worker_name="test.worker")
await client.connect()
await client.subscribe()

print(f"Stats: {pool.get_stats()}")

await client.close()
pool.stop()
