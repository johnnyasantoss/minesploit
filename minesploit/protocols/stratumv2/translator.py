"""Stratum-to-StratumV2 translator proxy using Docker"""

import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Any

from minesploit.protocols.stratum.client import StratumClient


@dataclass
class UpstreamConfig:
    """Configuration for SV2 upstream pool"""

    host: str
    port: int
    pub_key: str
    channel_kind: str = "Extended"


class StratumToStratumV2:
    """RAII wrapper for Stratum-to-StratumV2 translator proxy.

    Wraps the stratumv2/translator_sv2 Docker container to provide a fluent
    interface for testing attack hypotheses against mining infrastructure.

    Usage:
        async with StratumToStratumV2(
            upstream_host="pool.example.com",
            upstream_port=3333,
            upstream_pubkey="...",
        ) as translator:
            client = translator.connect_sv1_client("worker1")
            # Test attack hypotheses...
        # Docker container auto-cleaned on exit

    Or with fluent API:
        translator = StratumToStratumV2()
        translator.upstream_host("pool.example.com") \
                  .upstream_port(3333) \
                  .upstream_pubkey("...")

        async with translator:
            client = translator.connect_sv1_client()
    """

    IMAGE = "stratumv2/translator_sv2:v0.2.0"
    DEFAULT_DOWNSTREAM_PORT = 34255

    def __init__(
        self,
        upstream_host: str | None = None,
        upstream_port: int | None = None,
        upstream_pubkey: str | None = None,
        downstream_host: str = "0.0.0.0",
        downstream_port: int = DEFAULT_DOWNSTREAM_PORT,
        channel_kind: str = "Extended",
        min_extranonce2_size: int = 8,
        channel_nominal_hashrate: int = 1_000_000_000,
        channel_diff_update_interval: int = 60,
        downstream_share_per_minute: int = 10,
        min_individual_miner_hashrate: int = 1_000_000_000,
        max_supported_version: int = 2,
        min_supported_version: int = 2,
    ):
        self._upstream_host = upstream_host
        self._upstream_port = upstream_port
        self._upstream_pubkey = upstream_pubkey
        self._downstream_host = downstream_host
        self._downstream_port = downstream_port
        self._channel_kind = channel_kind
        self._min_extranonce2_size = min_extranonce2_size
        self._channel_nominal_hashrate = channel_nominal_hashrate
        self._channel_diff_update_interval = channel_diff_update_interval
        self._downstream_share_per_minute = downstream_share_per_minute
        self._min_individual_miner_hashrate = min_individual_miner_hashrate
        self._max_supported_version = max_supported_version
        self._min_supported_version = min_supported_version

        self._container_name: str | None = None
        self._running = False

    def upstream_host(self, host: str) -> "StratumToStratumV2":
        """Set upstream SV2 pool hostname (fluent)"""
        self._upstream_host = host
        return self

    def upstream_port(self, port: int) -> "StratumToStratumV2":
        """Set upstream SV2 pool port (fluent)"""
        self._upstream_port = port
        return self

    def upstream_pubkey(self, pubkey: str) -> "StratumToStratumV2":
        """Set upstream pool authority public key (fluent)"""
        self._upstream_pubkey = pubkey
        return self

    def downstream_host(self, host: str) -> "StratumToStratumV2":
        """Set downstream listen address for SV1 miners (fluent)"""
        self._downstream_host = host
        return self

    def downstream_port(self, port: int) -> "StratumToStratumV2":
        """Set downstream listen port for SV1 miners (fluent)"""
        self._downstream_port = port
        return self

    def channel_kind(self, kind: str) -> "StratumToStratumV2":
        """Set channel kind: 'Extended' or 'Group' (fluent)"""
        self._channel_kind = kind
        return self

    def min_extranonce2_size(self, size: int) -> "StratumToStratumV2":
        """Set minimum extranonce2 size (fluent)"""
        self._min_extranonce2_size = size
        return self

    def channel_nominal_hashrate(self, hashrate: int) -> "StratumToStratumV2":
        """Set channel nominal hashrate in H/s (fluent)"""
        self._channel_nominal_hashrate = hashrate
        return self

    def _validate_config(self) -> None:
        """Validate that required configuration is set"""
        if not self._upstream_host:
            raise ValueError("upstream_host is required")
        if not self._upstream_port:
            raise ValueError("upstream_port is required")
        if not self._upstream_pubkey:
            raise ValueError("upstream_pubkey is required")

    def _generate_config(self) -> str:
        """Generate TOML configuration for the translator"""
        return f"""[[upstreams]]
channel_kind = "{self._channel_kind}"
address = "{self._upstream_host}"
port = {self._upstream_port}
pub_key = "{self._upstream_pubkey}"

listen_address = "{self._downstream_host}"
listen_mining_port = {self._downstream_port}
max_supported_version = {self._max_supported_version}
min_supported_version = {self._min_supported_version}
downstream_share_per_minute = {self._downstream_share_per_minute}
min_individual_miner_hashrate = {self._min_individual_miner_hashrate}
channel_nominal_hashrate = {self._channel_nominal_hashrate}
channel_diff_update_interval = {self._channel_diff_update_interval}
min_extranonce2_size = {self._min_extranonce2_size}
"""

    def _build_command(self, config_path: str) -> tuple[list[str], str]:
        """Build docker run command"""
        container_name = f"minesploit-translator-{id(self)}"

        cmd = [
            "docker",
            "run",
            "--rm",
            "-d",
            "--name",
            container_name,
            "--network",
            "host",
            "-v",
            f"{config_path}:/config/proxy-config.toml:ro",
            self.IMAGE,
            "-c",
            "/config/proxy-config.toml",
        ]

        return cmd, container_name

    def start(self) -> "StratumToStratumV2":
        """Start the translator"""
        self._validate_config()

        config_content = self._generate_config()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as config_file:
            config_file.write(config_content)
            config_path = config_file.name

        subprocess.run(
            ["docker", "pull", self.IMAGE],
            capture_output=True,
            text=True,
        )

        cmd, container_name = self._build_command(config_path)

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start translator: {result.stderr}")

        self._container_name = container_name
        self._running = True

        time.sleep(3)

        return self

    def stop(self) -> None:
        """Stop the translator and cleanup container"""
        if self._container_name:
            subprocess.run(
                ["docker", "stop", self._container_name],
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["docker", "rm", self._container_name],
                capture_output=True,
                text=True,
            )
            self._container_name = None

        self._running = False

    def connect_sv1_client(
        self,
        worker_name: str = "anonymous",
        worker_password: str = "x",
    ) -> StratumClient:
        """Create a Stratum V1 client connected to the translator.

        Args:
            worker_name: Worker name for authorization
            worker_password: Worker password for authorization

        Returns:
            StratumClient instance (call connect manually)

        Usage:
            async with translator:
                client = translator.connect_sv1_client("myworker", "secret")
                await client.connect()
                await client.subscribe()
                await client.authorize()
        """
        client = StratumClient(
            host=self._downstream_host,
            port=self._downstream_port,
            worker_name=worker_name,
            worker_password=worker_password,
        )
        return client

    async def connect_sv1_client_async(
        self,
        worker_name: str = "anonymous",
        worker_password: str = "x",
    ) -> StratumClient:
        """Create and connect a Stratum V1 client to the translator (async).

        This is a convenience method that handles connect, subscribe, and authorize
        in one call.

        Args:
            worker_name: Worker name for authorization
            worker_password: Worker password for authorization

        Returns:
            Connected and authorized StratumClient instance

        Usage:
            async with translator:
                client = await translator.connect_sv1_client_async("myworker", "secret")
                # Ready to mine!
        """
        client = StratumClient(
            host=self._downstream_host,
            port=self._downstream_port,
            worker_name=worker_name,
            worker_password=worker_password,
        )
        await client.connect()
        await client.subscribe()
        await client.authorize()
        return client

    @property
    def downstream_host(self) -> str:
        """Host where translator listens for SV1 connections"""
        return self._downstream_host

    @property
    def downstream_port(self) -> int:
        """Port where translator listens for SV1 connections"""
        return self._downstream_port

    @property
    def is_running(self) -> bool:
        """Whether the translator is running"""
        return self._running

    @property
    def container_id(self) -> str | None:
        """Docker container ID"""
        return self._container_name

    def __enter__(self) -> "StratumToStratumV2":
        return self.start()

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.stop()
        return False
