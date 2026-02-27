"""Minesploit REPL shell"""

import cmd
import random
import sys
from typing import Any

BANNER_PHRASES = [
    "Stack sats, not vulnz",
    "HODL your keys, crack their protocols",
    "In code we trust, especially when it's audited",
    "Layer 2: More secure than your pool",
    "Mining to the moon, one CVE at a time",
    "Don't trust, verify... the exploit",
    "51% attacks are just a community reorganization",
    "SIP-009: Never roll back a penetration test",
    "Orange pilling, white hat style",
    "Proof of Work > Proof of Vulnerability",
]

EXPLOIT_COUNT = 5


def generate_banner() -> str:
    phrase = random.choice(BANNER_PHRASES)
    padding = (60 - len(phrase)) // 2
    padded_phrase = " " * padding + phrase + " " * (60 - len(phrase) - padding)

    return f"""
 ______________________________________________________________
| {padded_phrase} |
|______________________________________________________________|
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\
                ||----w |
                ||     ||

 Minesploit | Bitcoin Mining Security Research Framework
 ─────────────────────────────────────────────────────────
 [⚡] Authorized security testing only | Use responsibly

 ┌─────────────────────────────────────────────────────────┐
 │ VERSION    │ EXPLOITS    │ PROTOCOLS                    │
 │ v0.1.0     │ {EXPLOIT_COUNT:<10}  │ Stratum V1, V2, P2Pool       │
 └─────────────────────────────────────────────────────────┘

 COMMANDS                  DESCRIPTION
 ─────────────────────────────────────────────────────────
 help                      Show this help message
 list exploits             List all available exploits
 search <query>            Search exploits by name/CVE
 use <exploit>             Select an exploit module
 set <option> <value>      Set option (RHOSTS, RPORT, etc)
 show options              Show current configuration
 check                     Check if target is vulnerable
 run                       Run exploit against target
 verify                    Verify exploit success
 exit/quit                 Exit the shell

 EXAMPLES
 ─────────────────────────────────────────────────────────
 minesploit> set RHOSTS 192.168.1.100
 minesploit> set RPORT 3333
 minesploit> use cve_2024_blocktxn_dos
 minesploit> check

 ─────────────────────────────────────────────────────────
 """


