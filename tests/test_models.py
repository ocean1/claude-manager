"""Tests for the models module."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from claude_manager.models import Project

if TYPE_CHECKING:
    from pathlib import Path


class TestProject:
    """Test the Project model."""

    def test_project_creation(self, sample_project: Project) -> None:
        """Test creating a Project instance."""
        assert sample_project.path == "/home/user/test_project"
        assert sample_project.allowed_tools == ["tool1", "tool2"]
        assert len(sample_project.history) == 2
        assert sample_project.has_trust_dialog_accepted is True

    def test_history_count(self, sample_project: Project) -> None:
        """Test history_count property."""
        assert sample_project.history_count == 2

        # Add more history
        sample_project.history.append({"display": "new command", "pastedContents": {}})
        assert sample_project.history_count == 3

    def test_last_accessed(self, sample_project: Project) -> None:
        """Test last_accessed property."""
        assert sample_project.last_accessed == "test command 2"

        # Test with empty history
        sample_project.history = []
        assert sample_project.last_accessed is None

    def test_directory_exists(self, tmp_path: Path) -> None:
        """Test directory_exists property."""
        # Create a project with existing directory
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        project1 = Project(path=str(existing_dir))
        assert project1.directory_exists is True

        # Create a project with non-existing directory
        project2 = Project(path=str(tmp_path / "nonexistent"))
        assert project2.directory_exists is False

    def test_get_size_estimate(self, sample_project: Project) -> None:
        """Test get_size_estimate method."""
        size = sample_project.get_size_estimate()
        assert size > 0

        # Size should increase with more data
        original_size = size
        sample_project.history.extend(
            [{"display": f"command {i}", "pastedContents": {}} for i in range(10)]
        )
        new_size = sample_project.get_size_estimate()
        assert new_size > original_size

    def test_to_dict(self, sample_project: Project) -> None:
        """Test to_dict method."""
        data = sample_project.to_dict()

        assert data["allowedTools"] == ["tool1", "tool2"]
        assert len(data["history"]) == 2
        assert data["mcpServers"] == {"test_server": {"url": "http://localhost:9999"}}
        assert data["hasTrustDialogAccepted"] is True
        assert data["projectOnboardingSeenCount"] == 5

        # Ensure it's JSON serializable
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

    def test_from_dict(self) -> None:
        """Test from_dict class method."""
        data = {
            "allowedTools": ["tool1"],
            "history": [{"display": "cmd1", "pastedContents": {}}],
            "mcpServers": {"server1": {"config": "value"}},
            "hasTrustDialogAccepted": True,
            "projectOnboardingSeenCount": 2,
            "enableAllProjectMcpServers": True,
            "ignorePatterns": ["*.tmp"],
        }

        project = Project.from_dict("/test/path", data)

        assert project.path == "/test/path"
        assert project.allowed_tools == ["tool1"]
        assert project.history_count == 1
        assert project.mcp_servers == {"server1": {"config": "value"}}
        assert project.has_trust_dialog_accepted is True
        assert project.project_onboarding_seen_count == 2
        assert project.enable_all_project_mcp_servers is True
        assert project.ignore_patterns == ["*.tmp"]

    def test_from_dict_with_missing_fields(self) -> None:
        """Test from_dict with minimal data."""
        # Minimal data - should use defaults
        data: dict[str, Any] = {}
        project = Project.from_dict("/minimal/path", data)

        assert project.path == "/minimal/path"
        assert project.allowed_tools == []
        assert project.history == []
        assert project.mcp_servers == {}
        assert project.has_trust_dialog_accepted is False
        assert project.project_onboarding_seen_count == 0

    def test_roundtrip_conversion(self, sample_project: Project) -> None:
        """Test that to_dict and from_dict are inverse operations."""
        # Convert to dict and back
        data = sample_project.to_dict()
        reconstructed = Project.from_dict(sample_project.path, data)

        # Verify all fields match
        assert reconstructed.path == sample_project.path
        assert reconstructed.allowed_tools == sample_project.allowed_tools
        assert reconstructed.history == sample_project.history
        assert reconstructed.mcp_servers == sample_project.mcp_servers
        assert reconstructed.has_trust_dialog_accepted == sample_project.has_trust_dialog_accepted
        assert (
            reconstructed.project_onboarding_seen_count
            == sample_project.project_onboarding_seen_count
        )
