"""Utility functions for Claude Manager."""

from __future__ import annotations

import signal
import sys
from typing import Any

from rich.console import Console

console = Console()


class SignalHandler:
    """Handle system signals gracefully."""

    def __init__(self) -> None:
        self.original_sigint = signal.getsignal(signal.SIGINT)
        self.exit_requested = False

    def __enter__(self) -> SignalHandler:
        """Set up signal handlers."""
        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Restore original signal handlers."""
        signal.signal(signal.SIGINT, self.original_sigint)

    def _handle_sigint(self, signum: int, frame: Any) -> None:
        """Handle SIGINT (Ctrl+C)."""
        self.exit_requested = True
        # Clean exit
        sys.exit(0)

    def _handle_sigterm(self, signum: int, frame: Any) -> None:
        """Handle SIGTERM."""
        self.exit_requested = True
        sys.exit(0)
