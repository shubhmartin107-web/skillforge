# Skill Standard v1.0

## Overview

A SkillForge skill is a **self-contained, reusable agent capability** defined by a manifest file (`skill.yaml`) and one or more implementation files.

## Manifest Format

Skills are defined in YAML (or JSON). The manifest describes:

- **Identity**: name, version, author
- **Interface**: typed inputs and outputs
- **Dependencies**: other skills required
- **Permissions**: security capabilities required
- **Execution**: entrypoint, function, runtime mode
- **Metadata**: tags, categories, documentation

## Specification

```yaml
# Required fields
name: string                        # 1-128 chars, alphanumeric-start
version: semver                     # Semantic version (1.0.0, 0.1.0, etc.)

# Optional but recommended
description: string                 # Human-readable description
author:
  name: string
  contact: string                   # Email or URL

# Input/output contract
inputs:
  - name: string                    # Input parameter name
    type: "string" | "integer" | "float" | "boolean" | "list" | "object" | "any"
    description: string
    required: boolean               # Default: true
    default: any                    # Default value

outputs:
  - name: string
    type: string
    description: string

# Dependencies on other skills
dependencies:
  - name: string                    # Skill name
    version: string                 # Semver constraint: ">=1.0", "^1.2", "*"
    source: "builtins" | "local" | "remote"

# Security permissions
permissions:
  network: boolean                  # Internet access
  filesystem_read: list[string]     # Allowed read paths
  filesystem_write: list[string]    # Allowed write paths
  env_vars: list[string]            # Allowed environment variables
  dangerous: boolean                # Dangerous operations flag

# Execution configuration
execution:
  mode: "direct" | "tool_calling" | "sub_agent"
  entrypoint: string                # File path (e.g., "skill.py")
  function: string                  # Function name to call (e.g., "run")
  runtime: "python3.12"             # Runtime identifier

# Metadata
tags: list[string]
categories: list[string]
license: string
documentation: string
examples:
  - inputs: {...}
    description: string
```

## Execution Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `direct` | Function is called directly with inputs | Simple, fast invocations |
| `tool_calling` | Exposed as LLM tool definition | Agent frameworks (OpenAI, Anthropic) |
| `sub_agent` | Spawns an autonomous sub-agent | Complex multi-step tasks |

## Naming Conventions

- Skill names: lowercase, hyphen-separated (`web-page-fetcher`)
- Versions: strict semantic versioning (`1.2.3`)
- Files: `skill.yaml` or `skill.yml` for manifest

## Packaging

A skill is a directory containing:

```
my-skill/
├── skill.yaml           # Required: manifest
├── skill.py             # Required: implementation
├── requirements.txt     # Optional: Python dependencies
├── README.md            # Optional: documentation
└── tests/               # Optional: test files
```

Skills can be distributed as directories (development) or zip archives (publishing).
