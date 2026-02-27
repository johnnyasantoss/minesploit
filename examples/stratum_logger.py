"""Stratum V1 Sniffer Example - intercept and log mining protocol messages"""

import asyncio

from minesploit.protocols.stratum.sniffer import StratumSniffer


async def main():
    async with StratumSniffer(
        listen_host="127.0.0.1",
        listen_port=3334,
        upstream_host="127.0.0.1",
        upstream_port=3333,
        output_file="stratum_messages.jsonl",
        verbosity="debug",
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
