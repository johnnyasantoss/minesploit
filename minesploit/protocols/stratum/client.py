"""Stratum V1 mining protocol client"""

from typing import Any

from minesploit.utils.networking import TCPClient
from minesploit.utils.parser import StratumParser


class StratumClient:
    def __init__(
        self,
        host: str,
        port: int,
        worker_name: str = "",
        worker_password: str = "",
    ):
        self.host = host
        self.port = port
        self.worker_name = worker_name
        self.worker_password = worker_password
        self.client: TCPClient | None = None
        self.authorized = False
        self.subscribed = False
        self.session_id: str | None = None
        self.extra_nonce_1: str | None = None
        self.extra_nonce_2_length: int = 0
        self.current_job: dict[str, Any] | None = None
        self.msg_id = 1

    async def connect(self) -> bool:
        self.client = TCPClient(self.host, self.port)
        connected = await self.client.connect()
        return connected

    async def subscribe(self) -> bool:
        if not self.client:
            return False

        msg = StratumParser.mining_subscribe(
            self.worker_name or "anonymous",
            self.session_id,
        )

        if await self.client.send(msg):
            response = await self.client.recv()
            if response:
                parsed = StratumParser.parse_message(response)
                if parsed and "result" in parsed:
                    result = parsed["result"]
                    if result and result[0]:
                        self.subscribed = True
                        self.session_id = result[0]
                        self.extra_nonce_1 = result[1][0]
                        self.extra_nonce_2_length = result[1][1]
                        return True

        return False

    async def authorize(self) -> bool:
        if not self.client:
            return False

        msg = StratumParser.mining_authorize(
            self.worker_name or "anonymous",
            self.worker_password or "x",
        )

        if await self.client.send(msg):
            response = await self.client.recv()
            if response:
                parsed = StratumParser.parse_message(response)
                if parsed and "result" in parsed:
                    self.authorized = bool(parsed["result"])

        return self.authorized

    async def submit(
        self,
        job_id: str,
        extra_nonce_2: str,
        ntime: str,
        nonce: str,
    ) -> bool:
        if not self.client or not self.authorized:
            return False

        msg = StratumParser.mining_submit(
            self.worker_name or "anonymous",
            job_id,
            extra_nonce_2,
            ntime,
            nonce,
        )

        if await self.client.send(msg):
            response = await self.client.recv()
            if response:
                parsed = StratumParser.parse_message(response)
                if parsed and "result" in parsed:
                    return parsed["result"] is True

        return False

    async def handle_notifications(self):
        if not self.client:
            return

        while True:
            data = await self.client.recv()
            if not data:
                break

            parsed = StratumParser.parse_message(data)
            if parsed:
                method = parsed.get("method")
                params = parsed.get("params", [])

                if method == "mining.notify":
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
                elif method == "mining.set_diff":
                    pass

    async def recv_message(self) -> dict[str, Any] | None:
        if not self.client:
            return None

        data = await self.client.recv()
        if data:
            return StratumParser.parse_message(data)
        return None

    async def close(self):
        if self.client:
            await self.client.close()
            self.client = None

    async def __aenter__(self):
        await self.connect()
        await self.subscribe()
        await self.authorize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
