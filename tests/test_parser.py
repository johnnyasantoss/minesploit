"""Tests for parser.py"""

from minesploit.utils.parser import JSONRPCParser, StratumParser, BTCNodeParser


def test_stratum_parser_create_message():
    msg = StratumParser.create_message("mining.subscribe", ["worker1"])
    assert b'"method"' in msg
    assert b'"mining.subscribe"' in msg
    assert msg.endswith(b"\n")


def test_stratum_parser_mining_subscribe():
    msg = StratumParser.mining_subscribe("worker1")
    assert b"mining.subscribe" in msg
    assert b"worker1" in msg


def test_stratum_parser_mining_authorize():
    msg = StratumParser.mining_authorize("worker1", "x")
    assert b"mining.authorize" in msg
    assert b"worker1" in msg
    assert b"x" in msg


def test_stratum_parser_mining_submit():
    msg = StratumParser.mining_submit("worker1", "job123", "extra", "ntime", "nonce")
    assert b"mining.submit" in msg
    assert b"worker1" in msg
    assert b"job123" in msg


def test_jsonrpc_parser_create_request():
    msg = JSONRPCParser.create_request("test.method", ["param1"], msg_id=1)
    parsed = JSONRPCParser.parse_response(msg)
    assert parsed is not None
    assert parsed["method"] == "test.method"
    assert parsed["params"] == ["param1"]
    assert parsed["id"] == 1


def test_jsonrpc_parser_parse_response():
    data = b'{"id": 1, "result": "success", "error": null}\n'
    parsed = JSONRPCParser.parse_response(data)
    assert parsed is not None
    assert parsed["result"] == "success"
    assert parsed["error"] is None


def test_jsonrpc_parser_parse_invalid():
    result = JSONRPCParser.parse_response(b"invalid json")
    assert result is None


def test_btcnode_parser_parse_message():
    data = (
        b"\xf9\xbe\xb4\xd9"
        b"version\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x00"
        b"\x00\x00\x00\x00"
        b"\x00\x00\x00\x00"
    )
    parsed = BTCNodeParser.parse_message(data)
    assert parsed is not None
    assert parsed["network"] == "mainnet"
    assert parsed["command"] == "version"


def test_btcnode_parser_parse_short():
    data = b"\xf9\xbe"
    parsed = BTCNodeParser.parse_message(data)
    assert parsed is None
