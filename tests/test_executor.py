import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest

from ping_monitor.core.executor import PingExecutor


@pytest.fixture
def executor(tmp_path: Path) -> PingExecutor:
    dummy_ping = tmp_path / "ping_adv"
    dummy_ping.touch(mode=0o755)
    return PingExecutor(dummy_ping)


def test_executor_successful_ping_ms(executor, mocker):
    mock_output = "[8.8.8.8] Test Result: Average Latency 20ms, Jitter 1ms (10 results)"
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = Mock(
        stdout=mock_output,
        stderr="",
        returncode=0
    )

    result = executor.execute("8.8.8.8", 10, 1.0)

    assert result.success
    assert result.average_latency == 20.0
    assert result.jitter == 1.0
    assert result.success_count == 10
    assert result.error_message is None


def test_executor_successful_ping_ns(executor, mocker):
    mock_output = "[8.8.8.8] Test Result: Average Latency 20ms, Jitter 935529ns (10 results)"
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = Mock(
        stdout=mock_output,
        stderr="",
        returncode=0
    )

    result = executor.execute("8.8.8.8", 10, 1.0)

    assert result.success
    assert result.average_latency == 20.0
    assert abs(result.jitter - 0.935529) < 0.0001
    assert result.success_count == 10
    assert result.error_message is None


def test_executor_timeout(executor, mocker):
    mock_run = mocker.patch('subprocess.run')
    mock_run.side_effect = subprocess.TimeoutExpired(
        cmd=["ping_adv", "8.8.8.8", "10", "1.0"],
        timeout=15
    )

    result = executor.execute("8.8.8.8", 10, 1.0)

    assert not result.success
    assert result.success_count == 0
    assert "timed out" in result.error_message.lower()
    assert result.average_latency == 0.0
    assert result.jitter == 0.0


def test_executor_invalid_output_format(executor, mocker):
    mock_output = "Invalid output format"
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = Mock(
        stdout=mock_output,
        stderr="",
        returncode=0
    )

    result = executor.execute("8.8.8.8", 10, 1.0)

    assert not result.success
    assert result.success_count == 0
    assert "invalid output format" in result.error_message.lower()
    assert result.average_latency == 0.0
    assert result.jitter == 0.0


def test_executor_malformed_numbers(executor, mocker):
    mock_output = "[8.8.8.8] Test Result: Average Latency invalid_ms"
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = Mock(stdout=mock_output, returncode=0)

    result = executor.execute("8.8.8.8", 10, 1.0)
    assert not result.success
    assert "Invalid output format" in result.error_message


def test_executor_validation(tmp_path):
    with pytest.raises(FileNotFoundError):
        PingExecutor(tmp_path / "nonexistent")

    non_exec = tmp_path / "non_executable"
    non_exec.touch(mode=0o644)
    with pytest.raises(PermissionError):
        PingExecutor(non_exec)


def test_executor_command_formatting(executor, mocker):
    mock_run = mocker.patch('subprocess.run')
    mock_run.return_value = Mock(
        stdout="[8.8.8.8] Test Result: Average Latency 20ms, Jitter 1ms (10 results)",
        stderr="",
        returncode=0
    )

    executor.execute("8.8.8.8", 10, 1.5)
    cmd_args = mock_run.call_args[0][0]
    assert cmd_args[3] == "1.5"
    assert cmd_args[2] == "10"


def test_executor_error_conditions(executor, mocker):
    mock_run = mocker.patch('subprocess.run')

    mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
    result = executor.execute("8.8.8.8", 10, 1.0)
    assert not result.success
    assert "invalid output format" in result.error_message.lower()

    mock_run.return_value = Mock(
        stdout="[8.8.8.8] Test Result: Average Latency 20ms",
        stderr="",
        returncode=0
    )
    result = executor.execute("8.8.8.8", 10, 1.0)
    assert not result.success
    assert "invalid output format" in result.error_message.lower()
