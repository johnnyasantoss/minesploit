"""Stratum V1 Mining Proxy with Message Logging"""

import argparse
import asyncio
import json
import signal
from datetime import datetime
from pathlib import Path


class StratumProxy:
    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 3334,
        upstream_host: str = "127.0.0.1",
        upstream_port: int = 3333,
        output_file: str = "stratum_messages.jsonl",
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.output_file = Path(output_file)

        self.server: asyncio.Server | None = None
        self.running = False

        self._log_file = None

    def _open_log_file(self):
        """Open log file in append mode"""
        self._log_file = open(self.output_file, "a", encoding="utf-8")

    def _close_log_file(self):
        """Close log file"""
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def _log_message(self, source: str, message: dict):
        """Log a message to the output file"""
        if not self._log_file:
            return

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "message": message,
        }

        self._log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        self._log_file.flush()

    async def handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ):
        client_id = f"{client_writer.get_extra_info('peername')}"
        print(f"[PROXY] Client connected: {client_id}")

        upstream_reader = None
        upstream_writer = None

        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(
                self.upstream_host,
                self.upstream_port,
            )
            print(f"[PROXY] Connected to upstream {self.upstream_host}:{self.upstream_port}")

            async def forward_miner_to_pool():
                """Forward messages from miner to pool"""
                try:
                    while self.running:
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
                except Exception as e:
                    print(f"[PROXY] Error forwarding miner->pool: {e}")
                finally:
                    upstream_writer.close()
                    await upstream_writer.wait_closed()

            async def forward_pool_to_miner():
                """Forward messages from pool to miner"""
                try:
                    while self.running:
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
                except Exception as e:
                    print(f"[PROXY] Error forwarding pool->miner: {e}")
                finally:
                    client_writer.close()
                    await client_writer.wait_closed()

            await asyncio.gather(
                forward_miner_to_pool(),
                forward_pool_to_miner(),
            )

        except Exception as e:
            print(f"[PROXY] Client handler error: {e}")
        finally:
            if upstream_writer:
                upstream_writer.close()
                await upstream_writer.wait_closed()
            client_writer.close()
            await client_writer.wait_closed()
            print(f"[PROXY] Client disconnected: {client_id}")

    async def start(self):
        self._open_log_file()

        self.server = await asyncio.start_server(
            self.handle_client,
            self.listen_host,
            self.listen_port,
        )

        self.running = True
        addr = self.server.sockets[0].getsockname()
        print(f"[PROXY] Listening on {addr[0]}:{addr[1]}")
        print(f"[PROXY] Forwarding to {self.upstream_host}:{self.upstream_port}")
        print(f"[PROXY] Logging to {self.output_file}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        self.running = False
        self._close_log_file()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        print("[PROXY] Stopped")


async def main():
    parser = argparse.ArgumentParser(description="Stratum Mining Proxy with Message Logging")
    parser.add_argument(
        "--listen",
        default="127.0.0.1:3334",
        help="Proxy listen address (default: 127.0.0.1:3334)",
    )
    parser.add_argument(
        "--upstream",
        default="127.0.0.1:3333",
        help="Upstream Stratum server (default: 127.0.0.1:3333)",
    )
    parser.add_argument(
        "--output",
        default="stratum_messages.jsonl",
        help="Output log file (default: stratum_messages.jsonl)",
    )

    args = parser.parse_args()

    listen_host, listen_port = args.listen.rsplit(":", 1)
    listen_port = int(listen_port)

    upstream_host, upstream_port = args.upstream.rsplit(":", 1)
    upstream_port = int(upstream_port)

    proxy = StratumProxy(
        listen_host=listen_host,
        listen_port=listen_port,
        upstream_host=upstream_host,
        upstream_port=upstream_port,
        output_file=args.output,
    )

    loop = asyncio.get_running_loop()

    def signal_handler():
        print("\n[PROXY] Shutting down...")
        asyncio.create_task(proxy.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await proxy.start()
    except KeyboardInterrupt:
        pass
    finally:
        await proxy.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
