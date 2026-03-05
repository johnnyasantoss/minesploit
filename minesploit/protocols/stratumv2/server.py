"""Mock Stratum V2 server for testing"""

import asyncio
import random
import string
from typing import Any

from minesploit.utils.logger import Logger


class StratumV2Server:
    def __init__(
        self, host: str = "0.0.0.0", port: int = 34254, verbosity: str = "info"
    ):
        self.host = host
        self.port = port
        self._logger = Logger(name="SV2_SERVER", verbosity=verbosity)
        self._server: asyncio.Server | None = None
        self._running = False
        self._connections: dict[str, asyncio.StreamWriter] = {}
        self._shares: list[dict[str, Any]] = []
        self._current_job: dict[str, Any] = {}
        self._job_broadcast_task: asyncio.Task | None = None

    def start(self) -> "StratumV2Server":
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()

        if loop.is_running():
            asyncio.create_task(self._start_async())
        else:
            loop.run_until_complete(self._start_async())
        return self

    def stop(self) -> None:
        if self._running:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()

            if loop.is_running():
                asyncio.create_task(self._stop_async())
            else:
                loop.run_until_complete(self._stop_async())

    async def _start_async(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port,
        )
        self._running = True
        addr = self._server.sockets[0].getsockname()

        self._logger.success(f"Stratum V2 Server starting on {addr[0]}:{addr[1]}")
        self._logger.info("Waiting for connections...")

        self._job_broadcast_task = asyncio.create_task(self._broadcast_job())

    async def _stop_async(self) -> None:
        self._running = False
        if self._job_broadcast_task:
            self._job_broadcast_task.cancel()
            try:
                await self._job_broadcast_task
            except asyncio.CancelledError:
                pass

        self._logger.warning("Shutting down...")

        for _client_id, writer in list(self._connections.items()):
            writer.close()
            await writer.wait_closed()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        self._logger.success("Server stopped.")
        self._logger.info(f"Total shares received: {len(self._shares)}")

    async def __aenter__(self) -> "StratumV2Server":
        await self._start_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._stop_async()

    async def _broadcast_job(self):
        while self._running:
            await asyncio.sleep(10)
            if not self._connections:
                continue
            self._current_job = self._generate_job()

    def _generate_job(self) -> dict[str, Any]:
        return {
            "job_id": "".join(random.choices(string.hexdigits.lower(), k=16)),
            "prev_hash": "".join(random.choices(string.hexdigits.lower(), k=64)),
            "coinbase_prefix": "".join(random.choices(string.hexdigits.lower(), k=20)),
            "coinbase_suffix": "".join(random.choices(string.hexdigits.lower(), k=20)),
            "merkle_branch": [],
            "version": "20000000",
            "ntime": "00000000",
            "target": "".join(random.choices(string.hexdigits.lower(), k=64)),
        }

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        client_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        peername = writer.get_extra_info("peername")

        self._connections[client_id] = writer
        self._logger.info(f"New connection from {peername[0]}:{peername[1]}")

        try:
            while self._running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=30)
                except asyncio.TimeoutError:
                    continue

                if not data:
                    break

        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            if client_id in self._connections:
                del self._connections[client_id]
            writer.close()
            await writer.wait_closed()

    def get_stats(self) -> dict[str, Any]:
        return {
            "connections": len(self._connections),
            "shares_submitted": len(self._shares),
        }

    @property
    def shares(self) -> list[dict[str, Any]]:
        return self._shares

    def has_workers(self) -> bool:
        return len(self._connections) > 0

    def get_config(self) -> dict:
        return {"host": "localhost", "port": self.port}
