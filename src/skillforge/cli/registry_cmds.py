from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from skillforge.models.registry import SearchQuery
from skillforge.registry.installer import InstallError
from skillforge.registry.local import LocalRegistry

registry_app = typer.Typer(help="Manage the skill registry")
console = Console()


@registry_app.command("list")
def list_skills(
    category: str | None = typer.Option(None, "--category", "-c", help="Filter by category"),
    tag: str | None = typer.Option(None, "--tag", "-t", help="Filter by tag"),
):
    reg = LocalRegistry()
    query = SearchQuery()
    if tag:
        query.tags = [tag]
    if category:
        query.categories = [category]
    result = reg.search(query)

    if not result.entries:
        console.print("[yellow]No skills installed.[/yellow]")
        console.print("Install a skill: [green]skillforge registry install <path>[/green]")
        return

    table = Table(title=f"Installed Skills ({result.total})")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description")
    table.add_column("Author")
    table.add_column("Mode")
    table.add_column("Tags")

    for entry in result.entries:
        table.add_row(
            entry.name,
            entry.version,
            entry.description[:50] + "..." if len(entry.description) > 50 else entry.description,
            entry.author_name,
            entry.execution_mode,
            ", ".join(entry.tags[:3]),
        )

    console.print(table)
    reg.close()


@registry_app.command("search")
def search_skills(query_text: str = typer.Argument(..., help="Search query")):
    reg = LocalRegistry()
    query = SearchQuery(query=query_text)
    result = reg.search(query)

    if not result.entries:
        console.print(f"[yellow]No skills found matching '{query_text}'.[/yellow]")
        return

    table = Table(title=f"Search Results for '{query_text}'")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description")
    table.add_column("Author")

    for entry in result.entries:
        table.add_row(entry.name, entry.version, entry.description[:60], entry.author_name)

    console.print(table)
    reg.close()


@registry_app.command("install")
def install_skill(
    source: str = typer.Argument(..., help="Path to skill directory or file"),
):
    source_path = Path(source).resolve()
    if not source_path.exists():
        console.print(f"[red]Source not found: {source}[/red]")
        raise typer.Exit(1)

    from skillforge.registry.installer import Installer
    installer = Installer()

    try:
        entry = installer.install_from_path(source_path)
        console.print(f"[green]Installed {entry.name}@{entry.version}[/green]")
    except InstallError as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        raise typer.Exit(1)


@registry_app.command("remove")
def remove_skill(
    name: str = typer.Argument(..., help="Skill name"),
    version: str | None = typer.Option(None, "--version", "-v", help="Specific version"),
):
    from skillforge.registry.installer import Installer
    installer = Installer()

    if installer.remove(name, version):
        if version:
            console.print(f"[green]Removed {name}@{version}[/green]")
        else:
            console.print(f"[green]Removed {name}[/green]")
    else:
        console.print(f"[yellow]Skill '{name}' not found.[/yellow]")


@registry_app.command("info")
def skill_info(name: str = typer.Argument(..., help="Skill name")):
    reg = LocalRegistry()
    entry = reg.get(name)

    if entry is None:
        console.print(f"[yellow]Skill '{name}' not found.[/yellow]")
        reg.close()
        return

    console.print(f"[bold cyan]{entry.name}[/bold cyan] [green]v{entry.version}[/green]")
    console.print(f"  [bold]Description:[/bold] {entry.description}")
    console.print(f"  [bold]Author:[/bold] {entry.author_name}")
    console.print(f"  [bold]Source:[/bold] {entry.source}")
    console.print(f"  [bold]Mode:[/bold] {entry.execution_mode}")
    console.print(f"  [bold]Tags:[/bold] {', '.join(entry.tags)}")
    console.print(f"  [bold]Categories:[/bold] {', '.join(entry.categories)}")
    console.print(f"  [bold]Dependencies:[/bold] {', '.join(entry.dependencies) if entry.dependencies else 'None'}")
    console.print(f"  [bold]Path:[/bold] {entry.skill_path}")
    console.print(f"  [bold]Installed:[/bold] {entry.installed_at.isoformat()}")
    reg.close()


@registry_app.command("stats")
def registry_stats():
    reg = LocalRegistry()
    stats = reg.stats()
    console.print("[bold cyan]Registry Statistics[/bold cyan]")
    console.print(f"  Skills: {stats.total_skills}")
    console.print(f"  Categories: {stats.total_categories}")
    console.print(f"  Tags: {stats.total_tags}")
    console.print(f"  Authors: {stats.total_authors}")
    reg.close()
