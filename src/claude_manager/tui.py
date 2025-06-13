"""Proper Terminal UI using Textual."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from rich.markup import escape
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TextArea,
)

if TYPE_CHECKING:
    from claude_manager.config import ClaudeConfigManager
    from claude_manager.models import Project


class ProjectListScreen(Screen):
    """Main screen showing project list."""

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "delete", "Delete Project"),
        Binding("h", "clear_history", "Clear History"),
        Binding("m", "manage_mcp", "MCP Servers"),
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "view_details", "View Details", show=False),
    ]

    def __init__(self, config_manager: ClaudeConfigManager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.projects = {}

    def compose(self) -> ComposeResult:
        """Create the UI."""
        yield Header()
        yield Container(DataTable(id="projects_table"), id="main_container")
        yield Footer()

    def on_mount(self) -> None:
        """Set up the table when screen mounts."""
        table = self.query_one("#projects_table", DataTable)
        table.add_columns("Path", "History", "MCP", "Exists", "Size")
        table.zebra_stripes = True
        table.cursor_type = "row"
        self.refresh_projects()

    @on(DataTable.RowSelected)
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection with Enter."""
        self.action_view_details()

    def refresh_projects(self) -> None:
        """Refresh the project list."""
        self.projects = self.config_manager.get_projects()
        table = self.query_one("#projects_table", DataTable)
        table.clear()

        for path, project in sorted(self.projects.items()):
            exists = "✓" if project.directory_exists else "✗"
            size = f"{project.get_size_estimate() / 1024:.1f}KB"

            # Shorten long paths
            display_path = path
            if len(path) > 80:
                display_path = "..." + path[-77:]

            table.add_row(
                display_path,
                str(project.history_count),
                str(len(project.mcp_servers)),
                exists,
                size,
                key=path,
            )

    def action_quit(self) -> None:
        """Quit the app."""
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh the project list."""
        self.refresh_projects()

    def action_view_details(self) -> None:
        """View details of selected project."""
        table = self.query_one("#projects_table", DataTable)
        if table.cursor_row is not None:
            rows = list(table.rows)
            if 0 <= table.cursor_row < len(rows):
                row_key = rows[table.cursor_row]
                project_path = row_key.value  # Get the actual string value
                if project_path in self.projects:
                    self.app.push_screen(
                        ProjectDetailScreen(self.projects[project_path], project_path)
                    )

    def action_delete(self) -> None:
        """Delete selected project."""
        table = self.query_one("#projects_table", DataTable)
        if table.cursor_row is not None:
            rows = list(table.rows)
            if 0 <= table.cursor_row < len(rows):
                row_key = rows[table.cursor_row]
                project_path = row_key.value  # Get the actual string value
                if project_path in self.projects:
                    self.app.push_screen(
                        ConfirmScreen(
                            f"Delete project?\n\n{project_path}",
                            lambda: self._do_delete(project_path),
                        )
                    )

    def _do_delete(self, project_path: str) -> None:
        """Actually delete the project."""
        self.config_manager.create_backup()
        if self.config_manager.remove_project(project_path):
            if self.config_manager.save_config(create_backup=False):
                self.notify("Project deleted", severity="information")
                self.refresh_projects()
            else:
                self.notify("Failed to save changes", severity="error")
        else:
            self.notify("Failed to delete project", severity="error")

    def action_clear_history(self) -> None:
        """Clear history of selected project."""
        table = self.query_one("#projects_table", DataTable)
        if table.cursor_row is not None:
            rows = list(table.rows)
            if 0 <= table.cursor_row < len(rows):
                row_key = rows[table.cursor_row]
                project_path = row_key.value  # Get the actual string value
                if project_path in self.projects:
                    project = self.projects[project_path]
                    if project.history_count > 0:
                        self.app.push_screen(
                            ConfirmScreen(
                                f"Clear {project.history_count} history entries?\n\n{project_path}",
                                lambda: self._do_clear_history(project_path),
                            )
                        )
                    else:
                        self.notify("No history to clear", severity="warning")

    def _do_clear_history(self, project_path: str) -> None:
        """Actually clear the history."""
        project = self.projects[project_path]
        self.config_manager.create_backup()
        project.history.clear()
        self.config_manager.update_project(project)

        if self.config_manager.save_config(create_backup=False):
            self.notify("History cleared", severity="information")
            self.refresh_projects()
        else:
            self.notify("Failed to save changes", severity="error")

    def action_manage_mcp(self) -> None:
        """Manage MCP servers for selected project."""
        table = self.query_one("#projects_table", DataTable)
        if table.cursor_row is not None:
            rows = list(table.rows)
            if 0 <= table.cursor_row < len(rows):
                row_key = rows[table.cursor_row]
                project_path = row_key.value
                if project_path in self.projects:
                    self.app.push_screen(
                        MCPServerScreen(
                            self.config_manager, self.projects[project_path], project_path
                        )
                    )


class ProjectDetailScreen(Screen):
    """Screen showing project details."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self, project: Project, project_path: str) -> None:
        super().__init__()
        self.project = project
        self.project_path = project_path

    def compose(self) -> ComposeResult:
        """Create the detail view."""
        yield Header()
        yield VerticalScroll(
            Static(f"[bold]Project: {self.project_path}[/bold]", id="project_title"),
            Static(id="project_info"),
            Static("[bold]Recent History:[/bold]", id="history_title"),
            Static(id="history_list"),
            id="detail_container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Populate the details."""
        info = self.query_one("#project_info", Static)
        info.update(
            f"Directory exists: {'✓' if self.project.directory_exists else '✗'}\n"
            f"History entries: {self.project.history_count}\n"
            f"MCP servers: {len(self.project.mcp_servers)}\n"
            f"Trust accepted: {'✓' if self.project.has_trust_dialog_accepted else '✗'}\n"
            f"Size: {self.project.get_size_estimate() / 1024:.1f}KB"
        )

        history = self.query_one("#history_list", Static)
        if self.project.history:
            history_text = ""
            for entry in self.project.history[-10:]:
                display = entry.get("display", "")
                if len(display) > 100:
                    display = display[:97] + "..."
                # Escape special characters to prevent markup errors
                display = escape(display)
                history_text += f"• {display}\n"
            history.update(history_text)
        else:
            history.update("[dim]No history[/dim]")

    def action_go_back(self) -> None:
        """Go back to project list."""
        self.app.pop_screen()


class ConfirmScreen(Screen):
    """Confirmation dialog screen."""

    def __init__(self, message: str, callback) -> None:
        super().__init__()
        self.message = message
        self.callback = callback

    def compose(self) -> ComposeResult:
        """Create the confirmation dialog."""
        yield Container(
            Static(self.message, id="confirm_message"),
            Horizontal(
                Button("Yes", variant="error", id="yes"),
                Button("No", variant="primary", id="no"),
                id="button_container",
            ),
            id="confirm_container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "yes":
            self.callback()
        self.app.pop_screen()


class MCPServerScreen(Screen):
    """Screen for managing MCP servers for a project."""

    BINDINGS = [
        Binding("escape", "go_back", "Back"),
        Binding("a", "add_server", "Add Server"),
        Binding("d", "delete_server", "Delete Server"),
        Binding("e", "edit_server", "Edit Server"),
        Binding("t", "toggle_all", "Toggle All"),
    ]

    def __init__(
        self, config_manager: ClaudeConfigManager, project: Project, project_path: str
    ) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.project = project
        self.project_path = project_path

    def compose(self) -> ComposeResult:
        """Create the MCP server management UI."""
        yield Header()
        yield Container(
            Static(f"[bold]MCP Servers for: {self.project_path}[/bold]", id="mcp_title"),
            Static(
                f"Enable all servers: {'✓' if self.project.enable_all_project_mcp_servers else '✗'}",
                id="enable_all_status",
            ),
            DataTable(id="mcp_table"),
            id="mcp_container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the MCP servers table."""
        table = self.query_one("#mcp_table", DataTable)
        table.add_columns("Server Name", "Configuration")
        table.zebra_stripes = True
        table.cursor_type = "row"
        self.refresh_servers()

    def refresh_servers(self) -> None:
        """Refresh the server list."""
        table = self.query_one("#mcp_table", DataTable)
        table.clear()

        for name, config in self.project.mcp_servers.items():
            # Truncate long configs for display
            config_str = str(config)
            if len(config_str) > 80:
                config_str = config_str[:77] + "..."
            table.add_row(name, config_str, key=name)

        # Update enable all status
        status = self.query_one("#enable_all_status", Static)
        status.update(
            f"Enable all servers: {'✓' if self.project.enable_all_project_mcp_servers else '✗'}"
        )

    def action_go_back(self) -> None:
        """Go back to project list."""
        self.app.pop_screen()

    def action_toggle_all(self) -> None:
        """Toggle enable all servers setting."""
        self.project.enable_all_project_mcp_servers = (
            not self.project.enable_all_project_mcp_servers
        )
        self.config_manager.update_project(self.project)

        if self.config_manager.save_config():
            self.notify("Updated enable all servers setting", severity="information")
            self.refresh_servers()
        else:
            self.notify("Failed to save changes", severity="error")

    def action_add_server(self) -> None:
        """Add a new MCP server."""
        self.app.push_screen(MCPServerEditScreen(self, None, None))

    def action_edit_server(self) -> None:
        """Edit selected MCP server."""
        table = self.query_one("#mcp_table", DataTable)
        if table.cursor_row is not None:
            rows = list(table.rows)
            if 0 <= table.cursor_row < len(rows):
                server_name = rows[table.cursor_row].value
                server_config = self.project.mcp_servers.get(server_name, {})
                self.app.push_screen(MCPServerEditScreen(self, server_name, server_config))

    def action_delete_server(self) -> None:
        """Delete selected MCP server."""
        table = self.query_one("#mcp_table", DataTable)
        if table.cursor_row is not None:
            rows = list(table.rows)
            if 0 <= table.cursor_row < len(rows):
                server_name = rows[table.cursor_row].value
                self.app.push_screen(
                    ConfirmScreen(
                        f"Delete MCP server '{server_name}'?",
                        lambda: self._do_delete_server(server_name),
                    )
                )

    def _do_delete_server(self, server_name: str) -> None:
        """Actually delete the server."""
        if server_name in self.project.mcp_servers:
            del self.project.mcp_servers[server_name]
            self.config_manager.update_project(self.project)

            if self.config_manager.save_config():
                self.notify(f"Deleted server '{server_name}'", severity="information")
                self.refresh_servers()
            else:
                self.notify("Failed to save changes", severity="error")

    def save_server(self, original_name: str | None, new_name: str, config: dict) -> None:
        """Save a server configuration."""
        # If renaming, remove old entry
        if (
            original_name
            and original_name != new_name
            and original_name in self.project.mcp_servers
        ):
            del self.project.mcp_servers[original_name]

        self.project.mcp_servers[new_name] = config
        self.config_manager.update_project(self.project)

        if self.config_manager.save_config():
            self.notify(f"Saved server '{new_name}'", severity="information")
            self.refresh_servers()
        else:
            self.notify("Failed to save changes", severity="error")


class MCPServerEditScreen(Screen):
    """Screen for editing MCP server configuration."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "save", "Save (Ctrl+S)"),
    ]

    def __init__(
        self, parent_screen: MCPServerScreen, server_name: str | None, server_config: dict | None
    ) -> None:
        super().__init__()
        self.parent_screen = parent_screen
        self.original_name = server_name
        self.server_config = server_config or {}

    def compose(self) -> ComposeResult:
        """Create the edit form."""
        yield Header()
        yield Container(
            Static(
                (
                    "[bold]Edit MCP Server[/bold]"
                    if self.original_name
                    else "[bold]Add MCP Server[/bold]"
                ),
                id="edit_title",
            ),
            Label("Server Name:"),
            Input(
                value=self.original_name or "", placeholder="Enter server name", id="server_name"
            ),
            Label("Configuration (JSON):"),
            TextArea(
                json.dumps(self.server_config, indent=2) if self.server_config else "{}",
                id="server_config",
                language="json",
            ),
            Static("[dim]Press Ctrl+S to save, Escape to cancel[/dim]", id="edit_help"),
            id="edit_container",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Focus the name input on mount."""
        self.query_one("#server_name", Input).focus()

    def action_save(self) -> None:
        """Save the server configuration."""
        name_input = self.query_one("#server_name", Input)
        config_area = self.query_one("#server_config", TextArea)

        server_name = name_input.value.strip()
        if not server_name:
            self.notify("Server name cannot be empty", severity="error")
            return

        try:
            # Parse the JSON to validate it
            server_config = json.loads(config_area.text)
            # Store it as a compact single-line JSON in the config
            self.parent_screen.save_server(self.original_name, server_name, server_config)
            self.app.pop_screen()
        except json.JSONDecodeError as e:
            self.notify(f"Invalid JSON: {e}", severity="error")
            return

    def action_cancel(self) -> None:
        """Cancel editing."""
        self.app.pop_screen()


class ClaudeManagerApp(App):
    """The main TUI application."""

    CSS = """
    #main_container {
        height: 100%;
        overflow: auto;
    }

    #projects_table {
        height: 100%;
    }

    #confirm_container {
        align: center middle;
        height: auto;
        width: 60;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }

    #confirm_message {
        height: auto;
        margin: 1 0;
        text-align: center;
    }

    #button_container {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }

    #detail_container {
        padding: 1 2;
    }

    #project_title {
        margin-bottom: 1;
    }

    #history_title {
        margin-top: 2;
        margin-bottom: 1;
    }

    #mcp_container {
        height: 100%;
        padding: 1 2;
    }

    #mcp_title {
        margin-bottom: 1;
    }

    #enable_all_status {
        margin-bottom: 1;
        color: $text-muted;
    }

    #mcp_table {
        height: 1fr;
    }

    #edit_container {
        align: center middle;
        height: auto;
        width: 80;
        max-width: 100;
        border: thick $background 80%;
        background: $surface;
        padding: 2;
    }

    #edit_title {
        margin-bottom: 1;
        text-align: center;
    }

    #server_name {
        margin-bottom: 1;
    }

    #server_config {
        height: 15;
        margin-bottom: 1;
    }

    #edit_help {
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self, config_manager: ClaudeConfigManager) -> None:
        super().__init__()
        self.config_manager = config_manager

    def on_mount(self) -> None:
        """Set up the app."""
        self.title = "Claude Manager"
        self.sub_title = "Manage your Claude Code projects"
        self.push_screen(ProjectListScreen(self.config_manager))


def run_tui(config_manager: ClaudeConfigManager) -> None:
    """Run the Textual UI."""
    app = ClaudeManagerApp(config_manager)
    app.run()
