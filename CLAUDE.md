# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Manager is a Python terminal UI application for managing Claude Code projects and configurations stored in `.claude.json` files. It provides features for project management, MCP server configuration, history management, and automatic backups.

## Essential Commands

### Task Runner Setup

This project uses `uv` with a custom task runner script (`scripts.py`). All commands can be run with `uv run python scripts.py <command>`.

### Development Setup
```bash
# Install development dependencies with pre-commit hooks
uv run python scripts.py install-dev

# Or manually
uv venv
uv pip install -e ".[dev]"
uv run pre-commit install
```

### Running the Application
```bash
# Run the application
uv run python scripts.py run

# Or directly
uv run claude-manager

# With custom config file
uv run claude-manager -c /path/to/custom/.claude.json
```

### Testing
```bash
# Run all tests
uv run python scripts.py test

# Run tests with coverage report
uv run python scripts.py test-cov

# Run a specific test file
uv run pytest tests/test_models.py

# Run a single test
uv run pytest tests/test_models.py::TestProject::test_from_dict
```

### Code Quality with Ruff
```bash
# Run all linters and type checking
uv run python scripts.py lint

# Auto-format code (fixes issues automatically)
uv run python scripts.py format

# Ruff-specific commands
uv run python scripts.py ruff        # Check with ruff
uv run python scripts.py ruff-fix    # Fix issues with ruff
uv run python scripts.py ruff-format # Format with ruff

# Type checking
uv run python scripts.py typecheck   # or 'mypy'

# Run pre-commit hooks on all files
uv run python scripts.py pre-commit  # or 'pc'
```

### Building and Packaging
```bash
# Build distribution packages
./build.sh

# Clean build artifacts
./clean.sh
```

### Available Commands Summary

| Command | Description |
|---------|-------------|
| `install` | Install the package |
| `install-dev` | Install with development dependencies and pre-commit hooks |
| `test` | Run all tests |
| `test-cov` | Run tests with coverage report |
| `test-watch` | Run tests in watch mode |
| `lint` | Run all linting checks (ruff, mypy, black, isort) |
| `format` | Auto-format code with all formatters |
| `lint-fix` | Alias for format |
| `ruff` | Run ruff linter |
| `ruff-fix` | Fix issues with ruff |
| `ruff-format` | Format code with ruff |
| `typecheck`/`mypy` | Run type checking with mypy |
| `pre-commit`/`pc` | Run pre-commit hooks on all files |
| `run` | Run the claude-manager application |

### Shell Scripts
| Script | Description |
|--------|-------------|
| `./clean.sh` | Clean all build artifacts |
| `./build.sh` | Clean and build distribution packages |

## Architecture Overview

### Core Components

1. **CLI Entry Point** (`src/claude_manager/cli.py`):
   - Uses Click for command-line parsing
   - Handles config file location and debug flags
   - Initializes the UI application

2. **Configuration Management** (`src/claude_manager/config.py`):
   - Reads/writes `.claude.json` files
   - Implements automatic backup system
   - Validates JSON structure before saving
   - Uses atomic writes to prevent corruption

3. **Data Models** (`src/claude_manager/models.py`):
   - `Project` class represents individual projects
   - Handles serialization/deserialization
   - Provides analysis methods for project health

4. **UI System**:
   - `ui.py`: Main application logic and menu system
   - `tui.py`: Rich terminal UI components (tables, panels)
   - `simple_ui.py`: Fallback UI for environments without Rich support
   - `ui_helpers.py`: Shared UI utilities

### Key Design Patterns

- **Backup System**: Automatically creates timestamped backups before any destructive operation
- **Type Safety**: Uses mypy in strict mode with comprehensive type annotations
- **Error Handling**: Comprehensive exception handling with user-friendly error messages
- **Modular Design**: Clear separation between UI, business logic, and data models

### Configuration File Structure

The tool manages `.claude.json` files with this structure:
```json
{
  "projects": {
    "/path/to/project": {
      "allowedTools": [],
      "history": [],
      "mcpServers": {},
      "enabledMcpjsonServers": [],
      "disabledMcpjsonServers": [],
      "enableAllProjectMcpServers": false,
      "hasTrustDialogAccepted": false,
      "ignorePatterns": [],
      "projectOnboardingSeenCount": 0,
      "hasClaudeMdExternalIncludesApproved": false,
      "hasClaudeMdExternalIncludesWarningShown": false,
      "dontCrawlDirectory": false,
      "mcpContextUris": []
    }
  }
}
```

### Testing Strategy

- Unit tests for all core components
- Integration tests for file operations
- Mock-based testing for UI components
- Coverage target: 90%+
- Test files mirror source structure in `tests/` directory