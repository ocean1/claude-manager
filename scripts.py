#!/usr/bin/env python3  # noqa: EXE001
"""Task runner script for the project."""

import subprocess
import sys
from pathlib import Path

TASKS = {
    # Installation
    "install": ["pip", "install", "-e", "."],
    "install-dev": [
        ["pip", "install", "-e", ".[dev]"],
        ["pre-commit", "install"],
    ],
    # Testing
    "test": ["pytest"],
    "test-cov": ["pytest", "--cov=claude_manager", "--cov-report=html", "--cov-report=term"],
    "test-watch": ["pytest-watch"],
    # Linting and formatting
    "lint": [
        ["ruff", "check", "src", "tests"],
        ["mypy", "src"],
        ["black", "--check", "src", "tests"],
        ["isort", "--check-only", "src", "tests"],
    ],
    "format": [
        ["ruff", "check", "--fix", "src", "tests"],
        ["black", "src", "tests"],
        ["isort", "src", "tests"],
    ],
    "lint-fix": "format",  # Alias
    # Ruff specific commands
    "ruff": ["ruff", "check", "src", "tests"],
    "ruff-fix": ["ruff", "check", "--fix", "src", "tests"],
    "ruff-format": ["ruff", "format", "src", "tests"],
    # Type checking
    "typecheck": ["mypy", "src"],
    "mypy": "typecheck",  # Alias
    # Pre-commit
    "pre-commit": ["pre-commit", "run", "--all-files"],
    "pc": "pre-commit",  # Alias
    # Running
    "run": ["claude-manager"],
}


def run_command(cmd: list[str]) -> int:
    """Run a single command."""
    # Prepend 'uv run' to all commands to ensure they run in the virtual environment
    full_cmd = ["uv", "run", *cmd]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(full_cmd, cwd=Path(__file__).parent, check=False)
    return result.returncode


def run_task(task_name: str) -> int:
    """Run a task by name."""
    if task_name not in TASKS:
        print(f"Unknown task: {task_name}")
        print(f"Available tasks: {', '.join(sorted(TASKS.keys()))}")
        return 1

    task = TASKS[task_name]

    # Handle aliases
    if isinstance(task, str):
        return run_task(task)

    # Handle single command
    if isinstance(task[0], str):
        return run_command(task)

    # Handle multiple commands
    for cmd in task:
        ret = run_command(cmd)
        if ret != 0:
            return ret

    return 0


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts.py <task>")
        print(f"Available tasks: {', '.join(sorted(TASKS.keys()))}")
        return 1

    task_name = sys.argv[1]
    return run_task(task_name)


if __name__ == "__main__":
    sys.exit(main())
