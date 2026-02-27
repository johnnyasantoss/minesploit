from abc import ABC, abstractmethod
from typing import Any


class MiningClient(ABC):
    """Abstract base class for Stratum V1/V2 mining clients

    Provides a unified interface for interacting with different Stratum protocol
    versions. CVEs can accept this type and use client.version() to determine
    which protocol variant to use for equivalent attacks.
    """

    @property
    @abstractmethod
    def version(self) -> str:
        """Return protocol version: 'v1' or 'v2'"""
        ...

    @property
    @abstractmethod
    def current_job(self) -> dict[str, Any] | None:
        """Current mining job from the pool"""
        ...

    @property
    @abstractmethod
    def authorized(self) -> bool:
        """Whether the worker has been authorized"""
        ...

    @property
    @abstractmethod
    def subscribed(self) -> bool:
        """Whether the client has subscribed to mining notifications"""
        ...

    @property
    @abstractmethod
    def session_id(self) -> str | None:
        """Session identifier from subscription"""
        ...

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to mining server"""
        ...

    @abstractmethod
    async def subscribe(self) -> bool:
        """Subscribe to mining notifications"""
        ...

    @abstractmethod
    async def authorize(self, worker_name: str = "", worker_password: str = "") -> bool:
        """Authorize worker with the pool"""
        ...

    @abstractmethod
    async def submit(
        self,
        job_id: str,
        extra_nonce_2: str,
        ntime: str,
        nonce: str,
    ) -> bool:
        """Submit a share to the pool"""
        ...

    @abstractmethod
    async def recv_message(self) -> dict[str, Any] | None:
        """Receive and parse a message from the server"""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close the connection"""
        ...

    async def __aenter__(self) -> "MiningClient":
        await self.connect()
        await self.subscribe()
        await self.authorize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
