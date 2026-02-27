"""Stratum V2 client stub

References external implementation: https://github.com/stratumv2/stratumv2
For production use, integrate with the reference implementation.
"""

from typing import Any

from minesploit.protocols.mining import MiningClient


class StratumV2Client(MiningClient):
    """Stratum V2 protocol client

    This is a stub. For full implementation, use:
    - https://github.com/stratumv2/stratumv2 (Python)
    - https://github.com/braiins/braiins (Rust reference)
    """

    def __init__(
        self, host: str, port: int = 3334, worker_name: str = "", worker_password: str = ""
    ):
        self.host = host
        self.port = port
        self.worker_name = worker_name
        self.worker_password = worker_password

    @property
    def version(self) -> str:
        return "v2"

    @property
    def current_job(self) -> dict[str, Any] | None:
        raise NotImplementedError("Use external stratumv2 implementation")

    @property
    def authorized(self) -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")

    @property
    def subscribed(self) -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")

    @property
    def session_id(self) -> str | None:
        raise NotImplementedError("Use external stratumv2 implementation")

    async def connect(self) -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")

    async def subscribe(self) -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")

    async def authorize(self, worker_name: str = "", worker_password: str = "") -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")

    async def submit(
        self,
        job_id: str,
        extra_nonce_2: str,
        ntime: str,
        nonce: str,
    ) -> bool:
        raise NotImplementedError("Use external stratumv2 implementation")

    async def recv_message(self) -> dict[str, Any] | None:
        raise NotImplementedError("Use external stratumv2 implementation")

    async def close(self) -> None:
        raise NotImplementedError("Use external stratumv2 implementation")
