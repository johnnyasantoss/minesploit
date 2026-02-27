"""Network utilities for connecting to mining services"""

import asyncio
import ssl


class TCPClient:
    def __init__(self, host: str, port: int, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def connect(self) -> bool:
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
            return True
        except (OSError, asyncio.TimeoutError, ConnectionRefusedError):
            return False

    async def send(self, data: bytes) -> bool:
        if not self.writer:
            return False
        try:
            self.writer.write(data)
            await self.writer.drain()
            return True
        except OSError:
            return False

    async def recv(self, size: int = 4096) -> bytes | None:
        if not self.reader:
            return None
        try:
            data = await asyncio.wait_for(
                self.reader.read(size),
                timeout=self.timeout,
            )
            return data if data else None
        except asyncio.TimeoutError:
            return None

    async def recv_line(self) -> str | None:
        if not self.reader:
            return None
        try:
            line = await asyncio.wait_for(
                self.reader.readline(),
                timeout=self.timeout,
            )
            return line.decode("utf-8").strip() if line else None
        except asyncio.TimeoutError:
            return None

    async def close(self):
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.reader = None
        self.writer = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class SSLClient(TCPClient):
    def __init__(
        self,
        host: str,
        port: int,
        timeout: int = 10,
        verify_ssl: bool = True,
    ):
        super().__init__(host, port, timeout)
        self.verify_ssl = verify_ssl

    async def connect(self) -> bool:
        try:
            ssl_context = ssl.create_default_context()
            if not self.verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port, ssl=ssl_context),
                timeout=self.timeout,
            )
            return True
        except (OSError, asyncio.TimeoutError, ConnectionRefusedError):
            return False


async def scan_port(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (OSError, asyncio.TimeoutError, ConnectionRefusedError):
        return False


async def scan_ports(host: str, ports: list[int], timeout: float = 1.0) -> dict[int, bool]:
    results: list[bool | BaseException] = await asyncio.gather(
        *[scan_port(host, port, timeout) for port in ports],
        return_exceptions=True,
    )
    return {
        port: isinstance(result, bool) and result
        for port, result in zip(ports, results, strict=True)
    }


def parse_host_port(target: str) -> tuple[str, int]:
    if ":" in target:
        host, port_str = target.rsplit(":", 1)
        return host, int(port_str)
    return target, 8333
