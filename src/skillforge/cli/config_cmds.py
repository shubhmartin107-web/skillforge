from __future__ import annotations

import typer
from rich.console import Console

from skillforge.config import settings

config_app = typer.Typer(help="View and manage configuration")
console = Console()


@config_app.command("show")
def show_config():
    console.print("[bold cyan]SkillForge Configuration[/bold cyan]")
    console.print(f"  [bold]Home:[/bold] {settings.skillforge_home}")
    console.print(f"  [bold]Registry DB:[/bold] {settings.registry_path}")
    console.print(f"  [bold]Skills Dir:[/bold] {settings.skills_path}")
    console.print(f"  [bold]Cache Dir:[/bold] {settings.cache_path}")
    console.print(f"  [bold]Logs Dir:[/bold] {settings.logs_path}")
    console.print(f"  [bold]Sandbox Enabled:[/bold] {settings.sandbox_enabled}")
    console.print(f"  [bold]Network Enabled:[/bold] {settings.network_enabled}")
    console.print(f"  [bold]Default Runtime:[/bold] {settings.default_runtime}")
    console.print(f"  [bold]Execution Timeout:[/bold] {settings.execution_timeout}s")
    console.print(f"  [bold]Max Memory:[/bold] {settings.max_memory_mb}MB")
    console.print(f"  [bold]DeepSeek API Key:[/bold] {'***' if settings.deepseek_api_key else 'Not set'}")
    console.print(f"  [bold]Gemini API Key:[/bold] {'***' if settings.gemini_api_key else 'Not set'}")
    console.print(f"  [bold]Groq API Key:[/bold] {'***' if settings.groq_api_key else 'Not set'}")
    console.print(f"  [bold]Ollama Base URL:[/bold] {settings.ollama_base_url}")


@config_app.command("init")
def init_config():
    settings.ensure_dirs()
    console.print(f"[green]Initialized SkillForge at {settings.skillforge_home}[/green]")
    console.print("  [dim]Set environment variables with SKILLFORGE_ prefix[/dim]")
    console.print("  [dim]Or create a .env file with settings[/dim]")
