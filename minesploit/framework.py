"""Core framework classes for Minesploit"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ExploitResult:
    def __init__(
        self,
        success: bool,
        message: str = "",
        details: dict[str, Any] | None = None,
    ):
        self.success = success
        self.message = message
        self.details = details or {}

    def __bool__(self) -> bool:
        return self.success


@dataclass
class ExploitMeta:
    name: str
    cve: str | None
    cvss_score: float | None
    severity: str
    affected_versions: str
    discovered_by: str | None
    disclosure_date: str | None
    description: str = ""
    references: list[str] = field(default_factory=list)


class Exploit(ABC):
    """Base class for all exploit modules"""

    meta: ExploitMeta

    def __init__(self):
        self.target: str | None = None
        self.port: int | None = None
        self.options: dict[str, Any] = {}

    async def check(self, target: str, **kwargs) -> ExploitResult:
        """Check if target is vulnerable. Override in subclasses."""
        raise NotImplementedError

    async def exploit(self, target: str, **kwargs) -> ExploitResult:
        """Run exploit against target. Override in subclasses."""
        raise NotImplementedError

    async def verify(self, target: str, **kwargs) -> ExploitResult:
        """Verify exploit succeeded. Override in subclasses."""
        raise NotImplementedError

    def set_option(self, name: str, value: Any):
        self.options[name] = value

    def get_option(self, name: str, default: Any = None) -> Any:
        return self.options.get(name, default)


class Scanner(ABC):
    """Base class for scanning modules"""

    def __init__(self):
        self.target: str | None = None
        self.port: int | None = None

    @abstractmethod
    async def scan(self, target: str, **kwargs) -> ExploitResult:
        """Perform scan. Override in subclasses."""
        raise NotImplementedError

    @abstractmethod
    async def identify(self, target: str, **kwargs) -> dict[str, Any]:
        """Identify service/version. Override in subclasses."""
        raise NotImplementedError
