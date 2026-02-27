"""Mock Stratum V1 server for testing"""

import asyncio
import json
import random
import string
from typing import Any


class StratumServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 3333):
        self.host = host
        self.port = port
        self.server: asyncio.Server | None = None
        self.running = False
        self.connections: list[asyncio.StreamWriter] = []
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self.authorizations: dict[str, bool] = {}
        self.share_log: list[dict[str, Any]] = []

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        writer.get_extra_info("peername")  # noqa: F841
        client_id = "".join(random.choices(string.ascii_letters, k=8))
        self.connections.append(writer)

        try:
            while self.running:
                data = await reader.read(4096)
                if not data:
                    break

                message = data.decode("utf-8").strip()
                if not message:
                    continue

                response = await self.process_message(client_id, message)
                if response:
                    writer.write(response.encode("utf-8") + b"\n")
                    await writer.drain()

        except asyncio.CancelledError:
            pass
        finally:
            if writer in self.connections:
                self.connections.remove(writer)
            writer.close()
            await writer.wait_closed()

    async def process_message(
        self,
        client_id: str,
        message: str,
    ) -> str | None:
        try:
            msg = json.loads(message)
            method = msg.get("method")
            msg_id = msg.get("id")

            if method == "mining.subscribe":
                session_id = "".join(random.choices(string.hexdigits.lower(), k=16))
                extra_nonce_1 = "".join(random.choices(string.hexdigits.lower(), k=8))
                self.subscriptions[client_id] = {
                    "session_id": session_id,
                    "extra_nonce_1": extra_nonce_1,
                    "extra_nonce_2_length": 4,
                }

                result = [
                    [
                        session_id,
                        [
                            extra_nonce_1,
                            4,
                        ],
                    ],
                    None,
                ]
                return json.dumps({"id": msg_id, "result": result})

            elif method == "mining.authorize":
                params = msg.get("params", [])
                params[0] if params else ""  # noqa: F841
                self.authorizations[client_id] = True

                result = True
                return json.dumps({"id": msg_id, "result": result})

            elif method == "mining.submit":
                if client_id in self.authorizations and self.authorizations[client_id]:
                    params = msg.get("params", [])
                    if params:
                        self.share_log.append(
                            {
                                "client_id": client_id,
                                "worker": params[0],
                                "job_id": params[1],
                                "extra_nonce_2": params[2],
                                "ntime": params[3],
                                "nonce": params[4],
                            }
                        )
                result = True
                return json.dumps({"id": msg_id, "result": result})

            elif method == "mining.get_transactions":
                result = []
                return json.dumps({"id": msg_id, "result": result})

        except json.JSONDecodeError:
            return None

        return None

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
        )
        self.running = True
        addr = self.server.sockets[0].getsockname()
        print(f"Stratum server running on {addr}")

    async def stop(self):
        self.running = False
        for writer in self.connections:
            writer.close()
            await writer.wait_closed()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

    def get_stats(self) -> dict[str, Any]:
        return {
            "connections": len(self.connections),
            "subscriptions": len(self.subscriptions),
            "authorizations": len(self.authorizations),
            "shares_submitted": len(self.share_log),
        }
