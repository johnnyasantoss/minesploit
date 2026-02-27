"""CPU Miner utility using Docker-wrapped cpuminer"""

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
    IMAGE = "pmietlicki/cpuminer:latest"

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

    def mine_at(self, pool: PoolConfig) -> "CPUMiner":
        self._pool = pool
        return self.start()

    def _get_pool_config(self) -> PoolConfig:
        import platform

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
        container_name = f"minesploit-miner-{id(self)}"

        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            "host",
            "-e",
            f"POOL=stratum+tcp://{pool.host}:{pool.port}",
            "-e",
            f"USER={pool.user}",
            "-e",
            f"PASS={pool.password}",
            "-e",
            "ALGO=sha256d",
            "-e",
            f"NB_THREADS={self.threads}",
            self.IMAGE,
        ]

        subprocess.run(["docker", "pull", self.image], capture_output=True)
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start miner: {result.stderr}")

        self._container_name = container_name
        self._running = True
        time.sleep(2)
        return self

    def get_stats(self) -> dict:
        if not self._running or not self._container_name:
            return {"running": False}

        result = subprocess.run(
            ["docker", "logs", self._container_name],
            capture_output=True,
            text=True,
        )
        output = result.stdout + result.stderr

        import re

        hashrate = 0.0
        for unit, mult in [("MH/s", 1000), ("kH/s", 1)]:
            m = re.search(r"(\d+\.\d+)\s*" + unit, output)
            if m:
                hashrate = float(m.group(1)) * mult
                break

        accepted = len(re.findall(r"accepted", output, re.I))
        rejected = len(re.findall(r"rejected", output, re.I))

        return {
            "running": True,
            "hashrate_khs": hashrate,
            "accepted": accepted,
            "rejected": rejected,
        }

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
