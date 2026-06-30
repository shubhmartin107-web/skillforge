# Getting Started with SkillForge

## Installation

```bash
pip install skillforge
```

### Optional Dependencies

```bash
pip install skillforge[dashboard]  # Gradio dashboard
pip install skillforge[deepseek]    # DeepSeek LLM provider
pip install skillforge[gemini]      # Google Gemini provider
pip install skillforge[groq]        # Groq provider
pip install skillforge[ollama]      # Ollama local provider
pip install skillforge[all]         # Everything
```

## Quick Start

### 1. Initialize

```bash
skillforge config init
```

### 2. Create a Skill

```bash
skillforge skill create my-first-skill
cd my-first-skill
```

This creates a skill directory with:
- `skill.yaml` — The manifest/definition
- `skill.py` — The implementation
- `README.md` — Documentation

### 3. Install the Skill

```bash
skillforge registry install ./
```

### 4. Run the Skill

```bash
skillforge skill run my-first-skill -i message="Hello World"
```

### 5. Using the Python SDK

```python
from skillforge import Forge

forge = Forge()

# Run an installed skill
result = forge.run("my-first-skill", message="Hello SDK!")
print(result.outputs)
```

### 6. Launch the Dashboard

```bash
skillforge dashboard
```

Opens at [http://127.0.0.1:7860](http://127.0.0.1:7860)

## Next Steps

- Read the [Skill Standard](skill-standard.md) to define your own skills
- Explore the [Examples](../examples/) directory
- Learn about [Workflows](composition.md) for composing skills
