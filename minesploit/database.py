"""Exploit database and registry"""

from __future__ import annotations

from minesploit.framework import ExploitMeta

AVAILABLE_EXPLOITS: dict[str, ExploitMeta] = {}


def register_exploit(meta: ExploitMeta):
    """Register an exploit in the database"""
    AVAILABLE_EXPLOITS[meta.cve or meta.name] = meta


class ExploitDatabase:
    def __init__(self):
        pass

    def _ensure_scanned(self) -> None:
        """Trigger exploit discovery if not yet scanned"""
        import minesploit.exploits as exploits

        exploits._scan_exploits()

    def _get_exploits(self) -> dict[str, ExploitMeta]:
        """Get the exploits dict, triggering scan if needed"""
        self._ensure_scanned()
        return AVAILABLE_EXPLOITS

    def list(self, category: str | None = None) -> list[ExploitMeta]:
        """List all available exploits, optionally filtered by category"""
        exploits = self._get_exploits()
        if category:
            return [e for e in exploits.values() if category.lower() in e.severity.lower()]
        return list(exploits.values())

    def get(self, name: str) -> ExploitMeta | None:
        """Get exploit by name or CVE"""
        return self._get_exploits().get(name)

    def search(self, query: str) -> list[ExploitMeta]:
        """Search exploits by name, CVE, or description"""
        exploits = self._get_exploits()
        query = query.lower()
        return [
            e
            for e in exploits.values()
            if query in (e.name or "").lower()
            or query in (e.cve or "").lower()
            or query in (e.description or "").lower()
        ]

    def by_severity(self, severity: str) -> list[ExploitMeta]:
        """Get exploits by severity level"""
        exploits = self._get_exploits()
        return [e for e in exploits.values() if e.severity.upper() == severity.upper()]

    def by_target(self, target: str) -> list[ExploitMeta]:
        """Get exploits for a specific target"""
        exploits = self._get_exploits()
        target = target.lower()
        return [e for e in exploits.values() if target in e.affected_versions.lower()]
