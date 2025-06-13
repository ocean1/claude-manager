"""Pytest configuration and fixtures."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

from claude_manager.config import ClaudeConfigManager
from claude_manager.models import Project


@pytest.fixture
def sample_config_data() -> dict[str, Any]:
    """Sample configuration data for testing."""
    return {
        "numStartups": 10,
        "firstStartTime": "2024-01-01T00:00:00.000Z",
        "oauthAccount": {
            "emailAddress": "test@example.com",
            "organizationName": "Test Organization",
        },
        "projects": {
            "/home/user/project1": {
                "allowedTools": ["tool1", "tool2"],
                "history": [
                    {"display": "command1", "pastedContents": {}},
                    {"display": "command2", "pastedContents": {}},
                ],
                "mcpServers": {
                    "server1": {"url": "http://localhost:8080"},
                },
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": [],
                "enableAllProjectMcpServers": False,
                "hasTrustDialogAccepted": True,
                "ignorePatterns": ["*.pyc", "__pycache__"],
                "projectOnboardingSeenCount": 3,
                "hasClaudeMdExternalIncludesApproved": False,
                "hasClaudeMdExternalIncludesWarningShown": False,
                "dontCrawlDirectory": False,
                "mcpContextUris": [],
            },
            "/home/user/project2": {
                "allowedTools": [],
                "history": [],
                "mcpServers": {},
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": [],
                "enableAllProjectMcpServers": False,
                "hasTrustDialogAccepted": False,
                "ignorePatterns": [],
                "projectOnboardingSeenCount": 0,
                "hasClaudeMdExternalIncludesApproved": False,
                "hasClaudeMdExternalIncludesWarningShown": False,
                "dontCrawlDirectory": False,
                "mcpContextUris": [],
            },
            "/home/user/nonexistent": {
                "allowedTools": [],
                "history": [{"display": "old command", "pastedContents": {}}],
                "mcpServers": {},
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": [],
                "enableAllProjectMcpServers": False,
                "hasTrustDialogAccepted": False,
                "ignorePatterns": [],
                "projectOnboardingSeenCount": 1,
                "hasClaudeMdExternalIncludesApproved": False,
                "hasClaudeMdExternalIncludesWarningShown": False,
                "dontCrawlDirectory": False,
                "mcpContextUris": [],
            },
        },
    }


@pytest.fixture
def temp_config_file(sample_config_data: dict[str, Any]) -> Generator[Path, None, None]:
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_config_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def config_manager(temp_config_file: Path, tmp_path: Path) -> ClaudeConfigManager:
    """Create a configured ClaudeConfigManager instance with isolated backup directory."""
    manager = ClaudeConfigManager(str(temp_config_file))
    # Override the backup directory to use a temporary one
    manager.backup_dir = tmp_path / ".claude_backups"
    manager.backup_dir.mkdir(exist_ok=True)
    manager.load_config()
    return manager


@pytest.fixture
def sample_project() -> Project:
    """Create a sample Project instance."""
    return Project(
        path="/home/user/test_project",
        allowed_tools=["tool1", "tool2"],
        history=[
            {"display": "test command 1", "pastedContents": {}},
            {"display": "test command 2", "pastedContents": {}},
        ],
        mcp_servers={"test_server": {"url": "http://localhost:9999"}},
        has_trust_dialog_accepted=True,
        project_onboarding_seen_count=5,
    )


@pytest.fixture
def mock_home_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock the home directory for testing."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


@pytest.fixture
def isolated_config_manager(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, sample_config_data: dict[str, Any]
) -> ClaudeConfigManager:
    """Create a fully isolated ClaudeConfigManager for tests that create their own configs."""
    # Mock home directory
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)

    # Create config file
    config_path = home / ".claude.json"
    with open(config_path, "w") as f:
        json.dump(sample_config_data, f)

    # Create manager
    manager = ClaudeConfigManager()  # Uses default path
    manager.load_config()
    return manager
