from pathlib import Path

from ping_monitor.models.exceptions import ValidationError


def validate_ping_adv(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"ping_adv not found at {path}")
    if not path.is_file():
        raise ValidationError(f"{path} is not a file")
    if not path.stat().st_mode & 0o111:
        raise ValidationError(f"{path} is not executable")


def validate_target(target: str) -> None:
    # Simple validation for demonstration
    parts = target.split(".")
    if len(parts) != 4:
        raise ValidationError("Invalid IP address format")
    try:
        if not all(0 <= int(p) <= 255 for p in parts):
            raise ValidationError("IP address parts must be between 0 and 255")
    except ValueError as e:
        raise ValidationError("Invalid IP address format") from e


def validate_packet_count(count: int) -> None:
    if not 2 <= count <= 50:
        raise ValidationError("Packet count must be between 2 and 50")


def validate_interval(interval: float) -> None:
    if not 0.1 <= interval <= 10.0:
        raise ValidationError("Interval must be between 0.1 and 10.0 ms")
