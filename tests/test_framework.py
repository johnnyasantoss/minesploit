"""Tests for framework.py"""

from minesploit.framework import Exploit, ExploitMeta, ExploitResult


def test_exploit_result_bool_true():
    result = ExploitResult(success=True, message="test")
    assert bool(result) is True


def test_exploit_result_bool_false():
    result = ExploitResult(success=False, message="test")
    assert bool(result) is False


def test_exploit_result_message():
    result = ExploitResult(success=True, message="test message")
    assert result.message == "test message"


def test_exploit_result_details():
    result = ExploitResult(success=True, details={"key": "value"})
    assert result.details["key"] == "value"


def test_exploit_options():
    class TestExploit(Exploit):
        pass

    exploit = TestExploit()
    exploit.set_option("test_key", "test_value")
    assert exploit.get_option("test_key") == "test_value"
    assert exploit.get_option("missing", "default") == "default"


def test_exploit_meta():
    meta = ExploitMeta(
        name="Test Exploit",
        cve="CVE-2024-1234",
        cvss_score=7.5,
        severity="HIGH",
        affected_versions="1.0-2.0",
        discovered_by="Tester",
        disclosure_date="2024-01-01",
        description="Test description",
        references=["http://example.com"],
    )
    assert meta.name == "Test Exploit"
    assert meta.cve == "CVE-2024-1234"
    assert meta.cvss_score == 7.5
