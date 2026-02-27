#!/usr/bin/env -S minesploit -s
"""Stratum V1 Sniffer Example - intercept and log mining protocol messages"""

from minesploit.protocols.stratum.sniffer import StratumSniffer

async with StratumSniffer(
    listen_host="127.0.0.1",
    listen_port=3334,
    upstream_host="127.0.0.1",
    upstream_port=3333,
    output_file="stratum_messages.jsonl",
) as sniffer:
    print("Sniffer running... press Ctrl+C to stop")
    try:
        while True:
            await asyncio.sleep(5)
            msgs = sniffer.get_messages()
            print(f"Captured {len(msgs)} messages")
    except KeyboardInterrupt:
        pass

print(f"\nFinal: {len(sniffer.get_messages())} messages captured")
