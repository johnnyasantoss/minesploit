"""Minesploit - Bitcoin Mining Security Research Framework"""

__version__ = "0.1.0"
__author__ = "Minesploit Contributors"

from minesploit.database import ExploitDatabase
from minesploit.framework import Exploit, Scanner

__all__ = ["Exploit", "Scanner", "ExploitDatabase", "__version__"]


class Minesploit:
    def __init__(self):
        self.exploits = ExploitDatabase()

    def list_exploits(self, category: str | None = None):
        return self.exploits.list(category)

    def get_exploit(self, name: str):
        return self.exploits.get(name)

    def search_exploits(self, query: str):
        return self.exploits.search(query)
