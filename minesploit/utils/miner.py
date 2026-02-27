"""CPU Miner utility using Docker-wrapped mujina"""

import importlib.util
import re
import subprocess
import time
from dataclasses import dataclass

REQUESTS_AVAILABLE = importlib.util.find_spec("requests") is not None


@dataclass
class PoolConfig:
    """Stratum pool connection configuration"""

    host: str
    port: int
    user: str
    password: str = "x"


class CPUMiner:
    """RAII wrapper for mujina CPU miner running in Docker

    Usage:
        with CPUMiner(threads=4) as miner:
            miner.mine_at(PoolConfig(host="pool.example.com", port=3333, user="worker"))
            time.sleep(60)  # mine for 60 seconds
            stats = miner.get_stats()
        # container auto-cleaned on exit
    """

    IMAGE = "ghcr.io/256foundation/mujina-minerd:latest"
    API_PORT = 7785

    def __init__(
        self,
        threads: int = 1,
        image: str = IMAGE,
    ):
        self.threads = threads
        self.image = image
        self._container_name: str | None = None
        self._running = False
        self._pool: PoolConfig | None = None
        self._api_port = self.API_PORT

    def mine_at(self, pool: PoolConfig) -> "CPUMiner":
        """Connect miner to a pool (fluent API)"""
        self._pool = pool
        self._start()
        return self

    def _build_env(self) -> list[str]:
        env = [
            "MUJINA_USB_DISABLE=1",
            f"MUJINA_CPUMINER_THREADS={self.threads}",
        ]

        if self._pool:
            env.append(f"MUJINA_POOL_URL=stratum+tcp://{self._pool.host}:{self._pool.port}")
            env.append(f"MUJINA_POOL_USER={self._pool.user}")
            env.append(f"MUJINA_POOL_PASS={self._pool.password}")

        return env

    def _build_command(self) -> tuple[list[str], str]:
        container_name = f"minesploit-mujina-{id(self)}"

        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "-p",
            f"{self._api_port}:{self.API_PORT}",
        ]

        for env_var in self._build_env():
            cmd.extend(["-e", env_var])

        cmd.append(self.image)

        return cmd, container_name

    def _start(self) -> None:
        """Start the Docker container with mujina"""
        cmd, container_name = self._build_command()

        subprocess.run(
            ["docker", "pull", self.image],
            capture_output=True,
            text=True,
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to start miner: {result.stderr}")

        self._container_name = container_name
        self._running = True

        time.sleep(2)

    def get_stats(self) -> dict:
        """Get mining statistics from mujina API"""
        if not self._running:
            return {"running": False}

        if REQUESTS_AVAILABLE:
            import requests  # type: ignore[import-untyped]

            try:
                resp = requests.get(f"http://localhost:{self._api_port}/stats", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "running": True,
                        "hashrate_khs": data.get("hashrate", 0),
                        "accepted": data.get("accepted_shares", 0),
                        "rejected": data.get("rejected_shares", 0),
                        "errors": data.get("errors", []),
                    }
            except Exception:
                pass

        return self._get_stats_from_logs()

    def _get_stats_from_logs(self) -> dict:
        """Parse stats from Docker logs"""
        if not self._container_name:
            return {"running": False}

        result = subprocess.run(
            ["docker", "logs", self._container_name],
            capture_output=True,
            text=True,
        )

        output = result.stdout + result.stderr

        hashrate = 0.0
        for unit, multiplier in [("MH/s", 1000), ("kH/s", 1)]:
            match = re.search(rf"(\d+\.\d+)\s*{unit}", output)
            if match:
                hashrate = float(match.group(1)) * multiplier
                break

        accepted = len(re.findall(r"accepted|share", output, re.I))

        return {
            "running": self._running,
            "hashrate_khs": hashrate,
            "accepted": accepted,
            "rejected": 0,
        }

    def stop(self) -> None:
        """Stop mining and cleanup container"""
        if self._container_name:
            subprocess.run(
                ["docker", "stop", self._container_name],
                capture_output=True,
            )
            subprocess.run(
                ["docker", "rm", self._container_name],
                capture_output=True,
            )
            self._container_name = None

        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
