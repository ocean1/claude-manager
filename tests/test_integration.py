"""Integration tests for Claude Manager."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest

from claude_manager.config import ClaudeConfigManager

if TYPE_CHECKING:
    from pathlib import Path


class TestIntegration:
    """Integration tests across modules."""

    @pytest.fixture
    def full_config_file(self, tmp_path: Path) -> Path:
        """Create a more comprehensive config file for integration testing."""
        config_data: dict[str, Any] = {
            "numStartups": 50,
            "firstStartTime": "2024-01-01T00:00:00.000Z",
            "oauthAccount": {
                "emailAddress": "integration@test.com",
                "organizationName": "Integration Test Org",
            },
            "projects": {},
        }

        # Add many projects with varied characteristics
        for i in range(20):
            project_path = f"/home/user/project_{i}"
            history_entries = []

            # Vary history sizes
            if i % 3 == 0:
                history_entries = [
                    {"display": f"cmd_{j}", "pastedContents": {}} for j in range(i * 10)
                ]

            # Vary MCP servers
            mcp_servers = {}
            if i % 4 == 0:
                mcp_servers = {f"server_{i}": {"url": f"http://localhost:{8000 + i}"}}

            config_data["projects"][project_path] = {
                "allowedTools": [f"tool_{i}"] if i % 2 == 0 else [],
                "history": history_entries,
                "mcpServers": mcp_servers,
                "enabledMcpjsonServers": [],
                "disabledMcpjsonServers": [],
                "enableAllProjectMcpServers": i % 5 == 0,
                "hasTrustDialogAccepted": i % 2 == 0,
                "ignorePatterns": ["*.tmp"] if i % 3 == 0 else [],
                "projectOnboardingSeenCount": i,
                "hasClaudeMdExternalIncludesApproved": False,
                "hasClaudeMdExternalIncludesWarningShown": False,
                "dontCrawlDirectory": False,
                "mcpContextUris": [],
            }

        config_file = tmp_path / "integration_config.json"
        config_file.write_text(json.dumps(config_data, indent=2))
        return config_file

    def test_full_workflow(self, full_config_file: Path, tmp_path: Path) -> None:
        """Test a complete workflow of operations."""
        # Initialize manager
        manager = ClaudeConfigManager(str(full_config_file))
        assert manager.load_config() is True

        # Get initial stats
        initial_stats = manager.get_stats()
        assert initial_stats["total_projects"] == 20

        # Create backup
        backup_path = manager.create_backup()
        assert backup_path is not None
        assert backup_path.exists()

        # Get projects and analyze
        projects = manager.get_projects()

        # Find projects with large histories
        large_history_projects = [p for p, proj in projects.items() if proj.history_count > 50]
        assert len(large_history_projects) > 0

        # Remove some projects
        removed_count = 0
        for path in large_history_projects[:3]:
            if manager.remove_project(path):
                removed_count += 1
        assert removed_count == 3

        # Save changes
        assert manager.save_config() is True

        # Verify changes persisted
        manager2 = ClaudeConfigManager(str(full_config_file))
        assert manager2.load_config() is True
        assert manager2.get_stats()["total_projects"] == 17

        # Test restoration
        assert manager2.restore_from_backup(backup_path) is True
        assert manager2.get_stats()["total_projects"] == 20

    def test_project_modifications(self, config_manager: ClaudeConfigManager) -> None:
        """Test various project modifications."""
        # Get a project
        projects = config_manager.get_projects()
        project_path = "/home/user/project1"
        project = projects[project_path]

        # Modify project
        original_history_count = project.history_count
        project.history.extend(
            [{"display": f"new_cmd_{i}", "pastedContents": {}} for i in range(5)]
        )
        project.mcp_servers["new_server"] = {"url": "http://newserver:8080"}
        project.allowed_tools.append("new_tool")

        # Update and save
        assert config_manager.update_project(project) is True
        assert config_manager.save_config() is True

        # Reload and verify
        new_manager = ClaudeConfigManager(str(config_manager.config_path))
        assert new_manager.load_config() is True

        updated_project = new_manager.get_projects()[project_path]
        assert updated_project.history_count == original_history_count + 5
        assert "new_server" in updated_project.mcp_servers
        assert "new_tool" in updated_project.allowed_tools

    def test_backup_rotation(self, config_manager: ClaudeConfigManager) -> None:
        """Test backup rotation functionality."""
        import time

        # Create many backups
        backup_paths = []
        for _i in range(15):
            backup = config_manager.create_backup()
            if backup:
                backup_paths.append(backup)
            # Small delay to ensure unique timestamps on Windows
            time.sleep(0.001)

        # Check that old backups were cleaned
        existing_backups = list(config_manager.backup_dir.glob("claude_*.json"))
        assert len(existing_backups) <= 10

        # Verify newest backups are kept
        newest_backup = max(existing_backups, key=lambda p: p.stat().st_mtime)
        assert newest_backup in backup_paths[-10:]

    def test_empty_config_handling(self, tmp_path: Path) -> None:
        """Test handling of empty configuration."""
        # Create empty config
        empty_config = tmp_path / "empty.json"
        empty_config.write_text("{}")

        manager = ClaudeConfigManager(str(empty_config))
        assert manager.load_config() is True

        # Should handle missing fields gracefully
        projects = manager.get_projects()
        assert len(projects) == 0

        stats = manager.get_stats()
        assert stats["total_projects"] == 0
        assert stats["num_startups"] == 0
        assert stats["user_email"] == "N/A"

    def test_concurrent_modifications(self, config_manager: ClaudeConfigManager) -> None:
        """Test handling of concurrent-like modifications."""
        # Get projects
        projects = config_manager.get_projects()

        # Simulate modifications to multiple projects
        modified_projects = []
        for i, (_path, project) in enumerate(projects.items()):
            if i >= 2:  # Modify first 2 projects
                break
            project.history.append({"display": f"concurrent_cmd_{i}", "pastedContents": {}})
            modified_projects.append(project)

        # Update all at once
        for project in modified_projects:
            assert config_manager.update_project(project) is True

        # Save once
        assert config_manager.save_config() is True

        # Verify all updates were saved
        new_manager = ClaudeConfigManager(str(config_manager.config_path))
        assert new_manager.load_config() is True

        for project in modified_projects:
            updated = new_manager.get_projects()[project.path]
            assert any(h.get("display", "").startswith("concurrent_cmd_") for h in updated.history)

    @pytest.mark.parametrize("corruption_type", ["truncated", "invalid_json", "wrong_type"])
    def test_corrupted_config_recovery(
        self, config_manager: ClaudeConfigManager, tmp_path: Path, corruption_type: str
    ) -> None:
        """Test recovery from various types of config corruption."""
        # Create backup first
        backup_path = config_manager.create_backup()
        assert backup_path is not None

        # Corrupt the config file
        if corruption_type == "truncated":
            # Truncate the file
            with open(config_manager.config_path) as f:
                content = f.read()
            with open(config_manager.config_path, "w") as f:
                f.write(content[: len(content) // 2])
        elif corruption_type == "invalid_json":
            # Write invalid JSON
            config_manager.config_path.write_text('{"invalid": json content}')
        elif corruption_type == "wrong_type":
            # Write wrong data type
            config_manager.config_path.write_text('["this", "should", "be", "object"]')

        # Try to load corrupted config
        corrupted_manager = ClaudeConfigManager(str(config_manager.config_path))
        assert corrupted_manager.load_config() is False

        # Restore from backup
        assert corrupted_manager.restore_from_backup(backup_path) is True

        # Verify restoration worked
        projects = corrupted_manager.get_projects()
        assert len(projects) > 0
