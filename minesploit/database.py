"""Exploit database and registry"""

from minesploit.framework import ExploitMeta
from typing import Any


AVAILABLE_EXPLOITS: dict[str, ExploitMeta] = {}


def register_exploit(meta: ExploitMeta):
    """Register an exploit in the database"""
    AVAILABLE_EXPLOITS[meta.cve or meta.name] = meta


class ExploitDatabase:
    def __init__(self):
        self._exploits = AVAILABLE_EXPLOITS.copy()

    def list(self, category: str | None = None) -> list[ExploitMeta]:
        """List all available exploits, optionally filtered by category"""
        if category:
            return [e for e in self._exploits.values() if category.lower() in e.severity.lower()]
        return list(self._exploits.values())

    def get(self, name: str) -> ExploitMeta | None:
        """Get exploit by name or CVE"""
        return self._exploits.get(name)

    def search(self, query: str) -> list[ExploitMeta]:
        """Search exploits by name, CVE, or description"""
        query = query.lower()
        return [
            e
            for e in self._exploits.values()
            if query in (e.name or "").lower()
            or query in (e.cve or "").lower()
            or query in (e.description or "").lower()
        ]

    def by_severity(self, severity: str) -> list[ExploitMeta]:
        """Get exploits by severity level"""
        return [e for e in self._exploits.values() if e.severity.upper() == severity.upper()]

    def by_target(self, target: str) -> list[ExploitMeta]:
        """Get exploits for a specific target"""
        target = target.lower()
        return [e for e in self._exploits.values() if target in e.affected_versions.lower()]
