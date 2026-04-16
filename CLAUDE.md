# Penquify — Python toolkit for synthetic logistics document & photo datasets

## What This Is
Generate PDFs and photorealistic smartphone photos of logistics documents. Three interfaces: CLI tool, Python library, REST API. Uses Gemini 3.1 flash image preview for photo generation.

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
{"mcpServers": {"penquify": {"command": "python3", "args": ["-m", "penquify.mcp"]}}}
```

## Key Directories
- `penquify/templates/` — Jinja2 HTML templates per document type
- `penquify/generators/` — pdf.py (Playwright), photo.py (Gemini), config.py (text→JSON)
- `penquify/models/` — document.py, variation.py, cameras.py
- `penquify/api/` — FastAPI REST server
- `penquify/mcp.py` — MCP server (5 tools)
- `penquify/agent_plugin.py` — Agent SDK plugin
- `tests/` — pytest suite

## Architecture
1. Document JSON → Jinja2 HTML template → Playwright → PDF + PNG
2. PNG + variation JSON → Gemini image gen (system instruction fixed + variation variable) → realistic photo
3. Everything configurable: camera model (free text), paper deformation, failure modes, stains, angles, blur

## Environment
- `GEMINI_API_KEY` — required for photo generation
- `PENQUIFY_OUTPUT` — output directory (default: ~/penquify-output)
- `DATABASE_URL` — PostgreSQL connection (optional)
