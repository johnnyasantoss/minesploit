"""Tests for networking.py"""

from minesploit.utils.networking import parse_host_port


def test_parse_host_port_with_port():
    host, port = parse_host_port("192.168.1.1:8333")
    assert host == "192.168.1.1"
    assert port == 8333


def test_parse_host_port_default():
    host, port = parse_host_port("192.168.1.1")
    assert host == "192.168.1.1"
    assert port == 8333


def test_parse_host_port_ipv6_with_port():
    host, port = parse_host_port("[::1]:8333")
    assert host == "[::1]"
    assert port == 8333
