# Security Model

## Permission System

SkillForge uses a **declarative, capability-based** security model:

- Skills **declare** what capabilities they need
- The runtime **enforces** those boundaries
- Users can **audit** every access

### Declared Permissions

```yaml
permissions:
  network: false                    # No internet access
  filesystem_read: ["/data/**"]     # Read only /data/
  filesystem_write: []              # No write access
  env_vars: ["API_KEY"]             # Can read specific env vars
  dangerous: false                  # No dangerous operations
```

### Enforcement

| Capability | Sandbox | Permission Check |
|------------|---------|-----------------|
| Network | Disabled by default | `permissions.network` |
| File Read | Restricted to declared paths | `permissions.filesystem_read` |
| File Write | Restricted to declared paths | `permissions.filesystem_write` |
| Environment | Only declared vars passed | `permissions.env_vars` |
| Dangerous | Requires explicit flag | `permissions.dangerous` |

## Sandboxing

The subprocess sandbox provides:

- **Temporary working directory** — Deleted after execution
- **Resource limits** — CPU time and memory via `setrlimit`
- **Timeout** — Configurable, default 120s
- **Clean environment** — Only explicitly passed env vars

## Audit Logging

All skill operations are logged to `~/.skillforge/logs/audit.log`:

```json
{"timestamp": "...", "event": "skill.execution", "skill_name": "...", "status": "completed", "duration_ms": 42}
```

Sensitive inputs (containing `key`, `secret`, `password`, `token`, `auth`) are automatically redacted.
