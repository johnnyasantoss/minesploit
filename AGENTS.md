# Minesploit - Bitcoin Mining Security Research Framework

## Project Overview

**Minesploit** is a security research framework for testing Bitcoin mining infrastructure. It is designed for white hat hackers, security researchers, and penetration testers who have explicit authorization to test mining systems.

**Purpose:** Help security professionals identify vulnerabilities in Bitcoin mining software, protocols, and infrastructure through systematic testing using publicly disclosed CVEs (Common Vulnerabilities and Exposures).

**Legal Notice:** This tool is intended for authorized security testing only. Users must have explicit written permission from the system owner before testing any target. Unauthorized access to computer systems is illegal.

---

## What Minesploit Is

### Legitimate Use Cases

1. **Security Auditing** - Internal security teams auditing their own mining infrastructure
2. **Vulnerability Research** - Researchers studying publicly disclosed vulnerabilities
3. **Penetration Testing** - Professional pentesters testing client mining systems
4. **Education** - Learning about mining protocol security in a controlled environment
5. **Defensive Testing** - Verifying patches and mitigations for known CVEs

### Comparison to Existing Tools

- **Metasploit** - General-purpose penetration testing framework; Minesploit specializes in Bitcoin/mining protocols
- **Nmap** - Network scanning; Minesploit focuses on mining-specific vulnerabilities
- **CVE Databases** - Provide vulnerability information; Minesploit provides working PoC implementations

---

## Architecture

### Two-Part System

1. **Framework** (`minesploit/`) - Python library of exploit modules
2. **REPL** (`repl/`) - Interactive Python shell for running exploits

### Directory Structure

```
minesploit/
├── AGENTS.md                 # This file
├── LICENSE                   # GNU GPL v3
├── pyproject.toml           # Python project config
├── README.md                # Quick start guide
├── minesploit/              # Framework core
│   ├── __init__.py
│   ├── framework.py         # Base Exploit, Scanner classes
│   ├── protocols/           # Protocol implementations
│   │   ├── stratum/
│   │   │   ├── client.py    # Stratum v1 client
│   │   │   ├── server.py    # Stratum v1 server mock
│   │   │   └── exploits/
│   │   ├── stratumv2/
│   │   └── p2pool/
│   ├── exploits/            # Exploit modules
│   │   ├── __init__.py
│   │   ├── cve_2013_stratum_duplicate_shares.py
│   │   ├── cve_2016_stratum_mass_duplicate.py
│   │   ├── cve_2018_cgminer_api_overflow.py
│   │   ├── cve_2018_cgminer_path_traversal.py
│   │   ├── cve_2024_blocktxn_dos.py
│   │   └── cve_2019_headers_oom.py
│   ├── database.py          # CVE/exploit registry
│   └── utils/
│       ├── networking.py    # TCP/SSL utilities
│       ├── crypto.py        # Bitcoin crypto helpers
│       └── parser.py        # Message parsing
└── repl/                    # REPL application
    ├── __init__.py
    ├── shell.py            # Main REPL loop
    ├── commands.py         # CLI commands
    └── completer.py        # Tab completion
```

---

## Exploit Module Structure

Each exploit module follows this pattern:

```python
from minesploit.framework import Exploit

class CVE_XXXX_XXXXXX(Exploit):
    """Exploit description and CVE details"""

    name = "CVE-XXXX-XXXXX: Description"
    cve = "CVE-XXXX-XXXXX"
    cvss_score = 7.5
    severity = "HIGH"
    affected_versions = "1.0 - 2.5"
    discovered_by = "Researcher Name"
    disclosure_date = "2024-01-15"

    def check(self, target):
        """Verify if target is vulnerable"""
        # Implementation
        return vulnerable, details

    def exploit(self, target):
        """Run exploit against target"""
        # Implementation
        return success, output

    def verify(self, target):
        """Verify exploit succeeded"""
        # Implementation
        return verified, evidence
```

---

## Available CVEs/Exploits

### Stratum Protocol Vulnerabilities

| CVE | Description | CVSS | Status |
|-----|-------------|------|--------|
| N/A (2013) | Stratum mining pool duplicate shares | 7.5 | Implemented |
| N/A (2016) | Mass duplicate shares exploit | 6.5 | Implemented |
| - | Stratum v1 subscription fuzzing | 5.0 | Planned |

