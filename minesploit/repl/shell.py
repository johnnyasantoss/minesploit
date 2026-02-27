"""Minesploit REPL shell"""

import cmd
import sys
from typing import Any


class MinesploitShell(cmd.Cmd):
    intro = """╔═══════════════════════════════════════════════════════════╗
║           Minesploit - Bitcoin Mining Security Framework      ║
║                  Security Research for White Hats            ║
╠═══════════════════════════════════════════════════════════╣
║ Type 'help' for commands, 'list exploits' to see available ║
║ Type 'exit' or 'quit' to leave                            ║
╚═══════════════════════════════════════════════════════════╝
"""
    prompt = "minesploit> "
    current_exploit: Any = None

    def __init__(self):
        super().__init__()
        self.exploits: dict[str, Any] = {}
        self.target: str | None = None
        self.port: int | None = None

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
    MinesploitShell().cmdloop()


if __name__ == "__main__":
    main()
