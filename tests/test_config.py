"""Tests for the config module."""

from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING

from claude_manager.config import ClaudeConfigManager
from claude_manager.models import Project

if TYPE_CHECKING:
    from pathlib import Path


class TestClaudeConfigManager:
    """Test the ClaudeConfigManager class."""

    def test_init_default_path(self, mock_home_dir: Path) -> None:
        """Test initialization with default path."""
        manager = ClaudeConfigManager()
        assert manager.config_path == mock_home_dir / ".claude.json"
        assert manager.backup_dir == mock_home_dir / ".claude_backups"
        assert manager.backup_dir.exists()

    def test_init_custom_path(self, tmp_path: Path) -> None:
        """Test initialization with custom path."""
        custom_path = tmp_path / "custom.json"
        manager = ClaudeConfigManager(str(custom_path))
        assert manager.config_path == custom_path

    def test_load_config_success(self, config_manager: ClaudeConfigManager) -> None:
        """Test successful config loading."""
        assert config_manager.config_data["numStartups"] == 10
        assert len(config_manager.config_data["projects"]) == 3

    def test_load_config_file_not_found(self, tmp_path: Path) -> None:
        """Test loading when config file doesn't exist."""
        manager = ClaudeConfigManager(str(tmp_path / "nonexistent.json"))
        assert manager.load_config() is False

    def test_load_config_invalid_json(self, tmp_path: Path) -> None:
        """Test loading invalid JSON."""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("{ invalid json }")

        manager = ClaudeConfigManager(str(invalid_file))
        assert manager.load_config() is False

    def test_save_config(self, config_manager: ClaudeConfigManager, tmp_path: Path) -> None:
        """Test saving configuration."""
        # Modify config
        config_manager.config_data["test_field"] = "test_value"

        # Save
        assert config_manager.save_config(create_backup=False) is True

        # Verify saved content
        with open(config_manager.config_path) as f:
            saved_data = json.load(f)

        assert saved_data["test_field"] == "test_value"

    def test_save_config_with_backup(self, config_manager: ClaudeConfigManager) -> None:
        """Test saving with backup creation."""
        original_projects = len(config_manager.config_data["projects"])

        # Modify and save
        config_manager.config_data["projects"] = {}
        assert config_manager.save_config(create_backup=True) is True

        # Check backup was created
        backups = list(config_manager.backup_dir.glob("claude_*.json"))
        assert len(backups) > 0

        # Verify backup contains original data
        with open(backups[-1]) as f:
            backup_data = json.load(f)
        assert len(backup_data["projects"]) == original_projects

    def test_create_backup(self, config_manager: ClaudeConfigManager) -> None:
        """Test backup creation."""
        backup_path = config_manager.create_backup()

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.name.startswith("claude_")
        assert backup_path.suffix == ".json"

        # Verify backup content matches original
        with open(backup_path) as f:
            backup_data = json.load(f)
        assert backup_data == config_manager.config_data

    def test_create_backup_no_config(self, tmp_path: Path) -> None:
        """Test backup creation when config doesn't exist."""
        manager = ClaudeConfigManager(str(tmp_path / "nonexistent.json"))
        assert manager.create_backup() is None

    def test_clean_old_backups(self, config_manager: ClaudeConfigManager) -> None:
        """Test cleaning old backups."""
        # Create many backups with proper date formatting
        for i in range(15):
            # Use proper date formatting: YYYYMMDD
            backup_path = config_manager.backup_dir / f"claude_202401{i:02d}_120000.json"
            shutil.copy2(config_manager.config_path, backup_path)

        # Clean old backups
        config_manager._clean_old_backups(keep_count=5)

        # Verify only 5 remain
        backups = list(config_manager.backup_dir.glob("claude_*.json"))
        assert len(backups) == 5

        # Verify the newest ones were kept (14, 13, 12, 11, 10)
        backup_names = [b.name for b in backups]
        assert "claude_20240114_120000.json" in backup_names
        assert "claude_20240110_120000.json" in backup_names

    def test_get_projects(self, config_manager: ClaudeConfigManager) -> None:
        """Test getting projects."""
        projects = config_manager.get_projects()

        assert len(projects) == 3
        assert "/home/user/project1" in projects
        assert "/home/user/project2" in projects
        assert "/home/user/nonexistent" in projects

        # Verify project data
        project1 = projects["/home/user/project1"]
        assert isinstance(project1, Project)
        assert project1.history_count == 2
        assert len(project1.mcp_servers) == 1
        assert project1.has_trust_dialog_accepted is True

    def test_remove_project(self, config_manager: ClaudeConfigManager) -> None:
        """Test removing a project."""
        # Remove existing project
        assert config_manager.remove_project("/home/user/project2") is True
        assert len(config_manager.config_data["projects"]) == 2
        assert "/home/user/project2" not in config_manager.config_data["projects"]

        # Try to remove non-existent project
        assert config_manager.remove_project("/nonexistent/path") is False

    def test_update_project(
        self, config_manager: ClaudeConfigManager, sample_project: Project
    ) -> None:
        """Test updating a project."""
        # Update existing project
        existing_project = config_manager.get_projects()["/home/user/project1"]
        existing_project.history.append({"display": "new command", "pastedContents": {}})

        assert config_manager.update_project(existing_project) is True

        # Verify update
        updated_data = config_manager.config_data["projects"]["/home/user/project1"]
        assert len(updated_data["history"]) == 3

        # Add new project
        assert config_manager.update_project(sample_project) is True
        assert sample_project.path in config_manager.config_data["projects"]

    def test_get_config_size(self, config_manager: ClaudeConfigManager) -> None:
        """Test getting config file size."""
        size = config_manager.get_config_size()
        assert size > 0
        assert isinstance(size, int)

    def test_get_stats(self, config_manager: ClaudeConfigManager) -> None:
        """Test getting configuration statistics."""
        stats = config_manager.get_stats()

        assert stats["total_projects"] == 3
        assert stats["total_history_entries"] == 3  # 2 + 0 + 1
        assert stats["total_mcp_servers"] == 1
        assert stats["config_size"] > 0
        assert stats["num_startups"] == 10
        assert stats["user_email"] == "test@example.com"
        assert stats["organization"] == "Test Organization"

    def test_restore_from_backup(self, config_manager: ClaudeConfigManager) -> None:
        """Test restoring from backup."""
        # First, verify initial state
        initial_project_count = len(config_manager.config_data["projects"])
        assert initial_project_count > 0, "Config should have projects initially"

        # Create a backup
        backup_path = config_manager.create_backup()
        assert backup_path is not None

        # Modify current config
        config_manager.config_data["projects"] = {}
        config_manager.save_config(create_backup=False)

        # Restore from backup
        assert config_manager.restore_from_backup(backup_path) is True

        # Verify restoration
        assert len(config_manager.config_data["projects"]) == initial_project_count

    def test_restore_from_nonexistent_backup(
        self, config_manager: ClaudeConfigManager, tmp_path: Path
    ) -> None:
        """Test restoring from non-existent backup."""
        fake_backup = tmp_path / "fake_backup.json"
        assert config_manager.restore_from_backup(fake_backup) is False

    def test_get_backups(self, config_manager: ClaudeConfigManager) -> None:
        """Test getting list of backups."""
        # Create some backups with small delays to ensure different timestamps
        import time

        backup_paths = []
        for _i in range(3):
            backup_path = config_manager.create_backup()
            if backup_path:
                backup_paths.append(backup_path)
            time.sleep(0.001)  # Small delay to ensure different timestamps

        backups = config_manager.get_backups()
        assert len(backups) >= 3
        assert all(b.name.startswith("claude_") for b in backups)
        assert all(b.suffix == ".json" for b in backups)

        # Verify backups are sorted in reverse order (most recent first)
        if len(backups) >= 2:
            # Since filenames include timestamps, alphabetical reverse sort should give newest first
            assert backups[0].name > backups[1].name, "Backups should be sorted most recent first"
