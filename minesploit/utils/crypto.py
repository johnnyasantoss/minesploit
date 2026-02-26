"""Cryptographic utilities for Bitcoin mining"""

import hashlib


def hash256(data: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def double_sha256(data: bytes) -> bytes:
    return hash256(data)


def ripemd160(data: bytes) -> bytes:
    h = hashlib.new("ripemd160")
    h.update(data)
    return h.digest()


def hash160(data: bytes) -> bytes:
    return ripemd160(hashlib.sha256(data).digest())


def merkle_root(merkle_branches: list[bytes]) -> bytes:
    if not merkle_branches:
        return b"\x00" * 32

    merkle_root = merkle_branches[0]
    for branch in merkle_branches[1:]:
        merkle_root = hash256(merkle_root + branch)

    return merkle_root


def varint(n: int) -> bytes:
    if n < 0xFD:
        return bytes([n])
    elif n < 0xFFFF:
        return b"\xfd" + n.to_bytes(2, "little")
    elif n < 0xFFFFFFFF:
        return b"\xfe" + n.to_bytes(4, "little")
    else:
        return b"\xff" + n.to_bytes(8, "little")


def encode_hex(data: bytes) -> str:
    return data.hex()


def decode_hex(hex_str: str) -> bytes:
    return bytes.fromhex(hex_str)


def reverse_hex(hex_str: str) -> str:
    return bytes.fromhex(hex_str)[::-1].hex()
