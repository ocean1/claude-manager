"""Simple, working UI for Claude Manager."""

import questionary
from rich import box
from rich.console import Console
from rich.table import Table

from claude_manager.config import ClaudeConfigManager

console = Console()


class SimpleUI:
    """A simple UI that actually works."""

    def __init__(self, config_manager: ClaudeConfigManager) -> None:
        self.config_manager = config_manager

    def run(self) -> None:
        """Main loop."""
        while True:
            console.clear()
            console.print("[bold cyan]Claude Manager[/bold cyan]\n")

            action = questionary.select(
                "What do you want to do?",
                choices=[
                    "List all projects",
                    "Remove unused projects",
                    "Clear project history",
                    "View project details",
                    "Exit",
                ],
            ).ask()

            if not action or action == "Exit":
                break

            if action == "List all projects":
                self.list_projects()
            elif action == "Remove unused projects":
                self.remove_projects()
            elif action == "Clear project history":
                self.clear_history()
            elif action == "View project details":
                self.view_project_details()

    def list_projects(self) -> None:
        """Just list the damn projects."""
        console.clear()
        projects = self.config_manager.get_projects()

        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            console.input()
            return

        table = Table(title=f"Projects ({len(projects)})", box=box.SIMPLE)
        table.add_column("Path", style="cyan")
        table.add_column("History", justify="right")
        table.add_column("Exists", justify="center")

        for path, project in sorted(projects.items()):
            exists = "✓" if project.directory_exists else "✗"
            table.add_row(
                path if len(path) < 80 else "..." + path[-77:], str(project.history_count), exists
            )

        console.print(table)
        console.print("\n[dim]Press Enter to continue...[/dim]")
        console.input()

    def view_project_details(self) -> None:
        """View details of a specific project."""
        console.clear()
        projects = self.config_manager.get_projects()

        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            console.input()
            return

        # Simple list to choose from
        project_list = sorted(projects.keys())
        selected = questionary.select("Select a project:", choices=[*project_list, "← Back"]).ask()

        if not selected or selected == "← Back":
            return

        project = projects[selected]
        console.clear()
        console.print(f"[bold cyan]Project: {selected}[/bold cyan]\n")
        console.print(f"Directory exists: {'✓' if project.directory_exists else '✗'}")
        console.print(f"History entries: {project.history_count}")
        console.print(f"MCP servers: {len(project.mcp_servers)}")
        console.print(f"Trust accepted: {'✓' if project.has_trust_dialog_accepted else '✗'}")

        if project.history and project.history_count > 0:
            console.print("\n[bold]Recent history:[/bold]")
            for entry in project.history[-5:]:
                display = entry.get("display", "")
                if len(display) > 70:
                    display = display[:67] + "..."
                console.print(f"  - {display}")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        console.input()

    def remove_projects(self) -> None:
        """Remove projects."""
        console.clear()
        projects = self.config_manager.get_projects()

        if not projects:
            console.print("[yellow]No projects found.[/yellow]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            console.input()
            return

        # Find removable projects
        non_existent = []
        no_history = []

        for path, project in projects.items():
            if not project.directory_exists:
                non_existent.append(path)
            elif project.history_count == 0:
                no_history.append(path)

        console.print("[bold]Removable projects:[/bold]\n")
        console.print(f"Non-existent directories: {len(non_existent)}")
        console.print(f"No history: {len(no_history)}")

        action = questionary.select(
            "\nWhat to remove?",
            choices=[
                f"Remove non-existent ({len(non_existent)})",
                f"Remove no history ({len(no_history)})",
                "Manual selection",
                "← Back",
            ],
        ).ask()

        if not action or action == "← Back":
            return

        to_remove = []

        if "non-existent" in action:
            to_remove = non_existent
        elif "no history" in action:
            to_remove = no_history
        elif action == "Manual selection":
            choices = []
            for path, project in sorted(projects.items()):
                info = f"[{'✗' if not project.directory_exists else '✓'}] {project.history_count} hist - {path}"
                choices.append(questionary.Choice(title=info, value=path))

            to_remove = (
                questionary.checkbox("Select projects to remove:", choices=choices).ask() or []
            )

        if to_remove:
            console.print(f"\n[yellow]Will remove {len(to_remove)} projects[/yellow]")
            if questionary.confirm("Continue?").ask():
                self.config_manager.create_backup()
                removed = 0
                for path in to_remove:
                    if self.config_manager.remove_project(path):
                        removed += 1

                if self.config_manager.save_config(create_backup=False):
                    console.print(f"[green]Removed {removed} projects[/green]")
                else:
                    console.print("[red]Failed to save[/red]")

                console.print("\n[dim]Press Enter to continue...[/dim]")
        console.input()

    def clear_history(self) -> None:
        """Clear history from projects."""
        console.clear()
        projects = self.config_manager.get_projects()

        projects_with_history = {p: proj for p, proj in projects.items() if proj.history_count > 0}

        if not projects_with_history:
            console.print("[yellow]No projects with history.[/yellow]")
            console.print("\n[dim]Press Enter to continue...[/dim]")
            console.input()
            return

        total_entries = sum(p.history_count for p in projects_with_history.values())
        console.print(f"[bold]Total history entries: {total_entries}[/bold]\n")

        action = questionary.select(
            "What to do?",
            choices=[
                f"Clear all history ({total_entries} entries)",
                "Select specific projects",
                "← Back",
            ],
        ).ask()

        if not action or action == "← Back":
            return

        if "Clear all" in action:
            if questionary.confirm(
                f"Clear {total_entries} entries from {len(projects_with_history)} projects?"
            ).ask():
                self.config_manager.create_backup()
                for project in projects_with_history.values():
                    project.history.clear()
                    self.config_manager.update_project(project)

                if self.config_manager.save_config(create_backup=False):
                    console.print("[green]Cleared all history[/green]")
                else:
                    console.print("[red]Failed to save[/red]")
        else:
            choices = []
            for path, project in sorted(projects_with_history.items()):
                info = f"{project.history_count} entries - {path}"
                choices.append(questionary.Choice(title=info, value=path))

            selected = (
                questionary.checkbox("Select projects to clear:", choices=choices).ask() or []
            )

            if selected:
                total = sum(projects_with_history[p].history_count for p in selected)
                if questionary.confirm(
                    f"Clear {total} entries from {len(selected)} projects?"
                ).ask():
                    self.config_manager.create_backup()
                    for path in selected:
                        project = projects_with_history[path]
                        project.history.clear()
                        self.config_manager.update_project(project)

                    if self.config_manager.save_config(create_backup=False):
                        console.print("[green]Cleared history[/green]")
                    else:
                        console.print("[red]Failed to save[/red]")

        console.print("\n[dim]Press Enter to continue...[/dim]")
        console.input()
