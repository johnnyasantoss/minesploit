"""Generic logging utility for minesploit framework"""

import sys
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Logger:
    def __init__(self, name: str = "MINESPLOIT", verbosity: str = "INFO"):
        self.name = name
        self._level = LogLevel(verbosity.upper()) if verbosity else LogLevel.INFO

    @property
    def verbosity(self) -> str:
        return self._level.value

    @verbosity.setter
    def verbosity(self, value: str) -> None:
        self._level = LogLevel(value.upper())

    def _should_log(self, level: LogLevel) -> bool:
        level_order = [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.SUCCESS,
            LogLevel.WARNING,
            LogLevel.ERROR,
        ]
        return level_order.index(level) >= level_order.index(self._level)

    def _get_color(self, level: LogLevel) -> str:
        colors = {
            LogLevel.DEBUG: "\033[97m",
            LogLevel.INFO: "\033[94m",
            LogLevel.SUCCESS: "\033[92m",
            LogLevel.WARNING: "\033[93m",
            LogLevel.ERROR: "\033[91m",
        }
        return colors.get(level, "\033[97m")

    def _hexdump(self, data: bytes, prefix: str = "        ") -> str:
        lines = []
        for i in range(0, len(data), 16):
            chunk = data[i : i + 16]
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            hex_part = hex_part.ljust(48)
            lines.append(f"{prefix}{hex_part} | {ascii_part}")
        return "\n".join(lines)

    def log(self, level: str, message: str, data: bytes | None = None, direction: str = "") -> None:
        level_enum = LogLevel(level.upper())
        if not self._should_log(level_enum):
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        reset = "\033[0m"
        color = self._get_color(level_enum)

        if direction == "SEND":
            prefix = f"[{self.name}] [{timestamp}] \033[95m>>> SEND{reset}"
        elif direction == "RECV":
            prefix = f"[{self.name}] [{timestamp}] \033[95m<<< RECV{reset}"
        else:
            prefix = f"[{self.name}] [{timestamp}]"

        print(f"{prefix} {color}{level}{reset}: {message}")

        if data:
            print(self._hexdump(data, prefix + " "))
        sys.stdout.flush()

    def debug(self, message: str) -> None:
        self.log("DEBUG", message)

    def info(self, message: str) -> None:
        self.log("INFO", message)

    def success(self, message: str) -> None:
        self.log("SUCCESS", message)

    def warning(self, message: str) -> None:
        self.log("WARNING", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)

    def debug_hex(self, message: str, data: bytes) -> None:
        if self._should_log(LogLevel.DEBUG):
            self.log("DEBUG", message, data)

    def info_hex(self, message: str, data: bytes) -> None:
        if self._should_log(LogLevel.INFO):
            self.log("INFO", message, data)

    def send(self, message: str, data: bytes) -> None:
        self.log("INFO", message, data, "SEND")

    def recv(self, message: str, data: bytes) -> None:
        self.log("INFO", message, data, "RECV")
