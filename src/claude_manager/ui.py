"""Terminal UI components for Claude Manager."""

from __future__ import annotations

import contextlib
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING

import questionary
from questionary import Choice
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from claude_manager.ui_helpers import (
    Confirm,
    Prompt,
    safe_autocomplete,
    safe_checkbox,
    safe_select,
    wait_for_enter,
)

if TYPE_CHECKING:
    from claude_manager.config import ClaudeConfigManager
    from claude_manager.models import Project

logger = logging.getLogger(__name__)
console = Console()


class ClaudeProjectManagerUI:
    """Terminal UI for Claude Project Manager."""

    def __init__(self, config_manager: ClaudeConfigManager) -> None:
        """Initialize the UI.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.console = console

    def run(self) -> None:
        """Main UI loop."""
        self.show_welcome()

        while True:
            choice = self.show_main_menu()

            if choice is None:  # Should not happen with proper CTRL+C handling
                break

            # Extract the actual value from Choice object if needed
            if isinstance(choice, Choice):
                choice_value = choice.value
            elif isinstance(choice, str):
                choice_value = choice
            else:
                choice_value = str(choice) if choice else None

            try:
                if choice_value == "list":
                    self.list_projects()
                elif choice_value == "analyze":
                    self.analyze_projects()
                elif choice_value == "edit":
                    self.edit_project()
                elif choice_value == "remove":
                    self.remove_projects()
                elif choice_value == "mcp":
                    self.manage_mcp_servers()
                elif choice_value == "history":
                    self.clear_history()
                elif choice_value == "backup":
                    self.backup_management()
                elif choice_value == "info":
                    self.show_config_info()
                elif choice_value == "exit":
                    console.print("\n[green]Thank you for using Claude Project Manager![/green]")
                    break
            except Exception as e:
                console.print(f"\n[red]Error: {e}[/red]\n")
                logger.exception("Error in UI operation")
                # Continue running unless it's a critical error
                if not isinstance(e, (ValueError, KeyError, AttributeError)):
                    raise

    def show_welcome(self) -> None:
        """Display welcome message."""
        console.clear()
        welcome_text = """
