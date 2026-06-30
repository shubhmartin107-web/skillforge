# Runtime Execution Engine

## Execution Modes

### Direct Execution

The skill's function is imported and called directly in-process.

```python
from skillforge import Forge

forge = Forge()
result = forge.run("my-skill", input1="value")
```

### Tool-Calling Execution

The skill is exposed as an LLM tool definition, compatible with:

- OpenAI function calling
- Anthropic tool use
- Any tool-calling interface

The tool definition is auto-generated from the skill manifest.

### Sandboxed Execution

Skills run in an isolated subprocess with:

- **Filesystem jail**: temporary working directory
- **Resource limits**: CPU time, memory (via `setrlimit`)
- **Network control**: enable/disable as declared
- **Timeout enforcement**: configurable per execution
- **Cleanup**: automatic temp directory removal

```python
result = forge.run("my-skill", sandbox=True, input1="value")
```

## LLM Providers

| Provider | Package | Class | Model Default |
|----------|---------|-------|---------------|
| DeepSeek | `openai` | `DeepSeekProvider` | `deepseek-chat` |
| Gemini | `google-genai` | `GeminiProvider` | `gemini-2.0-flash-exp` |
| Groq | `groq` | `GroqProvider` | `llama-3.3-70b-versatile` |
| Ollama | `ollama` | `OllamaProvider` | `llama3.2` |

## Observability

Execution hooks emit structured events:

- `skill.started` — Execution began
- `skill.completed` — Execution succeeded
- `skill.failed` — Execution failed
- `skill.output` — Output produced

Events are written to `~/.skillforge/logs/audit.log` in JSON-lines format.
