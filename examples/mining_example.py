#!/usr/bin/env python
"""Simple CPU mining example - test hypothesis with minimal code"""

from minesploit.protocols.stratum.server import StratumServer
from minesploit.utils.miner import CPUMiner

pool = StratumServer().start()
miner = CPUMiner(threads=2, pool=pool, user="test.worker").start()

assert pool.has_workers(), "No workers connected!"
print(f"Hashrate: {miner.get_stats()['hashrate_khs']} kH/s")

miner.stop()
pool.stop()
