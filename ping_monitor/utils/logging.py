import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler


@dataclass(frozen=True)
class LogConfig:
    level: str = "INFO"
    log_file: Optional[Path] = None
    rich_output: bool = True
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(config: LogConfig) -> None:
    handlers = []

    if config.rich_output:
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,
            show_path=False,
            tracebacks_extra_lines=3,
            tracebacks_show_locals=True,
        )
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(config.format))
    handlers.append(console_handler)

    if config.log_file:
        config.log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(logging.Formatter(config.format))
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, config.level.upper()),
        handlers=handlers,
        force=True
    )

    logger = logging.getLogger(__name__)
    logger.debug(
        "Logging configured: level=%s, rich_output=%s, log_file=%s",
        config.level,
        config.rich_output,
        config.log_file
    )
