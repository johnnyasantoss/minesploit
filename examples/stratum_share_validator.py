"""Stratum Share Validator Example

Connects to a Stratum pool, receives mining jobs, and validates share data
using the framework's crypto utilities (hash256, merkle_root).

Usage:
    python examples/stratum_share_validator.py 127.0.0.1 3333
    python examples/stratum_share_validator.py 127.0.0.1 3333 worker1 x
"""

import argparse
import asyncio
import random
import time
from typing import Any

from minesploit.protocols.stratum.client import StratumClient
from minesploit.utils.crypto import decode_hex, encode_hex, merkle_root


async def validate_share(
    client: StratumClient,
    job_id: str,
    extra_nonce_2: str,
    ntime: str,
    nonce: str,
) -> dict[str, Any]:
    """Validate a share using crypto utilities"""
    result: dict[str, Any] = {
        "valid": True,
        "checks": [],
        "errors": [],
    }

    try:
        coinb1 = client.current_job.get("coinb1", "") if client.current_job else ""
        coinb2 = client.current_job.get("coinb2", "") if client.current_job else ""
        merkle_branches = client.current_job.get("merkle_branch", []) if client.current_job else []
        version = client.current_job.get("version", "") if client.current_job else ""
        nbits = client.current_job.get("nbits", "") if client.current_job else ""

        result["checks"].append("Job data available")

        if not all([coinb1, coinb2, version, nbits]):
            result["valid"] = False
            result["errors"].append("Missing job data for validation")
            return result

        if len(nonce) != 8:
            result["valid"] = False
            result["errors"].append(f"Invalid nonce length: {len(nonce)} (expected 8)")
        else:
            result["checks"].append(f"Nonce format valid: {nonce}")

        if len(ntime) != 8:
            result["valid"] = False
            result["errors"].append(f"Invalid ntime length: {len(ntime)} (expected 8)")
        else:
            try:
                ntime_int = int(ntime, 16)
                current_time = int(time.time())
                if abs(ntime_int - current_time) > 7200:
                    result["errors"].append(f"ntime too far from current time: {ntime_int}")
                else:
                    result["checks"].append(f"NTime valid: {ntime_int}")
            except ValueError:
                result["valid"] = False
                result["errors"].append(f"Invalid ntime hex: {ntime}")

        if len(extra_nonce_2) != client.extra_nonce_2_length * 2:
            result["valid"] = False
            result["errors"].append(
                f"ExtraNonce2 length mismatch: {len(extra_nonce_2)} "
                f"(expected {client.extra_nonce_2_length * 2})"
            )
        else:
            result["checks"].append(f"ExtraNonce2 format valid: {extra_nonce_2}")

        try:
            decode_hex(coinb1)
            decode_hex(coinb2)
            _ = [decode_hex(branch) for branch in merkle_branches]
            result["checks"].append("All hex data decodes successfully")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Hex decode error: {e}")
            return result

        try:
            mr = merkle_root([decode_hex(branch) for branch in merkle_branches])
            result["checks"].append(f"Merkle root computed: {encode_hex(mr)}")
        except Exception as e:
            result["errors"].append(f"Merkle root computation error: {e}")

        try:
            target = decode_hex(nbits)
            result["checks"].append(f"NBits decoded: {encode_hex(target)}")
        except Exception as e:
            result["errors"].append(f"NBits decode error: {e}")

    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Validation error: {e}")

    return result


async def run_validator(
    host: str, port: int, worker_name: str, worker_password: str, num_shares: int = 5
):
    print(f"\n[~] Connecting to {host}:{port} as {worker_name}...\n")

    client = StratumClient(
        host=host,
        port=port,
        worker_name=worker_name,
        worker_password=worker_password,
        verbosity="debug",
    )

    try:
        if not await client.connect():
            print(f"[-] Failed to connect to {host}:{port}")
            return

        print(f"[+] Connected to {host}:{port}")

        if not await client.subscribe():
            print("[-] Failed to subscribe to mining notifications")
            return

        print(
            f"[+] Subscribed (session: {client.session_id}, extra_nonce_1: {client.extra_nonce_1})"
        )

        if not await client.authorize():
            print(f"[-] Failed to authorize worker: {worker_name}")
            return

        print(f"[+] Authorized as {worker_name}")
        print("[~] Waiting for mining job...\n")

        await asyncio.sleep(2)
        await client.handle_notifications()

        if not client.current_job:
            print("[-] No mining job received")
            return

        job = client.current_job
        print(f"[+] Received job: {job['job_id']}")
        print(f"    Version: {job['version']}")
        print(f"    NBits: {job['nbits']}")
        print(f"    NTime: {job['ntime']}")
        print(f"    Merkle branches: {len(job['merkle_branch'])}")

        print(f"\n[~] Generating and validating {num_shares} shares...\n")

        for i in range(num_shares):
            extra_nonce_2 = f"{random.randint(0, 0xFFFFFFFF):08x}"[
                : client.extra_nonce_2_length * 2
            ]
            ntime = format(int(time.time()), "08x")
            nonce = f"{random.randint(0, 0xFFFFFFFF):08x}"

            print(f"--- Share #{i + 1} ---")
            print(f"  Job ID: {job['job_id']}")
            print(f"  ExtraNonce2: {extra_nonce_2}")
            print(f"  NTime: {ntime}")
            print(f"  Nonce: {nonce}")

            validation = await validate_share(
                client,
                job["job_id"],
                extra_nonce_2,
                ntime,
                nonce,
            )

            print("  Validation:")
            for check in validation["checks"]:
                print(f"    + {check}")
            for error in validation["errors"]:
                print(f"    - {error}")

            submit_result = await client.submit(
                job["job_id"],
                extra_nonce_2,
                ntime,
                nonce,
            )

            print(f"  Submit: {'ACCEPTED' if submit_result else 'REJECTED'}\n")

            await asyncio.sleep(1)
            await client.handle_notifications()

            if client.current_job and client.current_job["job_id"] != job["job_id"]:
                job = client.current_job
                print(f"[+] New job received: {job['job_id']}\n")

        print(f"[~] Completed {num_shares} share validations")

    except KeyboardInterrupt:
        print("\n[-] Interrupted by user")
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        await client.close()
        print("[+] Connection closed")


def main():
    parser = argparse.ArgumentParser(
        description="Validate Stratum shares using framework crypto utilities"
    )
    parser.add_argument(
        "host",
        help="Stratum server host",
    )
    parser.add_argument(
        "port",
        type=int,
        help="Stratum server port",
    )
    parser.add_argument(
        "worker_name",
        nargs="?",
        default="worker1",
        help="Worker name (default: worker1)",
    )
    parser.add_argument(
        "worker_password",
        nargs="?",
        default="x",
        help="Worker password (default: x)",
    )
    parser.add_argument(
        "-n",
        "--num-shares",
        type=int,
        default=5,
        help="Number of shares to generate and validate (default: 5)",
    )

    args = parser.parse_args()

    asyncio.run(
        run_validator(
            args.host,
            args.port,
            args.worker_name,
            args.worker_password,
            args.num_shares,
        )
    )


if __name__ == "__main__":
    main()
