"""Tests for the CLI module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from claude_manager.cli import main

if TYPE_CHECKING:
    from pathlib import Path


class TestCLI:
    """Test the command line interface."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a Click test runner."""
        return CliRunner()

    def test_version_option(self, runner: CliRunner) -> None:
        """Test --version option."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "claude-manager" in result.output
        assert "1.0.0" in result.output

    def test_help_option(self, runner: CliRunner) -> None:
        """Test --help option."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Claude Manager" in result.output
        assert "Manage your Claude Code projects" in result.output
        assert "--config" in result.output
        assert "--debug" in result.output

    @patch("claude_manager.cli.ClaudeConfigManager")
    @patch("claude_manager.cli.run_tui")
    def test_main_success(
        self,
        mock_run_tui: Mock,
        mock_config_class: Mock,
        runner: CliRunner,
        temp_config_file: Path,
    ) -> None:
        """Test successful execution."""
        # Setup mocks
        mock_config = Mock()
        mock_config.load_config.return_value = True
        mock_config_class.return_value = mock_config

        # Run
        result = runner.invoke(main, ["-c", str(temp_config_file)])

        # Verify
        assert result.exit_code == 0
        mock_config_class.assert_called_once_with(str(temp_config_file))
        mock_config.load_config.assert_called_once()
        mock_run_tui.assert_called_once_with(mock_config)

    @patch("claude_manager.cli.ClaudeConfigManager")
    def test_main_config_load_failure(
        self,
        mock_config_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test handling of config load failure."""
        # Setup mock
        mock_config = Mock()
        mock_config.load_config.return_value = False
        mock_config_class.return_value = mock_config

        # Run
        result = runner.invoke(main, [])

        # Verify
        assert result.exit_code == 1
        assert "Failed to load configuration" in result.output

    @patch("claude_manager.cli.ClaudeConfigManager")
    @patch("claude_manager.cli.run_tui")
    def test_main_keyboard_interrupt(
        self,
        mock_run_tui: Mock,
        mock_config_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test handling of keyboard interrupt."""
        # Setup mocks
        mock_config = Mock()
        mock_config.load_config.return_value = True
        mock_config_class.return_value = mock_config

        mock_run_tui.side_effect = KeyboardInterrupt

        # Run
        result = runner.invoke(main, [])

        # Verify
        assert result.exit_code == 0
        # Note: Click doesn't capture KeyboardInterrupt output properly in tests

    @patch("claude_manager.cli.ClaudeConfigManager")
    @patch("claude_manager.cli.run_tui")
    def test_main_with_debug(
        self,
        mock_run_tui: Mock,
        mock_config_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test running with debug flag."""
        # Setup mocks
        mock_config = Mock()
        mock_config.load_config.return_value = True
        mock_config_class.return_value = mock_config

        # Run with debug
        with patch("claude_manager.cli.logging.basicConfig") as mock_logging:
            result = runner.invoke(main, ["--debug"])

            # Verify debug logging was set up
            assert result.exit_code == 0
            mock_logging.assert_called_once()
            call_kwargs = mock_logging.call_args.kwargs
            assert call_kwargs["level"] == 10  # logging.DEBUG

    @patch("claude_manager.cli.ClaudeConfigManager")
    @patch("claude_manager.cli.run_tui")
    def test_main_exception_handling(
        self,
        mock_run_tui: Mock,
        mock_config_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test handling of general exceptions."""
        # Setup mocks
        mock_config = Mock()
        mock_config.load_config.side_effect = Exception("Test error")
        mock_config_class.return_value = mock_config

        # Run
        result = runner.invoke(main, [])

        # Verify
        assert result.exit_code == 1
        assert "Error: Test error" in result.output

    @patch("claude_manager.cli.ClaudeConfigManager")
    @patch("claude_manager.cli.run_tui")
    def test_main_exception_with_debug(
        self,
        mock_run_tui: Mock,
        mock_config_class: Mock,
        runner: CliRunner,
    ) -> None:
        """Test exception handling with debug flag."""
        # Setup mocks
        mock_config = Mock()
        mock_config.load_config.side_effect = ValueError("Detailed error")
        mock_config_class.return_value = mock_config

        # Run with debug
        with patch("claude_manager.cli.console.print_exception") as mock_print_exc:
            result = runner.invoke(main, ["--debug"])

            # Verify
            assert result.exit_code == 1
            assert "Error: Detailed error" in result.output
            mock_print_exc.assert_called_once()
