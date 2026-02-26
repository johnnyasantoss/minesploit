"""P2Pool scanner stub

References external implementations:
- https://github.com/p2pool/p2pool (Python - older)
- https://github.com/pool2win/p2pool-v2 (Rust - modern)
"""

from typing import Any


class P2PoolScanner:
    """P2Pool protocol scanner

    This is a stub. For full implementation, use external P2Pool:
    - https://github.com/p2pool/p2pool (original Python)
    - https://github.com/pool2win/p2pool-v2 (Rust v2)
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9333):
        self.host = host
        self.port = port

    async def scan(self) -> dict[str, Any]:
        raise NotImplementedError("Use external p2pool implementation")

    async def detect_version(self) -> str | None:
        raise NotImplementedError("Use external p2pool implementation")
