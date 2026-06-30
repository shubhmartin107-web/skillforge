# Registry

## Local Registry

The local registry stores skill metadata in SQLite and skill files on disk.

### CLI Commands

```bash
# List installed skills
skillforge registry list

# Search for skills
skillforge registry search "web"

# Install a skill from a directory
skillforge registry install ./path/to/skill

# View skill details
skillforge registry info my-skill

# Remove a skill
skillforge registry remove my-skill

# Show registry statistics
skillforge registry stats
```

### Storage

- Database: `~/.skillforge/registry.db`
- Skills: `~/.skillforge/skills/<name>/<version>/`

## Remote Registry

Skills can be discovered and downloaded from:

- GitHub repositories (via API)
- Custom registry URLs (JSON index format)
- Direct download URLs (zip archives)

```python
from skillforge.registry.remote import RemoteRegistry

remote = RemoteRegistry()
skills = remote.fetch_from_github("username/repo")
```

## Dependency Resolution

Skills can declare dependencies on other skills. The resolver:

1. Fetches all installed versions of each dependency
2. Matches version constraints (`>=1.0`, `^1.2.3`, `~1.2.0`)
3. Resolves transitive dependencies recursively
4. Detects circular dependencies
