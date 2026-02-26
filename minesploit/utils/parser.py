"""Message parsers for mining protocols"""

import json
from typing import Any


class JSONRPCParser:
    @staticmethod
    def create_request(method: str, params: list[Any] | dict[str, Any], msg_id: int = 1) -> bytes:
        request = {
            "id": msg_id,
            "method": method,
            "params": params,
        }
        return json.dumps(request).encode("utf-8") + b"\n"

    @staticmethod
    def create_notification(method: str, params: list[Any] | dict[str, Any]) -> bytes:
        notification = {
            "method": method,
            "params": params,
        }
        return json.dumps(notification).encode("utf-8") + b"\n"

    @staticmethod
    def parse_response(data: bytes) -> dict[str, Any] | None:
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None


class StratumParser:
    @staticmethod
    def create_message(
        method: str,
        params: list[Any] | dict[str, Any] | None = None,
        msg_id: int | str | None = None,
    ) -> bytes:
        message: dict[str, Any] = {"method": method}
        if params is not None:
            message["params"] = params
        if msg_id is not None:
            message["id"] = msg_id
        return json.dumps(message).encode("utf-8") + b"\n"

    @staticmethod
    def parse_message(data: bytes) -> dict[str, Any] | None:
        try:
            return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    @staticmethod
    def mining_subscribe(
        worker_name: str,
        session_id: str | None = None,
    ) -> bytes:
        params = [worker_name]
        if session_id:
            params.append(session_id)
        return StratumParser.create_message("mining.subscribe", params)

    @staticmethod
    def mining_authorize(
        worker_name: str,
        worker_password: str,
    ) -> bytes:
        return StratumParser.create_message(
            "mining.authorize",
            [worker_name, worker_password],
        )

    @staticmethod
    def mining_submit(
        worker_name: str,
        job_id: str,
        extra_nonce_2: str,
        ntime: str,
        nonce: str,
    ) -> bytes:
        return StratumParser.create_message(
            "mining.submit",
            [worker_name, job_id, extra_nonce_2, ntime, nonce],
        )

    @staticmethod
    def mining_get_transactions(block_hash: str) -> bytes:
        return StratumParser.create_message(
            "mining.get_transactions",
            [block_hash],
        )


class BTCNodeParser:
    VERSION_MAGIC = {
        "mainnet": b"\xf9\xbe\xb4\xd9",
        "testnet": b"\x0b\x11\x09\x07",
        "signet": b"\xfa\xbf\xb5\xda",
        "regtest": b"\xfa\xbf\xb5\xda",
    }

    @staticmethod
    def parse_message(data: bytes) -> dict[str, Any] | None:
        if len(data) < 20:
            return None

        for network, magic in BTCNodeParser.VERSION_MAGIC.items():
            if data[:4] == magic:
                try:
                    command = data[4:16].rstrip(b"\x00").decode("ascii")
                    length = int.from_bytes(data[16:20], "little")
                    checksum = data[20:24]

                    if len(data) >= 24 + length:
                        payload = data[24 : 24 + length]
                        return {
                            "network": network,
                            "command": command,
                            "length": length,
                            "checksum": checksum.hex(),
                            "payload": payload.hex(),
                        }
                except (UnicodeDecodeError, ValueError):
                    pass

        return None
