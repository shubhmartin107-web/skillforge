from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from skillforge.composition.workflow import Workflow, WorkflowEngine

workflow_app = typer.Typer(help="Run workflow definitions")
console = Console()


@workflow_app.command("run")
def run_workflow(
    path: str = typer.Argument(..., help="Path to workflow YAML file"),
    inputs: list[str] = typer.Option([], "--input", "-i", help="Input as key=value"),
):
    wf_path = Path(path).resolve()
    if not wf_path.exists():
        console.print(f"[red]Workflow file not found: {wf_path}[/red]")
        raise typer.Exit(1)

    parsed_inputs: dict[str, str] = {}
    for inp in inputs:
        if "=" in inp:
            key, value = inp.split("=", 1)
            parsed_inputs[key] = value

    try:
        workflow = Workflow.from_yaml(wf_path)
    except Exception as e:
        console.print(f"[red]Failed to parse workflow: {e}[/red]")
        raise typer.Exit(1)

    engine = WorkflowEngine()
    try:
        context = engine.run(workflow, inputs=parsed_inputs)
    except Exception as e:
        console.print(f"[red]Workflow execution failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Workflow '{workflow.name}' completed[/green]")
    for key, value in context.items():
        if key.startswith("steps.") and key.endswith(".result"):
            node_id = key.split(".")[1]
            console.print(f"  [bold]{node_id}:[/bold] {value}")


@workflow_app.command("validate")
def validate_workflow(
    path: str = typer.Argument(..., help="Path to workflow YAML file"),
):
    wf_path = Path(path).resolve()
    if not wf_path.exists():
        console.print(f"[red]Workflow file not found: {wf_path}[/red]")
        raise typer.Exit(1)

    try:
        workflow = Workflow.from_yaml(wf_path)
        console.print(f"[green]✓ Valid workflow: {workflow.name} v{workflow.version}[/green]")
        console.print(f"  Nodes: {len(workflow.nodes)}")
        console.print(f"  Start node: {workflow.start_node}")
        for nid, node in workflow.nodes.items():
            console.print(f"    - {nid}: {node.type.value}")
    except Exception as e:
        console.print(f"[red]✗ Invalid workflow: {e}[/red]")
        raise typer.Exit(1)
