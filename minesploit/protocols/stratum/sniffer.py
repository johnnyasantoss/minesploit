"""Stratum V1 Sniffer for intercepting and logging mining protocol messages"""

import json
from datetime import datetime
from pathlib import Path
from typing import IO, Any

from minesploit.protocols.stratum.proxy import StratumProxy


class StratumSniffer(StratumProxy):
    def __init__(
        self,
        listen_host: str = "127.0.0.1",
        listen_port: int = 3334,
        upstream_host: str = "127.0.0.1",
        upstream_port: int = 3333,
        upstream_user: str = "proxy_worker",
        upstream_password: str = "x",
        steal_ratio: float = 0.0,
        output_file: str | Path | None = None,
        verbosity: str = "info",
    ):
        super().__init__(
            listen_host=listen_host,
            listen_port=listen_port,
            upstream_host=upstream_host,
            upstream_port=upstream_port,
            upstream_user=upstream_user,
            upstream_password=upstream_password,
            steal_ratio=steal_ratio,
            verbosity=verbosity,
        )

        self.output_file = Path(output_file) if output_file else None
        self._log_file: IO[str] | None = None
        self._messages: list[dict[str, Any]] = []

        self._logger.name = "SNIFFER"

        self.on_miner_message(self._handle_miner_message)
        self.on_pool_message(self._handle_pool_message)

    async def _start_async(self) -> None:
        self._open_log_file()
        await super()._start_async()
        if self.output_file:
            self._logger.info(f"Logging to {self.output_file}")

    async def _stop_async(self) -> None:
        await super()._stop_async()
        self._close_log_file()
        self._logger.info(f"Stopped. Total messages: {len(self._messages)}")

    def _open_log_file(self) -> None:
        if self.output_file:
            self._log_file = open(self.output_file, "a", encoding="utf-8")

    def _close_log_file(self) -> None:
        if self._log_file:
            self._log_file.close()
            self._log_file = None

    def _log_message(self, source: str, message: dict) -> None:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "message": message,
        }

        self._messages.append(log_entry)

        if self._log_file:
            self._log_file.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            self._log_file.flush()

    def _handle_miner_message(self, message: dict) -> dict | None:
        self._log_message("miner", message)
        return message

    def _handle_pool_message(self, message: dict) -> dict | None:
        self._log_message("pool", message)
        return message

    def get_messages(self) -> list[dict[str, Any]]:
        return self._messages

    def clear_messages(self) -> None:
        self._messages.clear()
