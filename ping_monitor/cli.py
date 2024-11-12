import asyncio
import logging
import signal

import typer
from rich.console import Console

from ping_monitor.core.monitor import ConnectionMonitor
from ping_monitor.utils.config import MonitorConfig

app = typer.Typer(help="Monitor network connection quality")
console = Console()


def setup_logging(verbose: bool) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )


def handle_signals(monitor: ConnectionMonitor) -> None:
    """Setup signal handlers."""

    def shutdown():
        asyncio.create_task(monitor.stop())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(sig, shutdown)


@app.command()
def main(
        verbose: bool = typer.Option(
            False,
            "--verbose", "-v",
            help="Enable verbose output"
        )
) -> None:
    """Monitor network connection quality."""
    try:
        setup_logging(verbose)
        config = MonitorConfig.load()
        monitor = ConnectionMonitor(config)

        async def run():
            async with monitor:
                handle_signals(monitor)
                while monitor.is_running:
                    await asyncio.sleep(1)

        asyncio.run(run())

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass
    except Exception:
        console.print_exception()
        raise typer.Exit(1)


if __name__ == "__main__":
    app()