### Bitcoin Core Node Vulnerabilities

| CVE | Description | CVSS | Status |
|-----|-------------|------|--------|
| CVE-2024-35202 | blocktxn message assertion DoS | 7.5 | Planned |
| CVE-2019-25220 | Headers OOM (memory exhaustion) | 7.0 | Planned |
| CVE-2024-52916 | Low-difficulty header spam DoS | 6.5 | Planned |

### Mining Software (cgminer/bfgminer)

| CVE | Description | CVSS | Status |
|-----|-------------|------|--------|
| CVE-2018-10058 | Remote API buffer overflow | 9.8 | Planned |
| CVE-2018-10057 | Remote API path traversal | 7.5 | Planned |

### P2Pool / Decentralized Mining

| CVE | Description | CVSS | Status |
|-----|-------------|------|--------|
| - | P2Pool protocol fuzzing vectors | 5.0 | Planned |

---

## Using the Framework

### As a Python Library

```python
from minesploit import Minesploit
from minesploit.exploits import CVE_XXXX_XXXXXX

# Initialize framework
ms = Minesploit()

# List available exploits
ms.list_exploits()

# Run a specific exploit
exploit = CVE_XXXX_XXXXXX()
result = exploit.check(target="192.168.1.100", port=8333)
```

### Using the REPL

```bash
$ python -m minesploit.repl
minesploit> help
minesploit> list exploits
minesploit> use cve_2016_stratum_mass_duplicate
minesploit (cve_2016_stratum_mass_duplicate)> set RHOSTS 192.168.1.100
minesploit (cve_2016_stratum_mass_duplicate)> set RPORT 3333
minesploit (cve_2016_stratum_mass_duplicate)> check
minesploit (cve_2016_stratum_mass_duplicate)> run
minesploit (cve_2016_stratum_mass_duplicate)> exit
```

---

## Metasploit Integration

Minesploit is designed to work alongside Metasploit:

1. **Complementary Testing** - Use Metasploit for general vulnerabilities, Minesploit for mining-specific ones
2. **Output Compatibility** - Export results in formats compatible with Metasploit reports
3. **Future: MSGRPC** - Plan to add remote execution via Metasploit's RPC API

---

## Development Guidelines

### For Contributors

1. **Only public CVEs** - Only implement vulnerabilities with public disclosure
2. **No weaponization** - Exploits should demonstrate vulnerability, not provide malware
3. **Documentation** - Every exploit needs CVE reference, affected versions, usage examples
4. **Safe defaults** - `check()` methods should be safe; `exploit()` requires explicit confirmation

### Code Style

- Python 3.10+ with type hints
- Async-first for network operations (asyncio)
- Follow PEP 8 with 100-char line limit
- No comments unless explaining complex logic

### Testing

- Unit tests for framework utilities
- Integration tests with mock servers
- Always test against controlled targets

### Version Control

- **Atomic commits** - Each commit should contain a single, focused change
- **Single responsibility** - One feature, one fix, or one refactor per commit
- **Commit message format**: `{type}: {short description}` where type is `feat`, `fix`, `docs`, `refactor`, `test`
- **Build before commit** - Run lint/typecheck: `ruff check . && mypy minesploit/`
- **Never commit broken code** - All tests should pass before committing

---

## Security Considerations

1. **Authorization Required** - Never use against systems you don't own
2. **Safe Scanning** - Default to `check()` mode before `exploit()`
3. **Logging** - All actions should be logged for audit trails
4. **No Persistence** - Exploits should not install backdoors or maintain access
5. **Read-Only** - Prefer read-only assessments when possible

---

## References

- Bitcoin Core Security Advisories: https://bitcoincore.org/en/security-advisories/
- CVE Database: https://nvd.nist.gov/
- Stratum V2 Specification: https://braiins.com/stratum-v2
- Bitcoin Wiki CVE List: https://en.bitcoin.it/wiki/Common_Vulnerabilities_and_Exposures

---

## License

GNU General Public License v3.0 - See LICENSE file for details.