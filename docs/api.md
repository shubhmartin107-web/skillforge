# API Reference

## CLI

### `skillforge`

```
Usage: skillforge [OPTIONS] COMMAND [ARGS]...
```

### `skillforge registry`

| Command | Description |
|---------|-------------|
| `list` | List installed skills |
| `search <query>` | Search for skills |
| `install <path>` | Install a skill from path |
| `remove <name>` | Remove a skill |
| `info <name>` | Show skill details |
| `stats` | Show registry statistics |

### `skillforge skill`

| Command | Description |
|---------|-------------|
| `create <name>` | Scaffold a new skill project |
| `run <name>` | Execute a skill |
| `test <name>` | Test a skill with default inputs |
| `validate <path>` | Validate a skill manifest |

### `skillforge workflow`

| Command | Description |
|---------|-------------|
| `run <path>` | Execute a workflow YAML |
| `validate <path>` | Validate workflow syntax and structure |

### `skillforge config`

| Command | Description |
|---------|-------------|
| `show` | Display current configuration |
| `init` | Initialize configuration directory |

### `skillforge dashboard`

Launches the Gradio dashboard at `http://127.0.0.1:7860`

## Python SDK

### `Forge` class

```python
class Forge:
    def install(self, source: str | Path) -> RegistryEntry
    def remove(self, name: str, version: str | None = None) -> bool
    def list_skills(self) -> list[RegistryEntry]
    def search(self, query: str = "", tags: list[str] | None = None) -> SearchResult
    def get_skill(self, name: str) -> RegistryEntry | None
    def run(self, skill_name: str, *, version=None, mode=ExecutionMode.direct, sandbox=False, hooks=None, **inputs) -> ExecutionResult
    def register_skill(self, name, version="0.1.0", description="", inputs=None) -> _SkillRegistrar
    def create_skill(self, name, path=None) -> Path
    def stats(self) -> RegistryStats
```

### `@skill` decorator

```python
from skillforge import skill

@skill(name="my-skill", version="1.0.0", network=False)
def my_function(input1: str) -> dict:
    return {"result": f"Processed: {input1}"}
```

### Models

- `SkillManifest` — Skill definition
- `ExecutionRequest` — Execution parameters
- `ExecutionResult` — Execution output
- `RegistryEntry` — Registry record
- `SearchQuery` / `SearchResult` — Search types
- `RegistryStats` — Registry statistics
