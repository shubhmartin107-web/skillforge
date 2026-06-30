# Composed Workflow Example

This example demonstrates composing multiple skills into a research workflow:

1. **web-page-fetcher** — Fetches content from a URL
2. **data-analyzer** — Analyzes extracted content
3. **hello-world** — Fallback skill

## Running

```bash
# First install the required skills
skillforge registry install ../hello-world/
skillforge registry install ../web-scraper/
skillforge registry install ../data-analysis/

# Run the workflow
skillforge workflow run research-workflow.yaml -i topic="https://example.com"
```
