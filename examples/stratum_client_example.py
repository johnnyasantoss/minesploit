"""Stratum V1 Mining Client Example with detailed logging"""

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


def log(level: str, message: str, data: bytes | None = None, direction: str = ""):
    """Colored logging with optional hex dump"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

    if direction == "SEND":
        prefix = f"[ CLIENT] [{timestamp}] {Colors.MAGENTA}>>> SEND{Colors.RESET}"
    elif direction == "RECV":
        prefix = f"[ CLIENT] [{timestamp}] {Colors.MAGENTA}<<< RECV{Colors.RESET}"
    else:
        prefix = f"[ CLIENT] [{timestamp}]"

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
        print(hexdump(data, prefix + " "))
    sys.stdout.flush()


class StratumClient:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3333,
        worker_name: str = "worker1",
        worker_password: str = "x",
    ):
        self.host = host
        self.port = port
        self.worker_name = worker_name
        self.worker_password = worker_password

        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

        self.connected = False
        self.subscribed = False
        self.authorized = False

        self.session_id: str | None = None
        self.extra_nonce_1: str | None = None
        self.extra_nonce_2_length: int = 0

        self.current_job: dict[str, Any] | None = None
        self.msg_id = 1

    async def connect(self) -> bool:
        """Connect to the Stratum server"""
        log("INFO", f"Connecting to {self.host}:{self.port}...")

        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host,
                self.port,
            )
            self.connected = True
            log("SUCCESS", f"Connected to {self.host}:{self.port}!")
            return True
        except Exception as e:
            log("ERROR", f"Connection failed: {e}")
            return False

    async def send_message(
        self, method: str, params: list | None = None, wait_response: bool = True
    ) -> dict | None:
        """Send a JSON-RPC message and return the response"""
        if not self.writer or not self.connected:
            log("ERROR", "Not connected")
            return None

        msg_id = self.msg_id
        self.msg_id += 1

        message: dict[str, Any] = {"id": msg_id, "method": method}
        if params is not None:
            message["params"] = params

        data = json.dumps(message).encode("utf-8") + b"\n"

        log("INFO", f"Sending {method}", data, "SEND")

        try:
            self.writer.write(data)
            await self.writer.drain()
        except Exception as e:
            log("ERROR", f"Failed to send: {e}")
            return None

        if not wait_response:
            return None

        response_data = await self.receive_response()
        if response_data:
            log("INFO", f"Received response for {method}", response_data, "RECV")
            try:
                return json.loads(response_data.decode("utf-8"))
            except json.JSONDecodeError as e:
                log("ERROR", f"Failed to parse response: {e}")

        return None

    async def receive_response(self, timeout: float = 10.0) -> bytes | None:
        """Receive a response from the server"""
        if not self.reader:
            return None

        try:
            data = await asyncio.wait_for(self.reader.readline(), timeout=timeout)
            return data if data else None
        except asyncio.TimeoutError:
            log("WARNING", "Response timeout")
            return None
        except Exception as e:
            log("ERROR", f"Receive error: {e}")
            return None

    async def subscribe(self) -> bool:
        """Send mining.subscribe request"""
        log("INFO", "Sending mining.subscribe...")

        params = [self.worker_name]
        response = await self.send_message("mining.subscribe", params)

        if response and "result" in response:
            result = response["result"]
            if result and result[0]:
                self.subscribed = True

                subscription_data = result[0]
                self.session_id = subscription_data[0]

                extra_nonce_info = subscription_data[1]
                self.extra_nonce_1 = extra_nonce_info[0]
                self.extra_nonce_2_length = extra_nonce_info[1]

                log(
                    "SUCCESS",
                    f"Subscribed! session_id={self.session_id}, extra_nonce_1={self.extra_nonce_1}",
                )
                return True

        log("ERROR", "Subscribe failed")
        return False

    async def authorize(self) -> bool:
        """Send mining.authorize request"""
        log("INFO", f"Authorizing worker: {self.worker_name}")

        params = [self.worker_name, self.worker_password]
        response = await self.send_message("mining.authorize", params)

        if response and "result" in response:
            self.authorized = bool(response["result"])
            if self.authorized:
                log("SUCCESS", f"Authorized as {self.worker_name}")
            else:
                log("ERROR", "Authorization failed")
            return self.authorized

        log("ERROR", "Authorization failed (no response)")
        return False

    async def poll_notifications(self, timeout: float = 0.5):
        """Poll for any pending notifications"""
        if not self.reader:
            return

        try:
            data = await asyncio.wait_for(self.reader.readline(), timeout=timeout)
            if not data:
                return

            message = data.decode("utf-8").strip()
            if not message:
                return

            try:
                msg = json.loads(message)
            except json.JSONDecodeError:
                return

            method = msg.get("method")

            if method == "mining.notify":
                params = msg.get("params", [])
                if params:
                    self.current_job = {
                        "job_id": params[0],
                        "prev_hash": params[1],
                        "coinb1": params[2],
                        "coinb2": params[3],
                        "merkle_branch": params[4],
                        "version": params[5],
                        "nbits": params[6],
                        "ntime": params[7],
                        "clean_jobs": params[8],
                    }

                    log("INFO", f"Received new job:")
                    log("INFO", f"  Job ID: {self.current_job['job_id']}")
                    log("INFO", f"  Prev Hash: {self.current_job['prev_hash'][:16]}...")
                    log("INFO", f"  Version: {self.current_job['version']}")
                    log("INFO", f"  NBits: {self.current_job['nbits']}")
                    log("INFO", f"  NTime: {self.current_job['ntime']}")
                    log("INFO", f"  Clean Jobs: {self.current_job['clean_jobs']}")

            elif method == "mining.set_difficulty":
                log("INFO", f"Set difficulty: {msg.get('params', [])}")

        except asyncio.TimeoutError:
            pass
        except Exception as e:
            log("ERROR", f"Poll error: {e}")

    async def submit_share(
        self,
        job_id: str,
        extra_nonce_2: str,
        ntime: str,
        nonce: str,
    ) -> bool:
        """Submit a share to the server"""
        log("INFO", f"Submitting share...")
        log("INFO", f"  Job ID: {job_id}")
        log("INFO", f"  ExtraNonce2: {extra_nonce_2}")
        log("INFO", f"  NTime: {ntime}")
        log("INFO", f"  Nonce: {nonce}")

        params = [
            self.worker_name,
            job_id,
            extra_nonce_2,
            ntime,
            nonce,
        ]

        await self.send_message("mining.submit", params, wait_response=False)

        response_data = await self.receive_response(timeout=2.0)
        if response_data:
            try:
                msg = json.loads(response_data.decode("utf-8"))
                if "result" in msg:
                    if msg["result"]:
                        log("SUCCESS", "Share accepted by server!")
                        return True
                    else:
                        log("WARNING", "Share rejected by server")
                        return False
            except:
                pass

        log("INFO", "Share submission sent")
        return True

    def generate_share(self) -> tuple[str, str, str, str]:
        """Generate random share data"""
        extra_nonce_2 = "".join(
            random.choices(string.hexdigits.lower(), k=self.extra_nonce_2_length * 2)
        )
        ntime = format(int(time.time()), "08x")
        nonce = "".join(random.choices(string.hexdigits.lower(), k=8))

        job_id = self.current_job["job_id"] if self.current_job else "0" * 16

        return job_id, extra_nonce_2, ntime, nonce

    async def close(self):
        """Close the connection"""
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()

        self.connected = False
        log("INFO", "Connection closed")


async def main():
    client = StratumClient(
        host="127.0.0.1",
        port=3333,
        worker_name="worker1",
        worker_password="x",
    )

    try:
        if not await client.connect():
            log("ERROR", "Failed to connect")
            return

        if not await client.subscribe():
            log("ERROR", "Failed to subscribe")
            await client.close()
            return

        if not await client.authorize():
            log("ERROR", "Failed to authorize")
            await client.close()
            return

        log("INFO", "Waiting for job broadcast...")
        wait_time = 12
        poll_interval = 1
        for _ in range(wait_time // poll_interval):
            await asyncio.sleep(poll_interval)
            await client.poll_notifications(timeout=0.1)
            if client.current_job:
                break

        share_count = 0
        while share_count < 10:
            if not client.current_job:
                log("WARNING", "No job received yet, waiting...")
                await asyncio.sleep(2)
                continue

            share_count += 1
            log("INFO", f"--- Submitting share #{share_count} ---")

            job_id, extra_nonce_2, ntime, nonce = client.generate_share()

            await client.submit_share(job_id, extra_nonce_2, ntime, nonce)

            await client.poll_notifications(timeout=0.5)

            await asyncio.sleep(3)

        log("INFO", f"Completed {share_count} share submissions")

    except KeyboardInterrupt:
        log("INFO", "Interrupted by user")
    finally:
        await client.close()

    log("INFO", "Client shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
