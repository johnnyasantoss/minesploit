"""Stratum V2 client stub

References external implementation: https://github.com/stratumv2/stratumv2
For production use, integrate with the reference implementation.
"""

from typing import Any


class StratumV2Client:
    """Stratum V2 protocol client

    This is a stub. For full implementation, use:
    - https://github.com/stratumv2/stratumv2 (Python)
    - https://github.com/braiins/braiins (Rust reference)
    """

    def __init__(self, host: str, port: int = 3334):
        self.host = host
        self.port = port

    async def connect(self) -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")

    async def send_message(self, message: dict[str, Any]) -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")
