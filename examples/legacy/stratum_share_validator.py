#!/usr/bin/env -S minesploit -s
"""Stratum Share Validator Example"""

import argparse
import asyncio
import random
import time

from minesploit.protocols.stratum.client import StratumClient
from minesploit.utils.crypto import validate_share_format, validate_share_job


async def main(host: str, port: int, worker: str, password: str, num_shares: int):
    client = StratumClient(host, port, worker, password)

    await client.connect()
    await client.subscribe()
    await client.authorize()

    await asyncio.sleep(1)
    await client.handle_notifications()

    if not client.current_job:
        print("[-] No job received")
        return

    job = client.current_job
    is_valid, missing = validate_share_job(job)
    print(f"[+] Job: {job['job_id']}, valid: {is_valid}")
    if missing:
        print(f"    Missing fields: {missing}")

    for i in range(num_shares):
        extra_nonce_2 = f"{random.randint(0, 0xFFFFFFFF):08x}"[: client.extra_nonce_2_length * 2]
        ntime = format(int(time.time()), "08x")
        nonce = f"{random.randint(0, 0xFFFFFFFF):08x}"

        is_valid, checks, errors = validate_share_format(
            nonce, ntime, extra_nonce_2, client.extra_nonce_2_length
        )

        print(f"--- Share #{i + 1} ---")
        print(f"  Valid: {is_valid}")
        for c in checks:
            print(f"    + {c}")
        for e in errors:
            print(f"    - {e}")

        result = await client.submit(job["job_id"], extra_nonce_2, ntime, nonce)
        print(f"  Submit: {'ACCEPTED' if result else 'REJECTED'}\n")

    await client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument("worker", nargs="?", default="worker1")
    parser.add_argument("password", nargs="?", default="x")
    parser.add_argument("-n", "--num-shares", type=int, default=3)
    args = parser.parse_args()

    asyncio.run(main(args.host, args.port, args.worker, args.password, args.num_shares))
