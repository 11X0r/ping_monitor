import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, ClassVar, List


@dataclass(frozen=True)
class MonitorConfig:
    ping_adv_path: Path
    target: str = "8.8.8.8"
    packet_count: int = 10
    interval: float = 1.0
    log_level: str = "INFO"
    log_file: Optional[Path] = None

    SEARCH_PATHS: ClassVar[List[Path]] = [
        Path("/usr/local/bin/ping_adv"),
        Path("/usr/bin/ping_adv"),
        Path("./ping_adv")
    ]

    @classmethod
    def find_ping_adv(cls) -> Path:
        try:
            result = subprocess.run(
                ["which", "ping_adv"],
                capture_output=True,
                text=True,
                check=True
            )
            return Path(result.stdout.strip())
        except subprocess.SubprocessError:
            pass

        for path in cls.SEARCH_PATHS:
            if (path.exists() and
                    path.is_file() and
                    path.stat().st_mode & 0o111):
                return path

        raise FileNotFoundError(
            "ping_adv not found. Ensure it's installed in /usr/local/bin or /usr/bin"
        )

    @classmethod
    def load(cls):
        return cls(ping_adv_path=cls.find_ping_adv())
