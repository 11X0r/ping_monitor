from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import Mock

import pytest

from ping_monitor.core.monitor import ConnectionMonitor
from ping_monitor.models.metrics import PingMetrics
from ping_monitor.utils.config import MonitorConfig


@pytest.fixture
def mock_ping_result() -> PingMetrics:
    return PingMetrics(
        timestamp=datetime.now(),
        target="8.8.8.8",
        average_latency=10.0,
        jitter=1.0,
        packet_count=10,
        success_count=10
    )


@pytest.fixture
def mock_executor(mock_ping_result) -> Mock:
    mock = Mock()
    mock.execute.return_value = mock_ping_result
    return mock


@pytest.fixture
def sample_config(tmp_path) -> MonitorConfig:
    dummy_ping = tmp_path / "ping_adv"
    dummy_ping.touch(mode=0o755)
    return MonitorConfig(
        ping_adv_path=dummy_ping,
        target="8.8.8.8",
        packet_count=10,
        interval=1.0,
        log_level="DEBUG"
    )


@pytest.fixture
async def monitor(sample_config, mock_executor) -> AsyncGenerator[ConnectionMonitor, None]:
    monitor = ConnectionMonitor(sample_config)
    monitor.executor = mock_executor
    yield monitor
    if monitor.is_running:
        await monitor.stop()
