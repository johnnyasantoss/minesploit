"""Cryptographic utilities for Bitcoin mining"""

import hashlib
import time


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


def validate_share_format(
    nonce: str, ntime: str, extra_nonce_2: str, extra_nonce_2_length: int
) -> tuple[bool, list[str], list[str]]:
    checks: list[str] = []
    errors: list[str] = []

    if len(nonce) != 8:
        errors.append(f"Invalid nonce length: {len(nonce)} (expected 8)")
    else:
        checks.append(f"Nonce format valid: {nonce}")

    if len(ntime) != 8:
        errors.append(f"Invalid ntime length: {len(ntime)} (expected 8)")
    else:
        try:
            ntime_int = int(ntime, 16)
            current_time = int(time.time())
            if abs(ntime_int - current_time) > 7200:
                errors.append(f"ntime too far from current time: {ntime_int}")
            else:
                checks.append(f"NTime valid: {ntime_int}")
        except ValueError:
            errors.append(f"Invalid ntime hex: {ntime}")

    expected_extra_nonce_2_len = extra_nonce_2_length * 2
    if len(extra_nonce_2) != expected_extra_nonce_2_len:
        errors.append(
            f"ExtraNonce2 length mismatch: {len(extra_nonce_2)} "
            f"(expected {expected_extra_nonce_2_len})"
        )
    else:
        checks.append(f"ExtraNonce2 format valid: {extra_nonce_2}")

    is_valid = len(errors) == 0
    return (is_valid, checks, errors)


def validate_share_job(job: dict) -> tuple[bool, list[str]]:
    required_fields = ["coinb1", "coinb2", "version", "nbits", "merkle_branch"]
    missing_fields = [field for field in required_fields if field not in job]
    is_valid = len(missing_fields) == 0
    return (is_valid, missing_fields)
