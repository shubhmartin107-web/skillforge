from __future__ import annotations

import json
from pathlib import Path

import httpx
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
        raise typer.Exit(1) from e


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


@registry_app.command("publish")
def publish_skill(
    path: str = typer.Argument(..., help="Path to skill directory or .zip file"),
    registry_url: str = typer.Option(
        None, "--registry-url", "-r",
        help="Registry server URL (env: SKILLFORGE_REGISTRY_URL)",
    ),
    api_key: str = typer.Option(
        None, "--api-key", "-k",
        help="API key for authentication (env: SKILLFORGE_API_KEY)",
    ),
):
    import io
    import zipfile

    source_path = Path(path).resolve()
    if not source_path.exists():
        console.print(f"[red]Path not found: {source_path}[/red]")
        raise typer.Exit(1)

    url = registry_url or "http://localhost:8000"

    if source_path.is_file() and source_path.suffix == ".zip":
        manifest_content = None
        with zipfile.ZipFile(source_path, "r") as zf:
            for name in zf.namelist():
                if Path(name).name in ("skill.yaml", "skill.yml"):
                    manifest_content = zf.read(name).decode("utf-8")
                    break
            if not manifest_content:
                console.print("[red]No skill.yaml found in zip file[/red]")
                raise typer.Exit(1)
        zip_data = source_path.read_bytes()
        files = {"files": ("skill.zip", zip_data, "application/zip")}
        data = {"manifest": manifest_content}
    else:
        manifest_path = source_path / "skill.yaml"
        if not manifest_path.exists():
            console.print(f"[red]No skill.yaml found in {source_path}[/red]")
            raise typer.Exit(1)
        manifest_content = manifest_path.read_text("utf-8")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in source_path.rglob("*"):
                if f.is_file():
                    arcname = str(f.relative_to(source_path))
                    zf.write(f, arcname)
        zip_data = zip_buffer.getvalue()
        files = {"files": ("skill.zip", zip_data, "application/zip")}
        data = {"manifest": manifest_content}

    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key

    try:
        resp = httpx.post(
            f"{url}/api/v1/skills/publish",
            data=data,
            files=files,
            headers=headers,
            timeout=60.0,
        )
        resp.raise_for_status()
        result = resp.json()
        console.print(f"[green]✓ Published {result['name']}@{result['version']}[/green]")
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Publish failed: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1) from e
    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1) from e


@registry_app.command("login")
def registry_login(
    registry_url: str = typer.Option(
        None, "--registry-url", "-r",
        help="Registry server URL",
    ),
    api_key: str = typer.Option(
        None, "--api-key", "-k",
        help="API key for authentication",
    ),
):
    creds_dir = Path.home() / ".skillforge"
    creds_dir.mkdir(parents=True, exist_ok=True)
    creds_file = creds_dir / "credentials.json"

    creds = {}
    if creds_file.exists():
        try:
            creds = json.loads(creds_file.read_text("utf-8"))
        except (json.JSONDecodeError, OSError):
            creds = {}

    if registry_url:
        creds["registry_url"] = registry_url
    if api_key:
        creds["api_key"] = api_key

    if not creds.get("registry_url"):
        url = typer.prompt("Registry URL", default="http://localhost:8000")
        creds["registry_url"] = url
    if not creds.get("api_key"):
        key = typer.prompt("API Key")
        creds["api_key"] = key

    creds_file.write_text(json.dumps(creds, indent=2))
    console.print(f"[green]✓ Credentials saved to {creds_file}[/green]")


community_app = typer.Typer(help="Interact with the community skill registry")
registry_app.add_typer(community_app, name="community", help="Community registry commands")


@community_app.command("discover")
def community_discover():
    from skillforge.registry.community import CommunityRegistry

    cr = CommunityRegistry()
    try:
        skills = cr.discover()
        if not skills:
            console.print("[yellow]No community skills found.[/yellow]")
            return
        table = Table(title=f"Community Skills ({len(skills)})")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Description")
        table.add_column("Author")
        table.add_column("Downloads")
        for s in skills:
            table.add_row(
                s.name,
                s.version,
                s.description[:50] + "..." if len(s.description) > 50 else s.description,
                s.author,
                str(s.downloads),
            )
        console.print(table)
    except httpx.HTTPError as e:
        console.print(f"[red]Failed to discover skills: {e}[/red]")
        raise typer.Exit(1) from e


@community_app.command("install")
def community_install(
    name: str = typer.Argument(..., help="Name of the community skill to install"),
):
    from skillforge.registry.community import CommunityRegistry

    cr = CommunityRegistry()
    try:
        entry = cr.install_from_community(name)
        console.print(f"[green]✓ Installed {entry.name}@{entry.version} from community[/green]")
    except httpx.HTTPError as e:
        console.print(f"[red]Failed to install: {e}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        raise typer.Exit(1) from e


@community_app.command("submit")
def community_submit(
    path: str = typer.Argument(..., help="Path to skill directory"),
    api_key: str = typer.Option(
        None, "--api-key", "-k",
        help="API key for community registry authentication",
    ),
):
    from skillforge.registry.community import CommunityRegistry

    key = api_key
    if not key:
        creds_file = Path.home() / ".skillforge" / "credentials.json"
        if creds_file.exists():
            try:
                creds = json.loads(creds_file.read_text("utf-8"))
                key = creds.get("api_key", "")
            except (json.JSONDecodeError, OSError):
                pass
    if not key:
        console.print("[red]API key required. Provide via --api-key or run 'skillforge registry login'[/red]")
        raise typer.Exit(1)

    cr = CommunityRegistry()
    try:
        result = cr.submit_skill(Path(path), key)
        name = result.get("name", "unknown")
        version = result.get("version", "unknown")
        console.print(f"[green]✓ Submitted {name}@{version} to community[/green]")
    except httpx.HTTPError as e:
        console.print(f"[red]Submission failed: {e}[/red]")
        raise typer.Exit(1) from e
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(1) from e
