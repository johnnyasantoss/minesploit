"""Mock Stratum V1 server for testing"""

import asyncio
import json
import random
import string
import sys
import time
from datetime import datetime
from typing import Any


class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"


def _log(
    level: str,
    client_id: str,
    message: str,
    data: bytes | None = None,
    direction: str = "",
):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if direction == "RECV":
        prefix = f"[ SERVER] [{timestamp}] [CONN:{client_id}] {Colors.MAGENTA}RECV{Colors.RESET}"
    elif direction == "SEND":
        prefix = f"[ SERVER] [{timestamp}] [CONN:{client_id}] {Colors.MAGENTA}SEND{Colors.RESET}"
    else:
        prefix = f"[ SERVER] [{timestamp}] [CONN:{client_id}]"

    if level == "INFO":
        level_color = Colors.BLUE
    elif level == "SUCCESS":
        level_color = Colors.GREEN
    elif level == "WARNING":
        level_color = Colors.YELLOW
    elif level == "ERROR":
        level_color = Colors.RED
    else:
        level_color = Colors.WHITE

    print(f"{prefix} {level_color}{level}{Colors.RESET}: {message}")
    sys.stdout.flush()


class StratumServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 3333, quiet: bool = False):
        self.host = host
        self.port = port
        self.quiet = quiet
        self._server: asyncio.Server | None = None
        self._running = False
        self._connections: dict[str, asyncio.StreamWriter] = {}
        self._subscriptions: dict[str, dict[str, Any]] = {}
        self._authorizations: dict[str, bool] = {}
        self._share_log: list[dict[str, Any]] = []
        self._current_job: dict[str, Any] = {}
        self._job_broadcast_task: asyncio.Task | None = None
        self._main_task: asyncio.Task | None = None

    def start(self) -> "StratumServer":
        asyncio.get_event_loop().run_until_complete(self._start_async())
        return self

    def stop(self) -> None:
        if self._running:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._stop_async())

    async def _start_async(self) -> None:
        self._server = await asyncio.start_server(
            self._handle_client,
            self.host,
            self.port,
        )
        self._running = True
        addr = self._server.sockets[0].getsockname()

        if not self.quiet:
            print(
                f"{Colors.BOLD}{Colors.GREEN}Stratum Server starting on {addr[0]}:{addr[1]}{Colors.RESET}"
            )
            print(f"{Colors.CYAN}Waiting for connections...{Colors.RESET}")
            sys.stdout.flush()

        self._job_broadcast_task = asyncio.create_task(self._broadcast_job())

        self._main_task = asyncio.create_task(self._server.serve_forever())

    async def _stop_async(self) -> None:
        self._running = False
        if self._job_broadcast_task:
            self._job_broadcast_task.cancel()
            try:
                await self._job_broadcast_task
            except asyncio.CancelledError:
                pass

        if not self.quiet:
            print(f"\n{Colors.YELLOW}Shutting down...{Colors.RESET}")

        for _client_id, writer in list(self._connections.items()):
            writer.close()
            await writer.wait_closed()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        if not self.quiet:
            print(f"{Colors.GREEN}Server stopped.{Colors.RESET}")
            print(f"{Colors.CYAN}Total shares received: {len(self._share_log)}{Colors.RESET}")

    async def __aenter__(self) -> "StratumServer":
        await self._start_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._stop_async()

    def _generate_job(self) -> dict[str, Any]:
        return {
            "job_id": "".join(random.choices(string.hexdigits.lower(), k=16)),
            "prev_hash": "".join(random.choices(string.hexdigits.lower(), k=64)),
            "coinb1": "".join(random.choices(string.hexdigits.lower(), k=64)),
            "coinb2": "".join(random.choices(string.hexdigits.lower(), k=64)),
            "merkle_branch": [],
            "version": "20000000",
            "nbits": "1a7fffff",
            "ntime": format(int(time.time()), "08x"),
            "clean_jobs": True,
        }

    async def _broadcast_job(self):
        while self._running:
            await asyncio.sleep(10)
            if not self._connections:
                continue

            self._current_job = self._generate_job()

            notification = {
                "id": None,
                "method": "mining.notify",
                "params": [
                    self._current_job["job_id"],
                    self._current_job["prev_hash"],
                    self._current_job["coinb1"],
                    self._current_job["coinb2"],
                    self._current_job["merkle_branch"],
                    self._current_job["version"],
                    self._current_job["nbits"],
                    self._current_job["ntime"],
                    self._current_job["clean_jobs"],
                ],
            }

            message = json.dumps(notification)
            data = message.encode("utf-8") + b"\n"

            for _client_id, writer in list(self._connections.items()):
                try:
                    writer.write(data)
                    await writer.drain()
                except Exception:
                    pass

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        client_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        peername = writer.get_extra_info("peername")

        self._connections[client_id] = writer
        if not self.quiet:
            _log(
                "INFO",
                client_id,
                f"{Colors.GREEN}New connection from {peername[0]}:{peername[1]}{Colors.RESET}",
            )

        buffer = b""

        try:
            while self._running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=30)
                except asyncio.TimeoutError:
                    continue

                if not data:
                    if not self.quiet:
                        _log("INFO", client_id, "Client disconnected (no data)")
                    break

                buffer += data

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue

                    message = line.decode("utf-8").strip()
                    response = await self._process_message(client_id, message)
                    if response:
                        response_data = response.encode("utf-8") + b"\n"
                        writer.write(response_data)
                        await writer.drain()

        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            if client_id in self._connections:
                del self._connections[client_id]
            if client_id in self._subscriptions:
                del self._subscriptions[client_id]
            if client_id in self._authorizations:
                del self._authorizations[client_id]
            writer.close()
            await writer.wait_closed()
            if not self.quiet:
                _log("INFO", client_id, "Connection closed")

    async def _process_message(
        self,
        client_id: str,
        message: str,
    ) -> str | None:
        result: Any = None
        try:
            msg = json.loads(message)
            method = msg.get("method")
            msg_id = msg.get("id")
            params = msg.get("params", [])

            if not self.quiet:
                _log("INFO", client_id, f"Method: {method}, ID: {msg_id}, Params: {params}")

            if method == "mining.subscribe":
                session_id = "".join(random.choices(string.hexdigits.lower(), k=16))
                extra_nonce_1 = "".join(random.choices(string.hexdigits.lower(), k=8))
                extra_nonce_2_length = 4

                self._subscriptions[client_id] = {
                    "session_id": session_id,
                    "extra_nonce_1": extra_nonce_1,
                    "extra_nonce_2_length": extra_nonce_2_length,
                }

                result = [
                    [
                        session_id,
                        [
                            extra_nonce_1,
                            extra_nonce_2_length,
                        ],
                    ],
                    None,
                ]

                if not self.quiet:
                    _log(
                        "SUCCESS",
                        client_id,
                        f"Subscribed! session_id={session_id}, extra_nonce_1={extra_nonce_1}",
                    )
                return json.dumps({"id": msg_id, "result": result})

            elif method == "mining.authorize":
                worker_name = params[0] if params else "unknown"

                self._authorizations[client_id] = True

                if not self.quiet:
                    _log("SUCCESS", client_id, f"Authorized worker: {worker_name}")
                return json.dumps({"id": msg_id, "result": True})

            elif method == "mining.submit":
                if client_id in self._authorizations and self._authorizations[client_id]:
                    if params:
                        share = {
                            "client_id": client_id,
                            "worker": params[0],
                            "job_id": params[1],
                            "extra_nonce_2": params[2],
                            "ntime": params[3],
                            "nonce": params[4],
                            "timestamp": datetime.now().isoformat(),
                        }
                        self._share_log.append(share)

                        if not self.quiet:
                            _log("SUCCESS", client_id, "SHARE RECEIVED:")
                            _log("INFO", client_id, f"  Worker: {share['worker']}")
                            _log("INFO", client_id, f"  Job ID: {share['job_id']}")

                    result = True
                else:
                    if not self.quiet:
                        _log("WARNING", client_id, "Submit from unauthorized client")
                    result = False

                return json.dumps({"id": msg_id, "result": result})

            elif method == "mining.get_transactions":
                if not self.quiet:
                    _log("INFO", client_id, "get_transactions requested")
                result = []
                return json.dumps({"id": msg_id, "result": result})

            else:
                if not self.quiet:
                    _log("WARNING", client_id, f"Unknown method: {method}")

        except json.JSONDecodeError:
            pass
        except Exception:
            pass

        return None

    def get_stats(self) -> dict[str, Any]:
        return {
            "connections": len(self._connections),
            "subscriptions": len(self._subscriptions),
            "authorizations": len(self._authorizations),
            "shares_submitted": len(self._share_log),
        }

    @property
    def share_log(self) -> list[dict[str, Any]]:
        return self._share_log

    @property
    def subscriptions(self) -> dict[str, dict[str, Any]]:
        return self._subscriptions

    @property
    def authorizations(self) -> dict[str, bool]:
        return self._authorizations

    def has_workers(self) -> bool:
        return len(self._authorizations) > 0
