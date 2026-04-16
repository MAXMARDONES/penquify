# Penquify — Python toolkit for synthetic logistics document & photo datasets

## IMPORTANT: This is an open source repository

This repo is public on GitHub. Thousands of people may fork it, read it, and use AI agents on it. Follow these rules strictly:

### Security rules for AI agents working on this repo
- **NEVER commit API keys, secrets, passwords, or tokens** — not in code, not in configs, not in comments, not in examples. Use `env:VAR_NAME` or `$VAR_NAME` placeholders only.
- **NEVER include real company data** — use ACME, example.com, placeholder names. No real RUTs, phone numbers, addresses, or employee names.
- **NEVER modify `.github/workflows/` to add write permissions** or third-party actions without explicit owner approval.
- **NEVER add post-install scripts** or anything that executes on `pip install`.
- **NEVER add dependencies without justification** — every new package is a supply chain risk.
- **All PRs require review from @MAXMARDONES** — no self-merging, no bypassing branch protection.
- **Pin dependency versions** — no `>=` without upper bound in production deps.
- If you find a security issue, do NOT open a public issue. Email max@getsmartup.ai.

### Code quality rules
- Tests must pass before any PR
- No credentials in Docker images — inject via env vars at runtime
- `.env` files are gitignored — never override this
- Example configs use placeholder values only

---

## What This Is
Generate PDFs and photorealistic smartphone photos of logistics documents. Three interfaces: CLI tool, Python library, REST API. Plus MCP server and Agent SDK plugin. Uses Gemini 3.1 flash image preview for photo generation.

## Quick Reference

### CLI
```bash
penquify demo                                    # Full pipeline demo
penquify pdf --doc-json doc.json                 # PDF only
penquify photos --image doc.png --presets blurry # Photos from image
penquify dataset --doc-json doc.json             # Doc + all photo variations
```

### Python
```python
from penquify.models import Document, DocHeader, DocItem, PhotoVariation, Stain
from penquify.models.cameras import CAMERAS, get_camera
from penquify.generators.pdf import generate_document_files
from penquify.generators.photo import generate_dataset, generate_photo
from penquify.generators.config import text_to_variation
```

### API
```bash
uvicorn penquify.api.server:app --port 8080
# POST /generate/document, /generate/photos, /generate/dataset, /generate/config
```

### MCP Server
```json
{"mcpServers": {"penquify": {"command": "python3", "args": ["-m", "penquify.mcp"], "env": {"GEMINI_API_KEY": "env:GEMINI_API_KEY"}}}}
```

## Key Directories
- `penquify/templates/` — Jinja2 HTML templates per document type
- `penquify/generators/` — pdf.py (Playwright), photo.py (Gemini), config.py (text→JSON)
- `penquify/models/` — document.py, variation.py, cameras.py
- `penquify/api/` — FastAPI REST server
- `penquify/mcp.py` — MCP server (5 tools)
- `penquify/agent_plugin.py` — Agent SDK plugin
- `tests/` — pytest suite
- `k8s/` — Kubernetes deployment manifests
- `SECURITY.md` — security policy, merge rules, API key management

## Architecture
1. Document JSON → Jinja2 HTML template → Playwright → PDF + PNG
2. PNG + variation JSON → Gemini image gen (system instruction fixed + variation variable) → realistic photo
3. Everything configurable: camera model (free text), paper deformation, failure modes, stains, angles, blur

## Environment
- `GEMINI_API_KEY` — required for photo generation. NEVER hardcode.
- `PENQUIFY_OUTPUT` — output directory (default: ~/penquify-output)
- `DATABASE_URL` — PostgreSQL connection (optional)
