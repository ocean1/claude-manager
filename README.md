# Claude Manager

[![CI](https://github.com/ocean1/claude-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/ocean1/claude-manager/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/claude-manager.svg)](https://badge.fury.io/py/claude-manager)
[![Python versions](https://img.shields.io/pypi/pyversions/claude-manager.svg)](https://pypi.org/project/claude-manager/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python terminal UI application for managing Claude Code projects and configurations stored in `.claude.json`.

## Features

### Project Management
- **List Projects**: View all projects with details including history count, MCP servers, and directory existence status
- **Analyze Projects**: Identify issues like non-existent directories, unused projects, and large history entries
- **Remove Projects**: Smart removal with multiple strategies (non-existent, no history, manual selection)
- **Project Details**: Deep dive into specific project configurations

### MCP Server Management
- View and manage MCP (Model Context Protocol) server configurations
- Enable/disable MCP servers per project
- View detailed server configurations

### History Management
- Clear all history across projects
- Clear history for specific projects
- Keep only recent entries (configurable retention)

### Backup & Safety
- Automatic backup creation before any destructive operation
- Timestamped backups with configurable retention
- Restore from any previous backup
- Validate JSON integrity before saving

### Configuration
- Support for custom config file locations (default: `~/.claude.json`)
- Rich terminal UI with intuitive navigation
- Comprehensive error handling and logging

## Installation

### Using pip
```bash
pip install claude-manager
```

### Using uv (recommended)
```bash
uv pip install claude-manager
```

### From source
```bash
git clone https://github.com/ocean1/claude-manager.git
cd claude-manager
uv pip install -e .
```

## Usage

### Basic Usage
```bash
# Run with default config location (~/.claude.json)
claude-manager

# Use custom config file
claude-manager -c /path/to/custom/.claude.json

# Enable debug logging
claude-manager --debug

# Skip automatic backups (not recommended)
claude-manager --no-backup
```

### Main Menu Options

1. **List Projects**: Browse all projects with summary information
2. **Analyze Projects**: Get insights and recommendations about your projects
3. **Remove Projects**: Clean up unused or problematic projects
4. **Manage MCP Servers**: Configure Model Context Protocol servers
5. **Clear History**: Manage project history entries
6. **Backup Management**: Create, restore, and manage configuration backups
7. **Configuration Info**: View statistics and configuration details

## Development

### Setup Development Environment

Using uv (recommended):
```bash
# Clone the repository
git clone https://github.com/ocean1/claude-manager.git
cd claude-manager

# Install development dependencies with pre-commit hooks
uv run python scripts.py install-dev
```

Or manually:
```bash
# Create virtual environment and install dependencies
uv venv
uv pip install -e ".[dev]"

# Install pre-commit hooks
uv run pre-commit install
```

### Development Commands

All development commands are available through the task runner:

```bash
# Run all tests
uv run python scripts.py test

# Run tests with coverage
uv run python scripts.py test-cov

# Run tests in watch mode (re-runs on file changes)
uv run python scripts.py test-watch

# Run all linters and type checking
uv run python scripts.py lint

# Auto-format code
uv run python scripts.py format

# Run specific tools
uv run python scripts.py ruff        # Run ruff linter
uv run python scripts.py ruff-fix    # Fix ruff issues
uv run python scripts.py mypy        # Run type checking
uv run python scripts.py black       # Run black formatter
uv run python scripts.py isort       # Run import sorter

# Run pre-commit hooks
uv run python scripts.py pre-commit

# Clean build artifacts
./clean.sh

# Build distribution packages
./build.sh
```

### Available Commands

| Command | Description |
|---------|-------------|
| `install` | Install the package |
| `install-dev` | Install with development dependencies and pre-commit hooks |
| `test` | Run all tests |
| `test-cov` | Run tests with coverage report |
| `test-watch` | Run tests in watch mode |
| `lint` | Run all linting checks |
| `format` | Auto-format code |
| `ruff` | Run ruff linter |
| `ruff-fix` | Fix ruff issues automatically |
| `ruff-format` | Format code with ruff |
| `mypy` | Run type checking |
| `black` | Run black formatter |
| `isort` | Sort imports |
| `pre-commit` | Run pre-commit hooks |
| `run` | Run the claude-manager application |

## Configuration Structure

The tool manages the following aspects of `.claude.json`:

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
  },
  // ... other configuration fields
}
```

## Safety Features

- **Automatic Backups**: Creates timestamped backups before any modification
- **Validation**: Validates JSON structure before saving
- **Atomic Writes**: Uses temporary files to prevent corruption
- **Confirmation Prompts**: Requires confirmation for destructive operations
- **Backup Retention**: Keeps last 10 backups by default

## Backup Location

Backups are stored in: `~/.claude_backups/claude_YYYYMMDD_HHMMSS.json`

## Architecture

The codebase is organized into modular components:

- `claude_manager.models`: Data models (Project class)
- `claude_manager.config`: Configuration file operations  
- `claude_manager.tui`: Terminal UI implementation using Textual
- `claude_manager.simple_ui`: Fallback UI for environments without Textual support
- `claude_manager.cli`: Command-line interface
- `claude_manager.utils`: Utility functions and signal handling

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Textual](https://github.com/Textualize/textual) for advanced terminal UI
- Uses [Rich](https://github.com/Textualize/rich) for beautiful terminal output
- Fallback UI uses [Questionary](https://github.com/tmbo/questionary) for interactive prompts
- Linting with [Ruff](https://github.com/astral-sh/ruff) for fast, comprehensive code quality checks
- Packaged with modern Python tools and best practices
