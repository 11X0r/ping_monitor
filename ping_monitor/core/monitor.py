import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Final

from ping_monitor.core.executor import PingExecutor
from ping_monitor.models.metrics import PingMetrics
from ping_monitor.utils.config import MonitorConfig
from ping_monitor.utils.logging import LogConfig, setup_logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMonitor:
    _running: bool = field(default=False, init=False)
    _history: List[PingMetrics] = field(default_factory=list, init=False)
    _last_metrics: Optional[PingMetrics] = field(default=None, init=False)
    _test_mode: bool = field(default=False, init=False)
    config: MonitorConfig
    executor: PingExecutor = field(init=False)
    log_config: LogConfig = field(default=LogConfig())

    CHECK_INTERVAL: Final[int] = 60
    HISTORY_HOURS: Final[int] = 1

    def __post_init__(self) -> None:
        setup_logging(self.log_config)
        self.executor = PingExecutor(self.config.ping_adv_path)
        logger.info(
            "Initialised monitor with target: %s, interval: %d, packet_count: %d",
            self.config.target,
            self.config.interval,
            self.config.packet_count
        )

    async def start(self) -> None:
        if self._running:
            logger.warning("Monitor already running")
            return

        self._running = True
        logger.info("Starting connection monitoring")

        try:
            await self._monitor_loop()
        except Exception as e:
            logger.exception("Monitoring failed: %s", str(e))
            self._running = False
            raise

    async def stop(self) -> None:
        if self._running:
            self._running = False
            logger.info("Stopping connection monitoring")

    async def _monitor_loop(self) -> None:
        while self._running:
            try:
                metrics = await self._execute_ping()
                await self._process_metrics(metrics)

                if self._test_mode:
                    break

                await asyncio.sleep(self.CHECK_INTERVAL)
            except Exception as e:
                logger.error("Error in monitoring loop: %s", str(e))
                if not self._test_mode:
                    raise

    async def _execute_ping(self) -> PingMetrics:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.executor.execute,
            self.config.target,
            self.config.packet_count,
            self.config.interval
        )

    async def _process_metrics(self, metrics: PingMetrics) -> None:
        self._history.append(metrics)
        self._trim_history()
        self._last_metrics = metrics

        if not metrics.success:
            logger.warning("[Connection unavailable]")
            return

        logger.info(
            "[Connection average latency %.2f, Jitter %.2f]",
            metrics.average_latency,
            metrics.jitter
        )

        if (self._history and len(self._history) > 1 and
                (abs(metrics.average_latency - self._history[-2].average_latency) > 5 or
                 abs(metrics.jitter - self._history[-2].jitter) > 2)):
            logger.info(
                "Significant change detected - Previous: %.2f/%.2f, Current: %.2f/%.2f",
                self._history[-2].average_latency,
                self._history[-2].jitter,
                metrics.average_latency,
                metrics.jitter
            )

    def _trim_history(self) -> None:
        if not self._history:
            return

        cutoff = datetime.now() - timedelta(hours=self.HISTORY_HOURS)
        self._history = [m for m in self._history if m.timestamp > cutoff]
        logger.debug("History trimmed to %d entries", len(self._history))

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *_) -> None:
        await self.stop()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def history(self) -> List[PingMetrics]:
        return self._history.copy()

    @property
    def last_metrics(self) -> Optional[PingMetrics]:
        return self._last_metrics

    def get_stats(self) -> dict:
        if not self._history:
            return {}

        successful = [m for m in self._history if m.success]
        if not successful:
            return {"error": "No successful measurements"}

        latencies = [m.average_latency for m in successful]
        return {
            "min_latency": min(latencies),
            "max_latency": max(latencies),
            "avg_latency": sum(latencies) / len(latencies),
            "measurements": len(self._history),
            "successful": len(successful),
            "success_rate": len(successful) / len(self._history) * 100
        }
