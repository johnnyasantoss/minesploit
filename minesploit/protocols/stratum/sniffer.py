"""Stratum V1 Sniffer for intercepting and logging mining protocol messages"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class StratumSniffer:
    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 3334,
        upstream_host: str = "127.0.0.1",
        upstream_port: int = 3333,
        output_file: str | Path | None = None,
        quiet: bool = False,
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.output_file = Path(output_file) if output_file else None
        self.quiet = quiet

        self._server: asyncio.Server | None = None
        self._running = False
        self._log_file = None
        self._messages: list[dict[str, Any]] = []

    def start(self) -> "StratumSniffer":
        asyncio.get_event_loop().run_until_complete(self._start_async())
        return self

    def stop(self) -> None:
        if self._running:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._stop_async())

    async def _start_async(self) -> None:
        self._open_log_file()

        self._server = await asyncio.start_server(
            self._handle_client,
            self.listen_host,
            self.listen_port,
        )

        self._running = True
        addr = self._server.sockets[0].getsockname()

        if not self.quiet:
            print(f"[Sniffer] Listening on {addr[0]}:{addr[1]}")
            print(f"[Sniffer] Forwarding to {self.upstream_host}:{self.upstream_port}")
            if self.output_file:
                print(f"[Sniffer] Logging to {self.output_file}")

        await self._server.serve_forever()

    async def _stop_async(self) -> None:
        self._running = False
        self._close_log_file()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        if not self.quiet:
            print(f"[Sniffer] Stopped. Total messages: {len(self._messages)}")

    async def __aenter__(self) -> "StratumSniffer":
        await self._start_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._stop_async()

    def _open_log_file(self):
        if self.output_file:
            self._log_file = open(self.output_file, "a", encoding="utf-8")

    def _close_log_file(self):
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def _log_message(self, source: str, message: dict):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "message": message,
        }

        self._messages.append(log_entry)

        if self._log_file:
            self._log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            self._log_file.flush()

    async def _handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ):
        client_id = f"{client_writer.get_extra_info('peername')}"
        if not self.quiet:
            print(f"[Sniffer] Client connected: {client_id}")

        upstream_reader = None
        upstream_writer = None

        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(
                self.upstream_host,
                self.upstream_port,
            )
            if not self.quiet:
                print(f"[Sniffer] Connected to upstream {self.upstream_host}:{self.upstream_port}")

            await asyncio.gather(
                self._forward_miner_to_pool(client_reader, upstream_writer),
                self._forward_pool_to_miner(upstream_reader, client_writer),
            )

        except Exception:
            pass
        finally:
            if upstream_writer:
                upstream_writer.close()
                await upstream_writer.wait_closed()
            client_writer.close()
            await client_writer.wait_closed()
            if not self.quiet:
                print(f"[Sniffer] Client disconnected: {client_id}")

    async def _forward_miner_to_pool(
        self,
        client_reader: asyncio.StreamReader,
        upstream_writer: asyncio.StreamWriter,
    ):
        try:
            while self._running:
                data = await asyncio.wait_for(client_reader.read(4096), timeout=30)
                if not data:
                    break

                buffer = data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line.decode("utf-8"))
                        self._log_message("miner", message)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass

                    upstream_writer.write(line + b"\n")
                    await upstream_writer.drain()

        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        finally:
            upstream_writer.close()
            await upstream_writer.wait_closed()

    async def _forward_pool_to_miner(
        self,
        upstream_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ):
        try:
            while self._running:
                data = await asyncio.wait_for(upstream_reader.read(4096), timeout=30)
                if not data:
                    break

                buffer = data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line.decode("utf-8"))
                        self._log_message("pool", message)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        pass

                    client_writer.write(line + b"\n")
                    await client_writer.drain()

        except asyncio.TimeoutError:
            pass
        except Exception:
            pass
        finally:
            client_writer.close()
            await client_writer.wait_closed()

    def get_messages(self) -> list[dict[str, Any]]:
        return self._messages

    def clear_messages(self) -> None:
        self._messages.clear()
