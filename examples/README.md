# Minesploit Examples

This directory contains example scripts demonstrating how to use the Minesploit framework for Bitcoin mining security research.

## Running Examples

All examples can be executed directly:

```bash
# Direct execution (requires executable permission)
chmod +x examples/mining_service_scanner.py
./examples/mining_service_scanner.py

# Or via the minesploit command
minesploit -s examples/mining_service_scanner.py

# Or via Python
python examples/mining_service_scanner.py
```

## Example Categories

### Basic Usage
- `mining_example.py` - Simple CPU mining test with local Stratum server
- `mining_service_scanner.py` - Scan for mining services on a target

### Stratum Protocol
- `stratum_client_example.py` - Basic Stratum V1 client implementation
- `stratum_server_example.py` - Stratum V1 server with RAII and fluent patterns
- `stratum_share_validator.py` - Validate mining shares using crypto utilities
- `stratum_logger.py` - Intercept and log Stratum protocol messages

### Security Testing
- `stratum_steal_shares_proxy.py` - Proxy demonstrating share theft vulnerabilities

## Writing New Examples

Follow these guidelines when creating new examples:

### 1. Shebang Header

Every example must start with:
```python
#!/usr/bin/env -S minesploit -s
"""Brief description of what this example does."""
```

### 2. No `if __name__ == "__main__"` Block

Examples run directly through the minesploit REPL. Do not include:
```python
if __name__ == "__main__":
    main()
```

### 3. Use RAII or Fluent Patterns

#### RAII Pattern (Preferred for servers/proxies)
```python
from minesploit.protocols.stratum.server import StratumServer

async with StratumServer(host="127.0.0.1", port=3333) as server:
    # Server auto-starts and auto-cleans
    await asyncio.sleep(5)
    stats = server.get_stats()
# Server auto-stops here
```

#### Fluent Pattern (For async utilities)
```python
from minesploit.protocols.stratum.client import StratumClient

client = StratumClient(host="127.0.0.1", port=3333, worker_name="test")
await client.connect()
await client.subscribe()
await client.authorize()
# ... do work ...
await client.close()
```

### 4. Hypothesis-First Design

Keep examples minimal and focused on testing a specific hypothesis:

```python
from minesploit.utils import MiningServiceScanner

scanner = MiningServiceScanner("192.168.1.100")
results = scanner.scan()

for port, info in results.items():
    if info["open"]:
        print(f"[+] {port} - {info['service']}")
```

### 5. Document Usage

Include docstrings explaining what the example does and how to use it:

```python
#!/usr/bin/env -S minesploit -s
"""Example Description

This example demonstrates X. It requires:
- A running Stratum server on 127.0.0.1:3333
- At least 2 CPU cores for mining

Usage:
    ./example.py              # Direct execution
    minesploit -s example.py  # Via REPL
    python example.py         # Via Python
"""
```

### 6. Error Handling

Use try/finally for cleanup:

```python
client = StratumClient(...)
try:
    await client.connect()
    # ... work ...
finally:
    await client.close()
```

Or use context managers which handle cleanup automatically:

```python
async with StratumServer() as server:
    # Auto-cleanup on exit
    pass
```

### 7. Async Examples

For async code, you don't need `asyncio.run()`:

```python
async def main():
    # Your async code here
    pass

# Just call main() directly
main()
```

## Template

```python
#!/usr/bin/env -S minesploit -s
"""Description of this example.

What it does:
- Point 1
- Point 2

Requirements:
- Requirement 1
- Requirement 2

Usage:
    ./example.py              # Direct execution
    minesploit -s example.py  # Via REPL
"""

from minesploit.utils import SomeUtility

# Setup
utility = SomeUtility(...)

# Hypothesis test
result = utility.do_something()
assert result, "Expected result not obtained"

print(f"Success: {result}")
```

## Testing Examples

Before committing a new example, verify it runs:

```bash
# Test via minesploit
minesploit -s examples/your_example.py

# Or make executable and run directly
chmod +x examples/your_example.py
./examples/your_example.py
```

## Contributing

1. Follow the patterns in `mining_service_scanner.py` and `mining_example.py`
2. Keep examples under 50 lines when possible
3. Focus on a single hypothesis or use case
4. Document any prerequisites
5. Test before committing