class MinesploitShell(cmd.Cmd):
    intro = generate_banner()

    prompt = "minesploit> "
    use_rawinput = True
    current_exploit: Any = None

    def __init__(self):
        super().__init__()
        self.exploits: dict[str, Any] = {}
        self.target: str | None = None
        self.port: int | None = None
        self._ctrl_c_pressed = False
        self._ctrl_d_pressed = False
        self._interactive = sys.stdin.isatty()

    def cmdloop(self, intro=None):
        if intro is None:
            intro = self.intro
        if intro:
            print(intro)

        while True:
            try:
                if self._interactive:
                    line = input(self.prompt)
                else:
                    line = sys.stdin.readline()
                    if not line:
                        if self._ctrl_d_pressed:
                            print("\nGoodbye!")
                            break
                        print("\nPress Ctrl+D again to exit")
                        self._ctrl_d_pressed = True
                        continue
                    line = line.strip()
                    if line:
                        print(f"{self.prompt}{line}")

                if not line:
                    continue

                stop = self.onecmd(line)
                if stop:
                    break

            except KeyboardInterrupt:
                if self._ctrl_c_pressed:
                    print("\nGoodbye!")
                    break
                print("\nPress Ctrl+C again to exit")
                self._ctrl_c_pressed = True
            except EOFError:
                if self._ctrl_d_pressed:
                    print("\nGoodbye!")
                    break
                print("\nPress Ctrl+D again to exit")
                self._ctrl_d_pressed = True

    def onecmd(self, line: str) -> bool:
        self._ctrl_c_pressed = False
        self._ctrl_d_pressed = False
        return super().onecmd(line)

    def do_help(self, arg: str):
        """Show available commands"""
        if arg:
            self.do_help(arg)
            return

        print("""
Available Commands:
  list exploits          - List all available exploits
  search <query>        - Search exploits by name/CVE
  use <exploit>         - Select an exploit module
  set <option> <value>  - Set exploit option
  show options          - Show current exploit options
  check                 - Check if target is vulnerable
  run                   - Run exploit against target
  verify                - Verify exploit success
  set target <host>     - Set target host
  set port <port>       - Set target port
  exit                  - Exit the shell
        """)

    def do_list(self, arg: str):
        """List exploits - usage: list [exploits]"""
        if "exploit" in arg or not arg:
            print("\nAvailable Exploits:")
            print("-" * 60)
            print(f"{'Name':<40} {'Severity':<10} {'CVE':<15}")
            print("-" * 60)

            exploits = [
                ("cve_2013_stratum_duplicate_shares", "HIGH", "N/A (2013)"),
                ("cve_2016_stratum_mass_duplicate", "MEDIUM", "N/A (2016)"),
                ("cve_2018_cgminer_api_overflow", "CRITICAL", "CVE-2018-10058"),
                ("cve_2018_cgminer_path_traversal", "HIGH", "CVE-2018-10057"),
                ("cve_2024_blocktxn_dos", "HIGH", "CVE-2024-35202"),
                ("cve_2019_headers_oom", "HIGH", "CVE-2019-25220"),
            ]

            for name, severity, cve in exploits:
                print(f"{name:<40} {severity:<10} {cve:<15}")
            print()

    def do_search(self, arg: str):
        """Search exploits by name or CVE"""
        if not arg:
            print("Usage: search <query>")
            return

        query = arg.lower()
        results = [
            ("cve_2013_stratum_duplicate_shares", "Stratum duplicate shares"),
            ("cve_2016_stratum_mass_duplicate", "Stratum mass duplicate"),
            ("cve_2018_cgminer_api_overflow", "cgminer API buffer overflow"),
            ("cve_2018_cgminer_path_traversal", "cgminer path traversal"),
            ("cve_2024_blocktxn_dos", "Bitcoin Core blocktxn DoS"),
            ("cve_2019_headers_oom", "Bitcoin Core headers OOM"),
        ]

        print(f"\nSearch results for '{arg}':")
        for name, desc in results:
            if query in name.lower() or query in desc.lower():
                print(f"  {name}")
                print(f"    {desc}")
        print()

    def do_use(self, arg: str):
        """Use an exploit module"""
        if not arg:
            print("Usage: use <exploit_name>")
            return

        valid_exploits = {
            "cve_2013_stratum_duplicate_shares": "CVE-2013 Stratum Duplicate Shares",
            "cve_2016_stratum_mass_duplicate": "CVE-2016 Stratum Mass Duplicate",
            "cve_2018_cgminer_api_overflow": "CVE-2018-10058 cgminer API Overflow",
            "cve_2018_cgminer_path_traversal": "CVE-2018-10057 cgminer Path Traversal",
            "cve_2024_blocktxn_dos": "CVE-2024-35202 Bitcoin Core blocktxn DoS",
            "cve_2019_headers_oom": "CVE-2019-25220 Bitcoin Core Headers OOM",
        }

        if arg in valid_exploits:
            self.current_exploit = arg
            self.prompt = f"minesploit ({arg})> "
            print(f"Using {valid_exploits[arg]}")
            print("Set RHOSTS and RPORT before running 'check' or 'run'")
        else:
            print(f"Unknown exploit: {arg}")
            print("Use 'list exploits' to see available modules")

    def do_set(self, arg: str):
        """Set options - usage: set <option> <value> or set target/port"""
        if not arg:
            print("Usage: set <option> <value>")
            print("       set target <host>")
            print("       set port <port>")
            return

        parts = arg.split()
        if len(parts) < 2:
            print("Usage: set <option> <value>")
            return

        key, value = parts[0], parts[1]

        if key == "target":
            self.target = value
            print(f"target => {value}")
        elif key == "port":
            try:
                self.port = int(value)
                print(f"port => {self.port}")
            except ValueError:
                print(f"Invalid port: {value}")
        elif key == "RHOSTS":
            self.target = value
            print(f"RHOSTS => {value}")
        elif key == "RPORT":
            try:
                self.port = int(value)
                print(f"RPORT => {self.port}")
            except ValueError:
                print(f"Invalid port: {value}")
        else:
            print(f"Setting {key} => {value}")

    def do_show(self, arg: str):
        """Show options"""
        if "option" in arg or not arg:
            print("\nCurrent Configuration:")
            print(f"  RHOSTS: {self.target or 'not set'}")
            print(f"  RPORT:  {self.port or 'not set'}")
            if self.current_exploit:
                print(f"  Exploit: {self.current_exploit}")
            print()

    def do_check(self, arg: str):
        """Check if target is vulnerable"""
        if not self.current_exploit:
            print("No exploit selected. Use 'use <exploit>' first.")
            return

        if not self.target:
            print("Target not set. Use 'set RHOSTS <target>'")
            return

        print(f"Checking {self.target}:{self.port or 8333}...")
        print("[*] This is a demonstration - no actual check performed")
        print("[+] Target appears vulnerable (demo)")

    def do_run(self, arg: str):
        """Run exploit against target"""
        if not self.current_exploit:
            print("No exploit selected. Use 'use <exploit>' first.")
            return

        if not self.target:
            print("Target not set. Use 'set RHOSTS <target>'")
            return

        print(f"Running {self.current_exploit} against {self.target}:{self.port or 8333}...")
        print("[*] This is a demonstration - no actual exploit performed")
        print("[+] Exploit completed (demo)")

    def do_verify(self, arg: str):
        """Verify exploit succeeded"""
        if not self.current_exploit:
            print("No exploit selected. Use 'use <exploit>' first.")
            return

        print("Verifying exploit...")
        print("[*] This is a demonstration - no actual verification performed")

    def do_exit(self, arg: str):
        """Exit the shell"""
        print("Goodbye!")
        return True

    def do_quit(self, arg: str):
        """Exit the shell"""
        return self.do_exit(arg)

    def do_back(self, arg: str):
        """Go back to main prompt"""
        self.current_exploit = None
        self.prompt = "minesploit> "
        print("Back to main prompt")

    def emptyline(self) -> bool:
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Minesploit REPL")
    parser.add_argument(
        "-s",
        "--script",
        type=str,
        help="Run Python script file with framework imports",
    )
    parser.add_argument(
        "-c",
        "--command",
        type=str,
        help="Run REPL command(s) - string or .ms file",
    )
    args = parser.parse_args()

    shell = MinesploitShell()

    if args.script:
        # Execute as Python with framework imports
        namespace = _create_script_namespace()

        with open(args.script) as f:
            script_content = f.read()

        # Skip shebang line if present
        if script_content.startswith("#!/"):
            script_content = script_content.split("\n", 1)[1] if "\n" in script_content else ""

        exec(script_content, namespace)
    elif args.command:
        if args.command.endswith(".ms"):
            # Execute .ms file as REPL commands
            with open(args.command) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        print(f"minesploit> {line}")
                        shell.onecmd(line)
        else:
            # Execute single REPL command
            shell.onecmd(args.command)
    else:
        shell.cmdloop()


