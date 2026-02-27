"""Stratum V1 Mining Server Example with detailed logging"""

import asyncio
import json
import random
import signal
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


def hexdump(data: bytes, prefix: str = "        ") -> str:
    """Create a hexdump-style output of bytes"""
    lines = []
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        hex_part = hex_part.ljust(48)
        lines.append(f"{prefix}{hex_part} | {ascii_part}")
    return "\n".join(lines)


def log(level: str, client_id: str, message: str, data: bytes | None = None, direction: str = ""):
    """Colored logging with optional hex dump"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if direction == "RECV":
        color = Colors.CYAN
        prefix = f"[ SERVER] [{timestamp}] [CONN:{client_id}] {Colors.MAGENTA}RECV{Colors.RESET}"
    elif direction == "SEND":
        color = Colors.CYAN
        prefix = f"[ SERVER] [{timestamp}] [CONN:{client_id}] {Colors.MAGENTA}SEND{Colors.RESET}"
    else:
        color = Colors.CYAN
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

    if data:
        try:
            msg_str = data.decode("utf-8").strip()
            print(f"{prefix} {msg_str}")
        except:
            print(hexdump(data, prefix + " "))
    sys.stdout.flush()


class StratumServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 3333):
        self.host = host
        self.port = port
        self.server: asyncio.Server | None = None
        self.running = False
        self.connections: dict[str, asyncio.StreamWriter] = {}
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self.authorizations: dict[str, bool] = {}
        self.share_log: list[dict[str, Any]] = []
        self.current_job: dict[str, Any] = {}
        self.job_broadcast_task: asyncio.Task | None = None

    def generate_job(self) -> dict[str, Any]:
        """Generate a fake mining job"""
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

    async def broadcast_job(self):
        """Periodically broadcast new mining jobs to all connected clients"""
        while self.running:
            await asyncio.sleep(10)
            if not self.connections:
                continue

            self.current_job = self.generate_job()

            notification = {
                "id": None,
                "method": "mining.notify",
                "params": [
                    self.current_job["job_id"],
                    self.current_job["prev_hash"],
                    self.current_job["coinb1"],
                    self.current_job["coinb2"],
                    self.current_job["merkle_branch"],
                    self.current_job["version"],
                    self.current_job["nbits"],
                    self.current_job["ntime"],
                    self.current_job["clean_jobs"],
                ],
            }

            message = json.dumps(notification)
            data = message.encode("utf-8") + b"\n"

            for client_id, writer in list(self.connections.items()):
                try:
                    log(
                        "INFO",
                        client_id,
                        f"Broadcasting job {self.current_job['job_id'][:8]}...",
                        data,
                        "SEND",
                    )
                    writer.write(data)
                    await writer.drain()
                except Exception as e:
                    log("ERROR", client_id, f"Failed to broadcast: {e}")

    async def handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        client_id = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        peername = writer.get_extra_info("peername")

        self.connections[client_id] = writer
        log(
            "INFO",
            client_id,
            f"{Colors.GREEN}New connection from {peername[0]}:{peername[1]}{Colors.RESET}",
        )

        buffer = b""

        try:
            while self.running:
                try:
                    data = await asyncio.wait_for(reader.read(4096), timeout=30)
                except asyncio.TimeoutError:
                    continue

                if not data:
                    log("INFO", client_id, "Client disconnected (no data)")
                    break

                buffer += data

                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    if not line.strip():
                        continue

                    message = line.decode("utf-8").strip()
                    log("INFO", client_id, f"Raw message received", line, "RECV")

                    response = await self.process_message(client_id, message)
                    if response:
                        response_data = response.encode("utf-8") + b"\n"
                        log("INFO", client_id, f"Sending response", response_data, "SEND")
                        writer.write(response_data)
                        await writer.drain()

        except asyncio.CancelledError:
            log("INFO", client_id, "Connection cancelled")
        except Exception as e:
            log("ERROR", client_id, f"Error: {e}")
        finally:
            if client_id in self.connections:
                del self.connections[client_id]
            if client_id in self.subscriptions:
                del self.subscriptions[client_id]
            if client_id in self.authorizations:
                del self.authorizations[client_id]
            writer.close()
            await writer.wait_closed()
            log("INFO", client_id, "Connection closed")

    async def process_message(
        self,
        client_id: str,
        message: str,
    ) -> str | None:
        try:
            msg = json.loads(message)
            method = msg.get("method")
            msg_id = msg.get("id")
            params = msg.get("params", [])

            log("INFO", client_id, f"Method: {method}, ID: {msg_id}, Params: {params}")

            if method == "mining.subscribe":
                session_id = "".join(random.choices(string.hexdigits.lower(), k=16))
                extra_nonce_1 = "".join(random.choices(string.hexdigits.lower(), k=8))
                extra_nonce_2_length = 4

                self.subscriptions[client_id] = {
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

                log(
                    "SUCCESS",
                    client_id,
                    f"Subscribed! session_id={session_id}, extra_nonce_1={extra_nonce_1}",
                )
                return json.dumps({"id": msg_id, "result": result})

            elif method == "mining.authorize":
                worker_name = params[0] if params else "unknown"
                worker_password = params[1] if len(params) > 1 else ""

                self.authorizations[client_id] = True

                log("SUCCESS", client_id, f"Authorized worker: {worker_name}")
                return json.dumps({"id": msg_id, "result": True})

            elif method == "mining.submit":
                if client_id in self.authorizations and self.authorizations[client_id]:
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
                        self.share_log.append(share)

                        log("SUCCESS", client_id, f"SHARE RECEIVED:")
                        log("INFO", client_id, f"  Worker: {share['worker']}")
                        log("INFO", client_id, f"  Job ID: {share['job_id']}")
                        log("INFO", client_id, f"  ExtraNonce2: {share['extra_nonce_2']}")
                        log("INFO", client_id, f"  NTime: {share['ntime']}")
                        log("INFO", client_id, f"  Nonce: {share['nonce']}")

                    result = True
                else:
                    log("WARNING", client_id, "Submit from unauthorized client")
                    result = False

                return json.dumps({"id": msg_id, "result": result})

            elif method == "mining.get_transactions":
                log("INFO", client_id, "get_transactions requested")
                result = []
                return json.dumps({"id": msg_id, "result": result})

            else:
                log("WARNING", client_id, f"Unknown method: {method}")

        except json.JSONDecodeError as e:
            log("ERROR", client_id, f"JSON decode error: {e}")
        except Exception as e:
            log("ERROR", client_id, f"Error processing message: {e}")

        return None

    async def start(self):
        self.server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
        )
        self.running = True
        addr = self.server.sockets[0].getsockname()
        print(
            f"{Colors.BOLD}{Colors.GREEN}Stratum Server starting on {addr[0]}:{addr[1]}{Colors.RESET}"
        )
        print(f"{Colors.CYAN}Waiting for connections...{Colors.RESET}")
        sys.stdout.flush()

        self.job_broadcast_task = asyncio.create_task(self.broadcast_job())

        async with self.server:
            await self.server.serve_forever()

    async def stop(self):
        self.running = False
        if self.job_broadcast_task:
            self.job_broadcast_task.cancel()
            try:
                await self.job_broadcast_task
            except asyncio.CancelledError:
                pass

        print(f"\n{Colors.YELLOW}Shutting down...{Colors.RESET}")

        for client_id, writer in list(self.connections.items()):
            writer.close()
            await writer.wait_closed()

        if self.server:
            self.server.close()
            await self.server.wait_closed()

        print(f"{Colors.GREEN}Server stopped.{Colors.RESET}")
        print(f"{Colors.CYAN}Total shares received: {len(self.share_log)}{Colors.RESET}")


async def main():
    server = StratumServer(host="127.0.0.1", port=3333)

    loop = asyncio.get_running_loop()

    def signal_handler():
        print(f"\n{Colors.YELLOW}Received signal, shutting down...{Colors.RESET}")
        asyncio.create_task(server.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await server.start()
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
