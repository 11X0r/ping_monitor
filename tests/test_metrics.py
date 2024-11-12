from datetime import datetime, timedelta

from ping_monitor.models.metrics import PingMetrics


def test_metrics_creation_with_datetime():
    now = datetime.now()
    metrics = PingMetrics(
        timestamp=now,
        target="8.8.8.8",
        average_latency=10.0,
        jitter=1.0,
        packet_count=10,
        success_count=9
    )

    assert metrics.timestamp == now
    assert metrics.target == "8.8.8.8"
    assert metrics.average_latency == 10.0
    assert metrics.jitter == 1.0
    assert metrics.packet_count == 10
    assert metrics.success_count == 9


def test_metrics_creation_with_timestamp():
    now = datetime.now()
    timestamp = now.timestamp()

    metrics = PingMetrics(
        timestamp=timestamp,
        target="8.8.8.8",
        average_latency=10.0,
        jitter=1.0,
        packet_count=10,
        success_count=9
    )

    assert isinstance(metrics.timestamp, datetime)
    assert abs((metrics.timestamp - now).total_seconds()) < 1


def test_metrics_success_property():
    metrics_success = PingMetrics(
        timestamp=datetime.now(),
        target="8.8.8.8",
        average_latency=10.0,
        jitter=1.0,
        packet_count=10,
        success_count=2
    )
    assert metrics_success.success

    metrics_failure = PingMetrics(
        timestamp=datetime.now(),
        target="8.8.8.8",
        average_latency=10.0,
        jitter=1.0,
        packet_count=10,
        success_count=1
    )
    assert not metrics_failure.success


def test_metrics_packet_loss():
    metrics = PingMetrics(
        timestamp=datetime.now(),
        target="8.8.8.8",
        average_latency=10.0,
        jitter=1.0,
        packet_count=10,
        success_count=8
    )
    assert metrics.packet_loss == 20.0


def test_metrics_age():
    timestamp = datetime.now() - timedelta(seconds=30)
    metrics = PingMetrics(
        timestamp=timestamp,
        target="8.8.8.8",
        average_latency=10.0,
        jitter=1.0,
        packet_count=10,
        success_count=8
    )

    assert 29 <= metrics.age <= 31


def test_metrics_string_representation():
    metrics = PingMetrics(
        timestamp=datetime.now(),
        target="8.8.8.8",
        average_latency=10.5,
        jitter=1.2,
        packet_count=10,
        success_count=9
    )

    assert (str(metrics) == "[8.8.8.8] Test Result: Average Latency 10.50ms, Jitter 1.20ms (9 results)")

    failed_metrics = PingMetrics(
        timestamp=datetime.now(),
        target="8.8.8.8",
        average_latency=0.0,
        jitter=0.0,
        packet_count=10,
        success_count=1
    )
    assert str(failed_metrics) == "[8.8.8.8] Test Failed"