def _create_script_namespace() -> dict:
    """Create namespace for script execution with framework imports."""
    namespace: dict = {"__name__": "__main__"}

    # Import stdlib
    import asyncio
    import json
    import pathlib
    import random
    import time

    namespace.update(
        {
            "asyncio": asyncio,
            "json": json,
            "random": random,
            "time": time,
            "pathlib": pathlib,
        }
    )

    # Import framework core
    from minesploit import Minesploit
    from minesploit.database import ExploitDatabase as _ExploitDatabase
    from minesploit.framework import Exploit as _Exploit
    from minesploit.framework import Scanner as _Scanner

    namespace.update(
        {
            "minesploit": Minesploit,
            "Minesploit": Minesploit,
            "Exploit": _Exploit,
            "Scanner": _Scanner,
            "ExploitDatabase": _ExploitDatabase,
        }
    )

    # Import protocols (lazy-loaded via function to avoid import overhead)
    def _import_stratum():
        from minesploit.protocols.stratum.client import StratumClient
        from minesploit.protocols.stratum.server import StratumServer
        from minesploit.protocols.stratum.sniffer import StratumSniffer

        return {
            "StratumClient": StratumClient,
            "StratumServer": StratumServer,
            "StratumSniffer": StratumSniffer,
        }

    # Import utilities
    def _import_utils():
        from minesploit.utils.miner import CPUMiner, PoolConfig
        from minesploit.utils.scanner import MiningServiceScanner

        return {
            "MiningServiceScanner": MiningServiceScanner,
            "CPUMiner": CPUMiner,
            "PoolConfig": PoolConfig,
        }

    namespace.update(_import_stratum())
    namespace.update(_import_utils())

    # Add crypto utilities
    def _import_crypto():
        from minesploit.utils.crypto import decode_hex, encode_hex, merkle_root

        return {
            "decode_hex": decode_hex,
            "encode_hex": encode_hex,
            "merkle_root": merkle_root,
        }

    namespace.update(_import_crypto())

    return namespace


if __name__ == "__main__":
    main()
