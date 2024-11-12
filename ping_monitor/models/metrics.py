from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PingMetrics:
    timestamp: datetime
    target: str
    average_latency: float
    jitter: float
    packet_count: int
    success_count: int
    error_message: Optional[str] = None

    SUCCESS_THRESHOLD: int = 2

    def __post_init__(self) -> None:
        if isinstance(self.timestamp, (int, float)):
            object.__setattr__(
                self, 'timestamp',
                datetime.fromtimestamp(self.timestamp)
            )

    @property
    def success(self) -> bool:
        return self.success_count >= self.SUCCESS_THRESHOLD

    @property
    def packet_loss(self) -> float:
        return (self.packet_count - self.success_count) / self.packet_count * 100

    @property
    def age(self) -> float:
        return (datetime.now() - self.timestamp).total_seconds()

    def __str__(self) -> str:
        if not self.success:
            return f"[{self.target}] Test Failed"

        return (
            f"[{self.target}] Test Result: "
            f"Average Latency {self.average_latency:.2f}ms, "
            f"Jitter {self.jitter:.2f}ms "
            f"({self.success_count} results)"
        )
