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

- CVE-2013: Stratum Duplicate Shares
- CVE-2016: Stratum Mass Duplicate Shares
- CVE-2018-10058: cgminer API Buffer Overflow
- CVE-2018-10057: cgminer Path Traversal
- CVE-2024-35202: Bitcoin Core blocktxn DoS
- CVE-2019-25220: Bitcoin Core Headers OOM

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

## Legal Notice

This tool is for authorized security testing only. Users must have explicit
written permission from the system owner before testing any target.