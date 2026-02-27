"""Tests for database.py"""

from minesploit.database import ExploitDatabase, register_exploit, AVAILABLE_EXPLOITS
from minesploit.framework import ExploitMeta


def test_register_exploit():
    AVAILABLE_EXPLOITS.clear()
    meta = ExploitMeta(
        name="Test Exploit",
        cve="CVE-2024-TEST",
        cvss_score=5.0,
        severity="MEDIUM",
        affected_versions="1.0",
        discovered_by="Tester",
        disclosure_date="2024-01-01",
    )
    register_exploit(meta)
    assert "CVE-2024-TEST" in AVAILABLE_EXPLOITS


def test_database_get():
    AVAILABLE_EXPLOITS.clear()
    meta = ExploitMeta(
        name="Test Exploit",
        cve="CVE-2024-GET",
        cvss_score=5.0,
        severity="MEDIUM",
        affected_versions="1.0",
        discovered_by="Tester",
        disclosure_date="2024-01-01",
    )
    register_exploit(meta)

    db = ExploitDatabase()
    result = db.get("CVE-2024-GET")
    assert result is not None
    assert result.cve == "CVE-2024-GET"


def test_database_list():
    AVAILABLE_EXPLOITS.clear()
    register_exploit(
        ExploitMeta(
            name="Exploit 1",
            cve="CVE-1",
            cvss_score=5.0,
            severity="HIGH",
            affected_versions="1.0",
            discovered_by="Tester",
            disclosure_date="2024-01-01",
        )
    )
    register_exploit(
        ExploitMeta(
            name="Exploit 2",
            cve="CVE-2",
            cvss_score=3.0,
            severity="LOW",
            affected_versions="1.0",
            discovered_by="Tester",
            disclosure_date="2024-01-01",
        )
    )

    db = ExploitDatabase()
    exploits = db.list()
    assert len(exploits) == 2


def test_database_by_severity():
    AVAILABLE_EXPLOITS.clear()
    register_exploit(
        ExploitMeta(
            name="High Exploit",
            cve="CVE-H",
            cvss_score=7.0,
            severity="HIGH",
            affected_versions="1.0",
            discovered_by="Tester",
            disclosure_date="2024-01-01",
        )
    )
    register_exploit(
        ExploitMeta(
            name="Low Exploit",
            cve="CVE-L",
            cvss_score=3.0,
            severity="LOW",
            affected_versions="1.0",
            discovered_by="Tester",
            disclosure_date="2024-01-01",
        )
    )

    db = ExploitDatabase()
    high = db.by_severity("HIGH")
    assert len(high) == 1
    assert high[0].severity == "HIGH"
