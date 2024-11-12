class PingMonitorError(Exception):
    """Base exception for all ping monitor errors."""


class ConfigurationError(PingMonitorError):
    """Raised when configuration is invalid."""


class ExecutionError(PingMonitorError):
    """Raised when ping_adv execution fails."""


class ValidationError(PingMonitorError):
    """Raised when input validation fails."""
