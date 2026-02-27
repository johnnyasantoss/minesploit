"""CPU Miner utility using Docker-wrapped mujina"""

import subprocess
import time
from dataclasses import dataclass


@dataclass
class PoolConfig:
    host: str
    port: int
    user: str
    password: str = "x"


class CPUMiner:
    IMAGE = "ghcr.io/256foundation/mujina-minerd:latest"
    API_PORT = 7785

    def __init__(
        self,
        threads: int = 1,
        pool: PoolConfig | None = None,
        host: str = "localhost",
        port: int = 3333,
        user: str = "test.worker",
        password: str = "x",
    ):
        self.threads = threads
        self._pool = pool
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._container_name: str | None = None
        self._running = False
        self._api_port = self.API_PORT

    def mine_at(self, pool: PoolConfig) -> "CPUMiner":
        self._pool = pool
        return self.start()

    def _get_pool_config(self) -> PoolConfig:
        if self._pool:
            if hasattr(self._pool, "host") and hasattr(self._pool, "port"):
                return PoolConfig(
                    host=self._pool.host,
                    port=self._pool.port,
                    user=self._user,
                    password=self._password,
                )
            return self._pool
        return PoolConfig(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
        )

    def start(self) -> "CPUMiner":
        pool = self._get_pool_config()
        container_name = f"minesploit-mujina-{id(self)}"

        env = [
            "MUJINA_USB_DISABLE=1",
            f"MUJINA_CPUMINER_THREADS={self.threads}",
            f"MUJINA_POOL_URL=stratum+tcp://{pool.host}:{pool.port}",
            f"MUJINA_POOL_USER={pool.user}",
            f"MUJINA_POOL_PASS={pool.password}",
        ]

        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            f"{self._api_port}:{self.API_PORT}",
        ]
        for e in env:
            cmd.extend(["-e", e])
        cmd.append(self.IMAGE)

        subprocess.run(["docker", "pull", self.image], capture_output=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start miner: {result.stderr}")

        self._container_name = container_name
        self._running = True
        time.sleep(2)
        return self

    def get_stats(self) -> dict:
        if not self._running:
            return {"running": False}

        try:
            import requests

            resp = requests.get(f"http://localhost:{self._api_port}/stats", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "running": True,
                    "hashrate_khs": data.get("hashrate", 0),
                    "accepted": data.get("accepted_shares", 0),
                    "rejected": data.get("rejected_shares", 0),
                }
        except Exception:
            pass

        return {"running": self._running, "hashrate_khs": 0, "accepted": 0, "rejected": 0}

    def stop(self) -> None:
        if self._container_name:
            subprocess.run(["docker", "stop", self._container_name], capture_output=True)
            subprocess.run(["docker", "rm", self._container_name], capture_output=True)
            self._container_name = None
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def image(self) -> str:
        return self.IMAGE

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
