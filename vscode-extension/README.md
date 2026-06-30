# SkillForge VS Code Extension

Develop, test, and manage SkillForge agent skills directly from VS Code.

## Features

- **Scaffold Skills** — Create new SkillForge skills with a complete directory structure (`skill.yaml`, `skill.py`, `__init__.py`)
- **Run Skills** — Select and execute installed skills with custom inputs
- **Validate Manifests** — Check `skill.yaml` files for correctness
- **Install Skills** — Install skills from your workspace into the local registry
- **Publish Skills** — Publish skills to a SkillForge registry server
- **List Skills** — View all skills installed in the local registry
- **Open Dashboard** — Launch the SkillForge web dashboard
- **Generate OpenAPI Spec** — Generate OpenAPI specifications from your skills
- **Syntax Highlighting** — Rich syntax highlighting for `skill.yaml` files with skillforge-specific keywords
- **Code Snippets** — Handy snippets for creating skill components

## Installation

1. Install the SkillForge CLI:
   ```bash
   pip install skillforge
   ```

2. Install this extension from the VS Code Marketplace or package it manually:
   ```bash
   vsce package
   code --install-extension skillforge-vscode-0.1.0.vsix
   ```

## Requirements

- VS Code 1.85.0 or higher
- SkillForge CLI (`pip install skillforge`)

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `skillforge.registryUrl` | `http://localhost:8000` | URL of the SkillForge registry server |
| `skillforge.apiKey` | `""` | API key for registry authentication |
| `skillforge.pythonPath` | `python3` | Path to Python interpreter for running SkillForge CLI |

## Commands

| Command | Title | Keybinding |
|---------|-------|------------|
| `skillforge.scaffoldSkill` | SkillForge: Scaffold New Skill | `Ctrl+Shift+S` |
| `skillforge.runSkill` | SkillForge: Run Skill | `Ctrl+Shift+R` |
| `skillforge.validateSkill` | SkillForge: Validate Skill | `Ctrl+Shift+V` |
| `skillforge.listSkills` | SkillForge: List Installed Skills | `Ctrl+Shift+L` |
| `skillforge.installSkill` | SkillForge: Install Skill | — |
| `skillforge.publishSkill` | SkillForge: Publish Skill | — |
| `skillforge.openDashboard` | SkillForge: Open Dashboard | — |
| `skillforge.generateOpenApi` | SkillForge: Generate OpenAPI Spec | — |

## Snippets

| Prefix | Description |
|--------|-------------|
| `skillforge-skeleton` | Complete skill.yaml scaffold with all fields |
| `skillforge-input` | Add an input definition |
| `skillforge-output` | Add an output definition |
| `skillforge-permissions` | Add permission block |
| `skillforge-dependency` | Add dependency entry |
| `skillforge-python-run` | Basic skill.py run function |

## Screenshots

> Screenshots coming soon.

## License

MIT
