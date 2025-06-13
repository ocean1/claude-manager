"""UI helper functions for Claude Manager."""

from __future__ import annotations

from typing import Any

import questionary
from rich.prompt import Confirm as RichConfirm
from rich.prompt import Prompt as RichPrompt


def safe_select(message: str, choices: list[Any], **kwargs: Any) -> Any | None:
    """Run a select prompt, letting CTRL+C propagate for app exit.

    Args:
        message: The prompt message
        choices: List of choices
        **kwargs: Additional arguments for questionary.select

    Returns:
        Selected choice or None if cancelled with ESC
    """
    return questionary.select(message, choices=choices, **kwargs).ask()


def safe_checkbox(message: str, choices: list[Any], **kwargs: Any) -> list[Any] | None:
    """Run a checkbox prompt, letting CTRL+C propagate for app exit.

    Args:
        message: The prompt message
        choices: List of choices
        **kwargs: Additional arguments for questionary.checkbox

    Returns:
        List of selected choices or None if cancelled with ESC
    """
    return questionary.checkbox(message, choices=choices, **kwargs).ask()  # type: ignore[no-any-return]


def safe_autocomplete(message: str, choices: list[str], **kwargs: Any) -> str | None:
    """Run an autocomplete prompt, letting CTRL+C propagate for app exit.

    Args:
        message: The prompt message
        choices: List of choices for autocomplete
        **kwargs: Additional arguments for questionary.autocomplete

    Returns:
        Selected choice or None if cancelled with ESC
    """
    return questionary.autocomplete(message, choices=choices, **kwargs).ask()  # type: ignore[no-any-return]


# Export convenience names
Prompt = RichPrompt
Confirm = RichConfirm


def wait_for_enter(console: Any, message: str = "Press Enter to continue...") -> None:
    """Wait for user to press Enter.

    Args:
        console: Rich console instance
        message: Message to display
    """
    try:
        console.input(f"\n[dim]{message}[/dim]")
    except EOFError:
        # Handle EOF (Ctrl+D)
        pass
