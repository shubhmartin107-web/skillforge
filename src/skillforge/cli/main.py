from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from skillforge import __version__

app = typer.Typer(
    name="skillforge",
    help="Reusable Agent Skills Registry & Runtime — standardized, secure, composable agent capabilities",
    no_args_is_help=True,
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
)
console = Console()

from skillforge.cli.config_cmds import config_app
from skillforge.cli.registry_cmds import registry_app
from skillforge.cli.skill_cmds import skill_app
from skillforge.cli.workflow_cmds import workflow_app

app.add_typer(registry_app, name="registry", help="Manage skill registry")
app.add_typer(skill_app, name="skill", help="Create, run, and test skills")
app.add_typer(config_app, name="config", help="Configuration management")
app.add_typer(workflow_app, name="workflow", help="Define and run workflows")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        _show_banner()


@app.command("version")
def show_version():
    console.print(f"[bold]SkillForge[/bold] [cyan]v{__version__}[/cyan]")


@app.command("install-completions")
def install_completions(
    shell: str = typer.Argument(
        ..., help="Shell type",
        autocompletion=lambda: ["bash", "zsh", "fish", "powershell"],
    ),
):
    import subprocess
    import sys

    try:
        result = subprocess.run(
            [sys.executable, "-m", "typer", "skillforge.cli.main", "utils", "completion", "install"],
            capture_output=True, text=True, env={**__import__("os").environ, "_TYPER_COMPLETE_INSTALL": shell},
        )
        console.print(f"[green]Tab completion installed for {shell}[/green]")
        console.print(f"Restart your shell or run: [bold]source ~/.{shell}rc[/bold]")
    except Exception as e:
        console.print(f"[red]Failed to install completions: {e}[/red]")
        raise typer.Exit(1)


@app.command("install-builtins")
def install_builtins():
    from skillforge.registry.local import LocalRegistry
    from skillforge.skills.builtins import install_builtins as _install_builtins

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description="Installing built-in skills...", total=None)
        reg = LocalRegistry()
        entries = _install_builtins(reg)
        reg.close()

    console.print(f"[green]✓ Installed {len(entries)} built-in skill(s)[/green]")
    for e in entries:
        console.print(f"  [dim]• {e.name}[/dim] [green]v{e.version}[/green]")


@app.command("dashboard")
def dashboard():
    try:
        from skillforge.dashboard.app import run_dashboard
        console.print("[green]Starting SkillForge Dashboard...[/green]")
        console.print("[dim]Open http://127.0.0.1:7860 in your browser[/dim]")
        run_dashboard()
    except ImportError:
        console.print("[red]Dashboard dependencies not installed.[/red]")
        console.print("[yellow]Install: pip install 'skillforge[dashboard]'[/yellow]")
        raise typer.Exit(1)


@app.command("init")
def init_project():
    from skillforge.config import settings
    settings.ensure_dirs()
    console.print("[green]✓ SkillForge initialized[/green]")
    console.print(f"  Home: [cyan]{settings.skillforge_home}[/cyan]")
    console.print(f"  Registry: [cyan]{settings.registry_path}[/cyan]")
    console.print(f"  Skills: [cyan]{settings.skills_path}[/cyan]")

    install_builtins()


def _show_banner():
    console.print()
    console.print(Panel.fit(
        "[bold cyan]⚒  SkillForge[/bold cyan]  [dim]v" + __version__ + "[/dim]\n"
        "[dim]Reusable Agent Skills Registry & Runtime[/dim]\n\n"
        "[bold]Quick Commands:[/bold]\n"
        "  [green]skillforge init[/green]              Initialize and install built-in skills\n"
        "  [green]skillforge skill create[/green]       Scaffold a new skill\n"
        "  [green]skillforge registry list[/green]      List installed skills\n"
        "  [green]skillforge skill run[/green]           Execute a skill\n"
        "  [green]skillforge workflow run[/green]        Run a workflow\n"
        "  [green]skillforge dashboard[/green]           Launch the web dashboard\n\n"
        "[dim]Run [bold]skillforge --help[/bold] for all commands[/dim]",
        title="SkillForge",
        border_style="cyan",
    ))


if __name__ == "__main__":
    app()
