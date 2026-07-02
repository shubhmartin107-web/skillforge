from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from skillforge.models.execution import ExecutionRequest
from skillforge.runtime.executor import Executor

skill_app = typer.Typer(help="Create, run, and test skills")
console = Console()


def _create_skill_files(dest: Path, name: str) -> None:
    dest.mkdir(parents=True)
    (dest / "skill.yaml").write_text(f"""\
name: {name}
version: 0.1.0
description: "A SkillForge skill"
author:
  name: "Your Name"
  contact: ""
inputs:
  - name: message
    type: string
    description: "Input message"
    required: true
outputs:
  - name: result
    type: string
    description: "Output result"
permissions:
  network: false
execution:
  mode: direct
  entrypoint: skill.py
  function: run
tags: []
categories: []
""")

    (dest / "skill.py").write_text("""\
def run(message: str) -> dict:
    return {"result": f"Received: {message}"}
""")

    (dest / "__init__.py").write_text("")

    (dest / "README.md").write_text(f"# {name}\n\nA SkillForge skill.\n")


@skill_app.command("create")
def create_skill(
    name: str = typer.Argument(..., help="Skill name"),
    path: str | None = typer.Option(None, "--path", "-p", help="Output directory"),
):
    dest = Path(path or Path.cwd() / name)
    if dest.exists():
        console.print(f"[red]Directory already exists: {dest}[/red]")
        raise typer.Exit(1)

    _create_skill_files(dest, name)

    console.print(f"[green]Created skill '{name}' at {dest}[/green]")
    console.print("  [dim]Edit skill.yaml and skill.py, then run:[/dim]")
    console.print(f"  [green]skillforge registry install {dest}[/green]")


@skill_app.command("run")
def run_skill(
    name: str = typer.Argument(..., help="Skill name"),
    inputs: list[str] = typer.Option([], "--input", "-i", help="Input key=value"),
    version: str | None = typer.Option(None, "--version", "-v", help="Skill version"),
    sandbox: bool = typer.Option(False, "--sandbox", "-s", help="Run in sandbox"),
):
    parsed_inputs: dict[str, str] = {}
    for inp in inputs:
        if "=" in inp:
            key, value = inp.split("=", 1)
            parsed_inputs[key] = value
        else:
            console.print(
                f"[yellow]Warning: ignoring invalid input '{inp}' (use key=value)[/yellow]"
            )

    req = ExecutionRequest(
        skill_name=name,
        skill_version=version,
        inputs=parsed_inputs,
    )

    executor = Executor()

    try:
        result = executor.execute_in_sandbox(req) if sandbox else executor.execute(req)
    except Exception as e:
        console.print(f"[red]Execution failed: {e}[/red]")
        raise typer.Exit(1) from e

    if result.success:
        console.print("[green]Execution completed successfully[/green]")
        for key, value in result.outputs.items():
            console.print(f"  [bold]{key}:[/bold] {value}")
    else:
        console.print(f"[red]Execution failed: {result.error}[/red]")
        raise typer.Exit(1)


@skill_app.command("test")
def test_skill(
    name: str = typer.Argument(..., help="Skill name"),
):
    import yaml

    from skillforge.models.skill import SkillManifest
    from skillforge.registry.local import LocalRegistry

    reg = LocalRegistry()
    entry = reg.get(name)
    if entry is None:
        console.print(f"[red]Skill '{name}' not found in registry[/red]")
        raise typer.Exit(1)

    manifest_path = Path(entry.manifest_path)
    if not manifest_path.exists():
        console.print(f"[red]Manifest not found: {manifest_path}[/red]")
        raise typer.Exit(1)

    raw = yaml.safe_load(manifest_path.read_text("utf-8"))
    manifest = SkillManifest.from_yaml_dict(raw)

    console.print(f"[bold]Testing {manifest.name} v{manifest.version}[/bold]")
    console.print(f"  Inputs: {len(manifest.inputs)}")
    console.print(f"  Outputs: {len(manifest.outputs)}")
    console.print(f"  Dependencies: {len(manifest.dependencies)}")

    test_inputs: dict[str, object] = {}
    for inp in manifest.inputs:
        if inp.default is not None:
            test_inputs[inp.name] = inp.default
        elif inp.type == "string":
            test_inputs[inp.name] = "test"
        elif inp.type == "integer":
            test_inputs[inp.name] = 0
        elif inp.type == "boolean":
            test_inputs[inp.name] = False
        else:
            test_inputs[inp.name] = None

    console.print(f"\n[bold]Running with inputs:[/bold] {test_inputs}")

    req = ExecutionRequest(skill_name=name, inputs=test_inputs)
    executor = Executor()
    result = executor.execute(req)

    if result.success:
        console.print("[green]  ✓ Skills passed[/green]")
        console.print(f"  Outputs: {result.outputs}")
    else:
        console.print(f"[red]  ✗ Failed: {result.error}[/red]")
        raise typer.Exit(1)

    reg.close()


@skill_app.command("validate")
def validate_skill(
    path: str = typer.Argument(..., help="Path to skill directory or manifest"),
):
    import yaml

    from skillforge.models.skill import SkillManifest

    skill_path = Path(path)
    if skill_path.is_dir():
        for fname in ("skill.yaml", "skill.yml", "skill.json"):
            fpath = skill_path / fname
            if fpath.exists():
                skill_path = fpath
                break

    if not skill_path.exists():
        console.print(f"[red]File not found: {skill_path}[/red]")
        raise typer.Exit(1)

    try:
        content = skill_path.read_text("utf-8")
        if skill_path.suffix == ".json":
            import json

            data = json.loads(content)
        else:
            data = yaml.safe_load(content)
        manifest = SkillManifest.from_yaml_dict(data)
        console.print(f"[green]✓ Valid skill manifest: {manifest.name} v{manifest.version}[/green]")
        console.print(f"  Inputs: {len(manifest.inputs)}")
        console.print(f"  Outputs: {len(manifest.outputs)}")
        console.print(f"  Dependencies: {len(manifest.dependencies)}")
        console.print(
            f"  Permissions: network={manifest.permissions.network}, dangerous={manifest.permissions.dangerous}"
        )
    except Exception as e:
        console.print(f"[red]✗ Invalid manifest: {e}[/red]")
        raise typer.Exit(1) from e


@skill_app.command("openapi")
def openapi_command(
    name: str = typer.Argument(..., help="Skill name or path to skill.yaml"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    format: str = typer.Option("yaml", "--format", "-f", help="Output format: yaml or json"),
):
    from skillforge.runtime.openapi import generate_openapi_json, generate_openapi_yaml

    path_or_name: str | Path = Path(name) if Path(name).exists() else name

    try:
        if format == "json":
            result = generate_openapi_json(path_or_name, output_file=output)
        else:
            result = generate_openapi_yaml(path_or_name, output_file=output)

        if output:
            console.print(f"[green]OpenAPI spec written to {output}[/green]")
        else:
            console.print(result)
    except Exception as e:
        console.print(f"[red]Failed to generate OpenAPI spec: {e}[/red]")
        raise typer.Exit(1) from e
