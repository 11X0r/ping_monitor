import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Match, Final, ClassVar

from ping_monitor.models.metrics import PingMetrics
from ping_monitor.utils.logging import LogConfig, setup_logging

setup_logging(LogConfig())
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PingExecutor:
    ping_adv_path: Path

    PATTERN: ClassVar[str] = (
        r'\[(.*?)\] Test Result: '
        r'Average Latency (\d+)ms, '
        r'Jitter (\d+)(ms|ns) '
        r'\((\d+) results\)'
    )
    NS_TO_MS: Final[float] = 1_000_000.0
    TIMEOUT_BUFFER: Final[int] = 5

    def __post_init__(self) -> None:
        if not self.ping_adv_path.is_file():
            raise FileNotFoundError(f"ping_adv not found: {self.ping_adv_path}")
        if not self.ping_adv_path.stat().st_mode & 0o111:
            raise PermissionError(f"ping_adv not executable: {self.ping_adv_path}")
        logger.debug("Using ping_adv at: %s", self.ping_adv_path)

    def execute(self, target: str, packet_count: int, interval: float) -> PingMetrics:
        try:
            cmd = [str(self.ping_adv_path), target, str(packet_count), str(interval)]
            logger.debug("Running command: %s", ' '.join(cmd))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=packet_count * interval + self.TIMEOUT_BUFFER,
                check=False
            )

            if result.returncode != 0:
                return self._as_error(target, packet_count, result.stderr.strip())

            metrics = self._parse_output(result.stdout.strip(), target, packet_count)
            logger.debug("Parsed metrics: %s", metrics)
            return metrics

        except subprocess.TimeoutExpired:
            return self._as_error(target, packet_count, "Command timed out")
        except Exception as e:
            logger.exception("Unexpected error")
            return self._as_error(target, packet_count, str(e))

    def _parse_output(self, output: str, target: str, packet_count: int) -> PingMetrics:
        match = re.search(self.PATTERN, output)
        if not match:
            logger.error("Invalid output format: %s", output)
            return self._as_error(target, packet_count, "Invalid output format")

        try:
            latency = float(match.group(2))
            jitter = self._parse_jitter(match)
            success_count = int(match.group(5))

            return PingMetrics(
                timestamp=datetime.now(),
                target=target,
                average_latency=latency,
                jitter=jitter,
                packet_count=packet_count,
                success_count=success_count
            )
        except ValueError as e:
            logger.error("Failed to parse values: %s", e)
            return self._as_error(target, packet_count, "Invalid output format")

    def _parse_jitter(self, match: Match[str]) -> float:
        jitter = float(match.group(3))
        return jitter / self.NS_TO_MS if match.group(4) == 'ns' else jitter

    def _as_error(self, target: str, packet_count: int, error: str) -> PingMetrics:
        return PingMetrics(
            timestamp=datetime.now(),
            target=target,
            average_latency=0.0,
            jitter=0.0,
            packet_count=packet_count,
            success_count=0,
            error_message=error
        )