[bold cyan]Claude Code Project Manager[/bold cyan]
[dim]Manage your Claude Code projects and configurations[/dim]
        """
        panel = Panel(welcome_text, box=box.DOUBLE, expand=False)
        console.print(panel)
        console.print()

    def show_main_menu(self) -> str | None:
        """Display main menu and get user choice.

        Returns:
            Selected menu option or None if cancelled
        """
        choices = [
            Choice(title="📋 List Projects", value="list"),
            Choice(title="🔍 Analyze Projects (find issues, unused projects)", value="analyze"),
            Choice(title="✏️  Edit Project Settings", value="edit"),
            Choice(title="🗑️  Remove Projects", value="remove"),
            Choice(title="🔌 Manage MCP Servers", value="mcp"),
            Choice(title="📜 Clear History", value="history"),
            Choice(title="💾 Backup Management", value="backup"),
            Choice(title="ℹ️  Configuration Info", value="info"),
            Choice(title="❌ Exit", value="exit"),
        ]

        return safe_select(
            "What would you like to do?",
            choices=choices,
            style=questionary.Style(
                [
                    ("question", "bold"),
                    ("highlighted", "fg:cyan bold"),
                    ("selected", "fg:green"),
                    ("pointer", "fg:cyan bold"),
                ]
            ),
        )

    def list_projects(self) -> None:
        """List all projects with details."""
        projects = self.config_manager.get_projects()

        if not projects:
            console.print("\n[yellow]No projects found in configuration.[/yellow]\n")
            return

        console.clear()
        console.print(f"\n[bold cyan]Claude Code Projects ({len(projects)} total)[/bold cyan]\n")

        # Create choices with detailed info
        choices = []
        choices.append(Choice(title="← Back to Main Menu", value=None))

        for path, project in sorted(projects.items()):
            exists = "[green]✓[/green]" if project.directory_exists else "[red]✗[/red]"
            history = f"[magenta]{project.history_count:3d}[/magenta]"
            mcp = f"[blue]{len(project.mcp_servers):2d}[/blue]"
            size = f"[yellow]{project.get_size_estimate() / 1024:6.1f}KB[/yellow]"

            # Format the path nicely
            display_path = path
            if len(path) > 60:
                display_path = "..." + path[-57:]

            title = f"{exists} {history} hist {mcp} mcp {size}  {display_path}"
            choices.append(Choice(title=title, value=path))

        selected = safe_select(
            "Select a project to view details (or use ↑↓ arrows):",
            choices=choices,
            style=questionary.Style(
                [
                    ("highlighted", "fg:cyan bold"),
                    ("selected", "fg:green"),
                ]
            ),
        )

        if selected:
            console.clear()
            self.show_project_details(projects[selected])
            console.print()
            with contextlib.suppress(KeyboardInterrupt, EOFError):
                console.input("\n[dim]Press Enter to continue...[/dim]")

    def show_project_details(self, project: Project) -> None:
        """Show detailed information about a project.

        Args:
            project: Project to show details for
        """
        console.print()

        # Create a tree view
        tree = Tree(f"[bold cyan]{project.path}[/bold cyan]")

        # Basic info
        info_branch = tree.add("[bold]Basic Information[/bold]")
        info_branch.add(f"Directory exists: {'✓' if project.directory_exists else '[red]✗[/red]'}")
        info_branch.add(f"History entries: {project.history_count}")
        info_branch.add(
            f"Trust dialog accepted: {'✓' if project.has_trust_dialog_accepted else '✗'}"
        )
        info_branch.add(f"Onboarding seen: {project.project_onboarding_seen_count} times")

        # MCP Servers
        if project.mcp_servers:
            mcp_branch = tree.add(f"[bold]MCP Servers ({len(project.mcp_servers)})[/bold]")
            for server_name, server_config in project.mcp_servers.items():
                mcp_branch.add(f"{server_name}: {server_config}")

        # Recent history
        if project.history:
            history_branch = tree.add("[bold]Recent History (last 5)[/bold]")
            for entry in project.history[-5:]:
                display = entry.get("display", "N/A")
                if len(display) > 60:
                    display = display[:57] + "..."
                history_branch.add(display)

        # Allowed tools
        if project.allowed_tools:
            tools_branch = tree.add(f"[bold]Allowed Tools ({len(project.allowed_tools)})[/bold]")
            for tool in project.allowed_tools:
                tools_branch.add(tool)

        console.print(tree)
        console.print()

    def analyze_projects(self) -> None:
        """Analyze projects for issues and usage patterns.

        This function scans all projects and identifies:
        - Projects with non-existent directories (may have been deleted)
        - Projects with no history (possibly unused)
        - Projects with large history (may need cleanup)
        - Projects without trust dialog accepted
        - Overall statistics and recommendations
        """
        projects = self.config_manager.get_projects()

        if not projects:
            console.print("\n[yellow]No projects found in configuration.[/yellow]\n")
            return

        console.print("\n[bold]Analyzing projects...[/bold]\n")

        # Find issues
        non_existent: list[str] = []
        empty_history: list[str] = []
        large_history: list[tuple[str, int]] = []
        no_trust: list[str] = []

        total_size = 0

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Analyzing...", total=len(projects))

            for path, project in projects.items():
                if not project.directory_exists:
                    non_existent.append(path)

                if project.history_count == 0:
                    empty_history.append(path)
                elif project.history_count > 100:
                    large_history.append((path, project.history_count))

                if not project.has_trust_dialog_accepted:
                    no_trust.append(path)

                total_size += project.get_size_estimate()

                progress.update(task, advance=1)

        # Display analysis results
        console.print("\n[bold cyan]Analysis Results[/bold cyan]\n")

        # Summary statistics
        stats_table = Table(box=box.SIMPLE)
        stats_table.add_column("Metric", style="bold")
        stats_table.add_column("Value", justify="right")

        stats_table.add_row("Total Projects", str(len(projects)))
        stats_table.add_row("Total Size", f"{total_size / 1024 / 1024:.2f} MB")
        stats_table.add_row(
            "Average History Size",
            f"{sum(p.history_count for p in projects.values()) / len(projects):.1f}",
        )

        console.print(stats_table)
        console.print()

        # Issues found
        if non_existent:
            console.print(f"[red]• Non-existent directories ({len(non_existent)}):[/red]")
            for path in non_existent[:5]:
                console.print(f"  - {path}")
            if len(non_existent) > 5:
                console.print(f"  ... and {len(non_existent) - 5} more")
            console.print()

        if empty_history:
            console.print(f"[yellow]• Projects with no history ({len(empty_history)}):[/yellow]")
            for path in empty_history[:5]:
                console.print(f"  - {path}")
            if len(empty_history) > 5:
                console.print(f"  ... and {len(empty_history) - 5} more")
            console.print()

        if large_history:
            console.print("[blue]• Projects with large history:[/blue]")
            for path, count in sorted(large_history, key=lambda x: x[1], reverse=True)[:5]:
                console.print(f"  - {path}: {count} entries")
            console.print()

        # Recommendations
        console.print("[bold green]Recommendations:[/bold green]")
        if non_existent:
            console.print("• Consider removing projects with non-existent directories")
        if empty_history:
            console.print("• Projects with no history might be unused and can be removed")
        if large_history:
            console.print("• Consider clearing history for projects with many entries")

    def edit_project(self) -> None:
        """Edit settings for a specific project."""
        projects = self.config_manager.get_projects()

        if not projects:
            console.print("\n[yellow]No projects found in configuration.[/yellow]\n")
            return

        # Create choices with more info
        choices = []
        for path, project in sorted(projects.items()):
            exists = "✓" if project.directory_exists else "✗"
            info = f" (History: {project.history_count}, Exists: {exists})"
            choices.append(Choice(title=path + info, value=path))

        project_path = safe_select(
            "Select a project to edit:",
            choices=choices,
            style=questionary.Style(
                [
                    ("highlighted", "fg:cyan bold"),
                    ("selected", "fg:green"),
                ]
            ),
        )

        if not project_path:
            return

        project = projects[project_path]

        # Show current settings and edit options
        while True:
            console.clear()
            console.print(f"\n[bold cyan]Editing Project: {project_path}[/bold cyan]\n")

            # Show current settings
            table = Table(box=box.SIMPLE)
            table.add_column("Setting", style="bold")
            table.add_column("Current Value")

            table.add_row("Directory Exists", "✓" if project.directory_exists else "[red]✗[/red]")
            table.add_row("History Entries", str(project.history_count))
            table.add_row("MCP Servers", str(len(project.mcp_servers)))
            table.add_row(
                "Trust Dialog Accepted", "✓" if project.has_trust_dialog_accepted else "✗"
            )
            table.add_row("Allowed Tools", str(len(project.allowed_tools)))
            table.add_row("Ignore Patterns", str(len(project.ignore_patterns)))

            console.print(table)
            console.print()

            # Edit menu
            edit_choices = [
                Choice(title="Clear History", value="clear_history"),
                Choice(title="Toggle Trust Dialog", value="toggle_trust"),
                Choice(title="Edit Allowed Tools", value="edit_tools"),
                Choice(title="Edit Ignore Patterns", value="edit_ignore"),
                Choice(title="View Full Details", value="view_details"),
                Choice(title="Back to Main Menu", value="back"),
            ]

            action = safe_select(
                "What would you like to do?",
                choices=edit_choices,
                style=questionary.Style(
                    [
                        ("highlighted", "fg:cyan bold"),
                        ("selected", "fg:green"),
                    ]
                ),
            )

            if not action or action == "back":
                break

            if action == "clear_history":
                if Confirm.ask(f"Clear {project.history_count} history entries?"):
                    project.history.clear()
                    self.config_manager.update_project(project)
                    if self.config_manager.save_config():
                        console.print("[green]History cleared successfully![/green]")
                    else:
                        console.print("[red]Failed to save changes.[/red]")

            elif action == "toggle_trust":
                project.has_trust_dialog_accepted = not project.has_trust_dialog_accepted
                self.config_manager.update_project(project)
                if self.config_manager.save_config():
                    status = "accepted" if project.has_trust_dialog_accepted else "not accepted"
                    console.print(f"[green]Trust dialog is now {status}.[/green]")
                else:
                    console.print("[red]Failed to save changes.[/red]")

            elif action == "edit_tools":
                console.print("\n[yellow]Current allowed tools:[/yellow]")
                if project.allowed_tools:
                    for tool in project.allowed_tools:
                        console.print(f"  - {tool}")
                else:
                    console.print("  (none)")
                console.print("\n[dim]Tool editing not yet implemented.[/dim]")

            elif action == "edit_ignore":
                console.print("\n[yellow]Current ignore patterns:[/yellow]")
                if project.ignore_patterns:
                    for pattern in project.ignore_patterns:
                        console.print(f"  - {pattern}")
                else:
                    console.print("  (none)")
                console.print("\n[dim]Pattern editing not yet implemented.[/dim]")

            elif action == "view_details":
                console.clear()
                self.show_project_details(project)

    def remove_projects(self) -> None:
        """Remove selected projects."""
        projects = self.config_manager.get_projects()

        if not projects:
            console.print("\n[yellow]No projects found in configuration.[/yellow]\n")
            return

        # Offer different removal strategies
        strategy = safe_select(
            "How would you like to select projects to remove?",
            choices=[
                Choice(title="Non-existent directories", value="non_existent"),
                Choice(title="No history", value="no_history"),
                Choice(title="Manual selection", value="manual"),
                Choice(title="Back", value="back"),
            ],
        )

        if not strategy or strategy == "back":
            return

        projects_to_remove: list[str] = []

        if strategy == "non_existent":
            projects_to_remove = [p for p, proj in projects.items() if not proj.directory_exists]
        elif strategy == "no_history":
            projects_to_remove = [p for p, proj in projects.items() if proj.history_count == 0]
        elif strategy == "manual":
            choices = []
            for path, project in sorted(projects.items()):
                exists = "✓" if project.directory_exists else "✗"
                label = f"{path} (History: {project.history_count}, Exists: {exists})"
                choices.append(Choice(title=label, value=path))

            selected = safe_checkbox("Select projects to remove:", choices=choices)
            projects_to_remove = selected if selected else []

        if not projects_to_remove:
            console.print("\n[yellow]No projects selected for removal.[/yellow]\n")
            return

        # Show summary
        console.print(f"\n[bold]Selected {len(projects_to_remove)} project(s) for removal:[/bold]")
        for path in projects_to_remove:
            console.print(f"  - {path}")

        if Confirm.ask("\nAre you sure you want to remove these projects?"):
            # Create backup first
            console.print("\n[dim]Creating backup...[/dim]")
            backup_path = self.config_manager.create_backup()

            if backup_path:
                console.print(f"[green]Backup created at: {backup_path}[/green]")

                # Remove projects
                removed_count = 0
                for path in projects_to_remove:
                    if self.config_manager.remove_project(path):
                        removed_count += 1

                # Save configuration
                if self.config_manager.save_config(create_backup=False):
                    console.print(
                        f"\n[green]Successfully removed {removed_count} project(s).[/green]"
                    )
                else:
                    console.print("\n[red]Error saving configuration.[/red]")
            else:
                console.print("\n[red]Failed to create backup. Removal cancelled.[/red]")

    def manage_mcp_servers(self) -> None:
        """Manage MCP server configurations."""
        projects = self.config_manager.get_projects()

        # Filter projects with MCP servers
        projects_with_mcp = {p: proj for p, proj in projects.items() if proj.mcp_servers}

        if not projects_with_mcp:
            console.print("\n[yellow]No projects with MCP servers found.[/yellow]\n")
            return

        console.print(
            f"\n[bold]Projects with MCP Servers ({len(projects_with_mcp)} total)[/bold]\n"
        )

        # Show MCP server summary
        table = Table(box=box.ROUNDED)
        table.add_column("Project", style="cyan")
        table.add_column("MCP Servers", style="magenta")
        table.add_column("Enabled", justify="center", style="green")

        for path, project in projects_with_mcp.items():
            server_names = ", ".join(project.mcp_servers.keys())
            enabled = "✓" if project.enable_all_project_mcp_servers else "✗"

            table.add_row(
                path if len(path) < 50 else "..." + path[-47:],
                server_names,
                enabled,
            )

        console.print(table)

        # Offer management options
        action = safe_select(
            "\nWhat would you like to do?",
            choices=[
                Choice(title="View server details", value="view"),
                Choice(title="Enable/disable all MCP servers for a project", value="toggle"),
                Choice(title="Back to main menu", value="back"),
            ],
        )

        if not action or action == "back":
            return

        if action == "view":
            project_path = safe_autocomplete(
                "Select project:", choices=list(projects_with_mcp.keys())
            )

            if project_path:
                project = projects_with_mcp[project_path]
                console.print(f"\n[bold]MCP Servers for {project_path}:[/bold]\n")

                for server_name, config in project.mcp_servers.items():
                    console.print(f"[cyan]{server_name}:[/cyan]")
                    console.print(Syntax(json.dumps(config, indent=2), "json"))
                    console.print()

        elif action == "toggle":
            project_path = safe_autocomplete(
                "Select project:", choices=list(projects_with_mcp.keys())
            )

            if project_path:
                project = projects_with_mcp[project_path]
                current_state = project.enable_all_project_mcp_servers

                new_state = Confirm.ask(
                    f"Enable all MCP servers for this project? (Currently: {'enabled' if current_state else 'disabled'})"
                )

                project.enable_all_project_mcp_servers = new_state
                self.config_manager.update_project(project)

                if self.config_manager.save_config():
                    console.print(
                        f"\n[green]Updated MCP server settings for {project_path}[/green]"
                    )

    def clear_history(self) -> None:
        """Clear project history entries."""
        projects = self.config_manager.get_projects()

        # Filter projects with history
        projects_with_history = {p: proj for p, proj in projects.items() if proj.history_count > 0}

        if not projects_with_history:
            console.print("\n[yellow]No projects with history found.[/yellow]\n")
            return

        strategy = safe_select(
            "How would you like to clear history?",
            choices=[
                Choice(title="Clear all history for all projects", value="clear_all"),
                Choice(title="Clear history for specific projects", value="clear_specific"),
                Choice(title="Keep only recent entries", value="keep_recent"),
                Choice(title="Back to main menu", value="back"),
            ],
        )

        if not strategy or strategy == "back":
            return

        if strategy == "clear_all":
            total_entries = sum(p.history_count for p in projects_with_history.values())

            if Confirm.ask(
                f"Clear {total_entries} history entries from {len(projects_with_history)} projects?"
            ):
                # Create backup
                backup_path = self.config_manager.create_backup()

                if backup_path:
                    console.print(f"[green]Backup created at: {backup_path}[/green]")

                    # Clear history
                    for project in projects_with_history.values():
                        project.history.clear()
                        self.config_manager.update_project(project)

                    if self.config_manager.save_config(create_backup=False):
                        console.print(f"\n[green]Cleared {total_entries} history entries.[/green]")

        elif strategy == "clear_specific":
            choices = []
            for path, project in sorted(
                projects_with_history.items(), key=lambda x: x[1].history_count, reverse=True
            ):
                label = f"{path} ({project.history_count} entries)"
                choices.append(Choice(title=label, value=path))

            selected = safe_checkbox("Select projects to clear history:", choices=choices)

            if selected and Confirm.ask(f"Clear history for {len(selected)} project(s)?"):
                backup_path = self.config_manager.create_backup()

                if backup_path:
                    cleared = 0
                    for path in selected:
                        project = projects_with_history[path]
                        cleared += project.history_count
                        project.history.clear()
                        self.config_manager.update_project(project)

                    if self.config_manager.save_config(create_backup=False):
                        console.print(f"\n[green]Cleared {cleared} history entries.[/green]")

        elif strategy == "keep_recent":
            keep_count = int(
                Prompt.ask("How many recent entries to keep per project?", default="10")
            )

            total_to_remove = sum(
                max(0, p.history_count - keep_count) for p in projects_with_history.values()
            )

            if total_to_remove > 0 and Confirm.ask(
                f"Remove {total_to_remove} old history entries?"
            ):
                backup_path = self.config_manager.create_backup()

                if backup_path:
                    for project in projects_with_history.values():
                        if project.history_count > keep_count:
                            project.history = project.history[-keep_count:]
                            self.config_manager.update_project(project)

                    if self.config_manager.save_config(create_backup=False):
                        console.print(
                            f"\n[green]Removed {total_to_remove} old history entries.[/green]"
                        )

    def backup_management(self) -> None:
        """Manage configuration backups."""
        backup_files = self.config_manager.get_backups()

        if not backup_files:
            console.print("\n[yellow]No backups found.[/yellow]\n")

            if Confirm.ask("Would you like to create a backup now?"):
                backup_path = self.config_manager.create_backup()
                if backup_path:
                    console.print(f"\n[green]Backup created at: {backup_path}[/green]")

            return

        # Show backup list
        table = Table(title=f"Configuration Backups ({len(backup_files)} total)", box=box.ROUNDED)
        table.add_column("#", style="dim")
        table.add_column("Filename", style="cyan")
        table.add_column("Date", style="yellow")
        table.add_column("Size", justify="right", style="magenta")

        for i, backup in enumerate(backup_files, 1):
            timestamp = backup.stem.split("_", 1)[1]
            # Try new format with microseconds first, fall back to old format
            try:
                date_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S_%f")
            except ValueError:
                date_obj = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
            date = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            size = f"{backup.stat().st_size / 1024:.1f} KB"

            table.add_row(str(i), backup.name, date, size)

        console.print()
        console.print(table)
        console.print()

        # Backup actions
        action = safe_select(
            "What would you like to do?",
            choices=[
                Choice(title="Create new backup", value="create"),
                Choice(title="Restore from backup", value="restore"),
                Choice(title="Delete old backups", value="delete"),
                Choice(title="Back to main menu", value="back"),
            ],
        )

        if not action or action == "back":
            return

        if action == "create":
            backup_path = self.config_manager.create_backup()
            if backup_path:
                console.print(f"\n[green]Backup created at: {backup_path}[/green]")

        elif action == "restore":
            backup_num = Prompt.ask("Enter backup number to restore", default="0")

            try:
                idx = int(backup_num) - 1
                if 0 <= idx < len(backup_files):
                    backup_path = backup_files[idx]

                    if Confirm.ask(
                        f"Restore from {backup_path.name}? Current config will be backed up first."
                    ):
                        if self.config_manager.restore_from_backup(backup_path):
                            console.print(f"\n[green]Restored from {backup_path.name}[/green]")
                        else:
                            console.print("\n[red]Failed to restore from backup.[/red]")
            except (ValueError, IndexError):
                console.print("\n[red]Invalid backup number.[/red]")

        elif action == "delete":
            keep_count = int(Prompt.ask("How many recent backups to keep?", default="10"))

            if len(backup_files) > keep_count:
                to_delete = len(backup_files) - keep_count

                if Confirm.ask(f"Delete {to_delete} old backup(s)?"):
                    for backup in backup_files[:-keep_count]:
                        backup.unlink()
                    console.print(f"\n[green]Deleted {to_delete} old backup(s).[/green]")

    def show_config_info(self) -> None:
        """Show configuration statistics and information."""
        stats = self.config_manager.get_stats()

        # Create info panels
        console.print("\n[bold cyan]Claude Code Configuration Information[/bold cyan]\n")

        # User info
        user_info = Table(title="User Information", box=box.SIMPLE)
        user_info.add_column("Field", style="bold")
        user_info.add_column("Value")

        user_info.add_row("Email", stats["user_email"])
        user_info.add_row("Organization", stats["organization"])
        user_info.add_row("First Start", stats["first_start_time"])
        user_info.add_row("Total Startups", str(stats["num_startups"]))

        # Stats
        stats_table = Table(title="Configuration Statistics", box=box.SIMPLE)
        stats_table.add_column("Metric", style="bold")
        stats_table.add_column("Value", justify="right")

        stats_table.add_row("Total Projects", str(stats["total_projects"]))
        stats_table.add_row("Total History Entries", str(stats["total_history_entries"]))
        stats_table.add_row("Total MCP Servers", str(stats["total_mcp_servers"]))
        stats_table.add_row("Config File Size", f"{stats['config_size'] / 1024:.1f} KB")

        # Display
        columns = Columns([user_info, stats_table], equal=True, expand=True)
        console.print(columns)

        # Config location
        console.print(f"\n[dim]Configuration file: {self.config_manager.config_path}[/dim]")
        console.print(f"[dim]Backup directory: {self.config_manager.backup_dir}[/dim]")

        wait_for_enter(console)
