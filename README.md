# Minesploit

Bitcoin Mining Security Research Framework for white hat hackers and security researchers.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the REPL
python -m minesploit.repl
# or
minesploit
```

## Available Exploits

### Bitcoin Core Node Vulnerabilities
- CVE-2018-17144: Bitcoin Core Inflation (CRITICAL)
- CVE-2024-52914: Bitcoin Core Orphan Transaction DoS (HIGH)
- CVE-2017-18350: Bitcoin Core SOCKS Proxy Overflow (HIGH)
- CVE-2024-52912: Bitcoin Core Timestamp Overflow Netsplit
- CVE-2024-52915: Bitcoin Core INV Memory DoS
- CVE-2024-52913: Bitcoin Core Transaction Censorship
- CVE-2024-52921: Bitcoin Core Mutated Blocks Propagation
- CVE-2024-52920: Bitcoin Core GETDATA CPU DoS
- CVE-2024-52919: Bitcoin Core Addr Message Spam DoS
- CVE-2025-46598: Bitcoin Core CPU DoS from Transactions
- CVE-2025-54604: Bitcoin Core Disk Fill (Spoofed Connections)
- CVE-2025-54605: Bitcoin Core Disk Fill (Invalid Blocks)
- CVE-2015-20111: Bitcoin Core miniupnpc RCE
- CVE-2024-35202: Bitcoin Core blocktxn DoS

### Stratum Protocol Vulnerabilities
- CVE-2013: Stratum Duplicate Shares
- CVE-2016: Stratum Mass Duplicate Shares

### Mining Software
- CVE-2018-10058: cgminer API Buffer Overflow
- CVE-2018-10057: cgminer Path Traversal

## REPL Usage

```
minesploit> list exploits
minesploit> use cve_2016_stratum_mass_duplicate
minesploit (cve_2016_stratum_mass_duplicate)> set RHOSTS 192.168.1.100
minesploit (cve_2016_stratum_mass_duplicate)> set RPORT 3333
minesploit (cve_2016_stratum_mass_duplicate)> check
minesploit (cve_2016_stratum_mass_duplicate)> run
```

## As Python Library

```python
from minesploit.exploits import CVE_2016_STRATUM_MASS_DUPLICATE

exploit = CVE_2016_STRATUM_MASS_DUPLICATE()
result = await exploit.check("192.168.1.100", port=3333)
print(result.message)
```

## CPU Mining for Hypothesis Testing

Test share-stealing attacks and other CVEs that require real hashrate:

```python
from minesploit.protocols.stratum.server import StratumServer
from minesploit.utils.miner import CPUMiner

pool = StratumServer().start()
miner = CPUMiner(threads=2, pool=pool, user="test.worker").start()

assert pool.has_workers(), "No workers connected!"
print(f"Hashrate: {miner.get_stats()['hashrate_khs']} kH/s")

miner.stop()
pool.stop()
```

Run with: `python examples/mining_example.py`

## Legal Notice

This tool is for authorized security testing only. Users must have explicit
written permission from the system owner before testing any target.