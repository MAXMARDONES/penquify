<div align="center">

<img src="https://img.shields.io/badge/penquify-v0.1.0-blue?style=for-the-badge&logo=python&logoColor=white" alt="version"/>
<img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="license"/>
<img src="https://img.shields.io/badge/python-3.10+-yellow?style=for-the-badge&logo=python" alt="python"/>
<img src="https://img.shields.io/badge/Gemini-Image%20Gen-purple?style=for-the-badge&logo=google" alt="gemini"/>
<img src="https://img.shields.io/badge/MCP-Server-orange?style=for-the-badge" alt="mcp"/>
<img src="https://img.shields.io/badge/Agent%20SDK-Plugin-cyan?style=for-the-badge" alt="agent-sdk"/>
<img src="https://img.shields.io/badge/Docker-Ready-blue?style=for-the-badge&logo=docker" alt="docker"/>

<br/><br/>

# penquify

> *From Chilean slang **"penca"** (lousy, worse) — because your document photos should look realistically bad, not studio-perfect.*

### Make your documents worse.

A Python toolkit that takes structured data and produces photorealistic smartphone photos of printed logistics documents — with coffee stains, folds, blur, skew, and every imperfection that makes real-world document processing hard.

**CLI tool** | **Python library** | **REST API** | **MCP server** | **Agent SDK plugin**

<br/>

</div>

---

## Demo

```
JSON payload ──► HTML template ──► PDF / PNG ──► Gemini image gen ──► realistic photo
```

**Input:** structured document data (header + items)

```json
{
  "header": {"doc_number": "00847291", "emitter_name": "ACME FOODS LTDA.", "oc_number": "4500000316"},
  "items": [
    {"description": "FROZEN POTATO WEDGES", "qty": 12, "unit": "CJ", "unit_price": 15000},
    {"description": "MOZZARELLA SHREDDED", "qty": 115, "unit": "KG", "unit_price": 4900}
  ]
}
```

**Output:** clean PDF + N realistic photos at different difficulty levels

<!-- TODO: add before/after images here once repo has demo photos -->

```bash
penquify demo  # generates PDF + 8 photo variations in ./output/
```

---

## Getting Started

### Install

```bash
pip install penquify

# or from source
git clone https://github.com/MAXMARDONES/penquify.git
cd penquify && pip install -e ".[all]"

# browser engine for HTML → PDF rendering
playwright install chromium
```

### Environment

```bash
export GEMINI_API_KEY="your-key"   # required for photo generation
export PENQUIFY_OUTPUT="./output"  # where files go (default: ~/penquify-output)
```

### Run

```bash
# Full demo: PDF + 8 photo variations
penquify demo

# PDF only from JSON
penquify pdf --doc-json invoice.json

# Photos from any document image
penquify photos --image scan.png --presets full_picture blurry coffee_stain

# Full dataset: 10 documents x 3 variations each
penquify dataset --doc-json docs.json --presets full_picture folded_skewed blurry
```

### Python

```python
from penquify.models import Document, DocHeader, DocItem, PhotoVariation, Stain
from penquify.generators.pdf import generate_document_files
from penquify.generators.photo import generate_dataset

doc = Document(
    header=DocHeader(doc_type="guia_despacho", doc_number="00847291", date="16/04/2026",
                     emitter_name="ACME FOODS LTDA.", oc_number="4500000316"),
    items=[
        DocItem(pos=1, code="AF-001", description="FROZEN POTATO WEDGES",
                qty=12, unit="CJ", unit_price=15000, total=180000),
    ],
)

files = await generate_document_files(doc, "output/")
photos = await generate_dataset(files["png"], preset_names=["full_picture", "blurry"])
```

---

## Document Templates

| Template | Description | Status |
|---|---|---|
| `guia_despacho` | Chilean dispatch guide (guia de despacho electronica) | **Done** |
| `factura_sii` | Chilean tax invoice (DTE tipo 33, SII XML) | Planned |
| `purchase_order` | Standard purchase order | Planned |
| `bill_of_lading` | Transport bill of lading (BOL) | Planned |
| `nota_credito` | Credit note (DTE tipo 61) | Planned |
| `remito` | Argentine dispatch note | Planned |

Templates are **Jinja2 HTML** — add your own:

```bash
penquify pdf --template my_template.html --doc-json data.json
```

---

## Photo Variations

A fixed **system instruction** handles base realism (paper physics, camera behavior, operational context). The **variation config** controls specifics. Every field is optional — override only what you need.

### 8 Built-in Presets

| Preset | What it tests |
|---|---|
| `full_picture` | Baseline: clean handheld shot, 90% frame coverage |
| `folded_skewed` | Geometric distortion: dog-ear, crease, 6deg tilt |
| `zoomed_detail` | Close-up OCR: tight crop, oblique 25-30deg |
| `blurry` | Motion blur: rushed capture, partial legibility |
| `cropped_header` | Missing data: top 10-15% cut off |
| `strong_oblique` | Extreme angle: 45deg, strong curvature |
| `coffee_stain` | Contamination: stain over text |
| `stapled_stack` | Multi-page: stapled with sheets behind |

### Full Variation Schema

```json
{
  "name": "my_variation",
  "camera": "Samsung Galaxy S8",
  "year_device_style": "2017 Android",
  "aspect_ratio": "4:3",
  "document_coverage": "90% of frame",
  "background": "blurred warehouse at edges",
  "curvature": "slight",
  "folds": "dog_ear",
  "wrinkles": "medium",
  "angle": "45 degree oblique",
  "skew": "strong",
  "rotation_degrees": 8,
  "motion_blur": true,
  "glare": "strong",
  "shadow_from_hand": true,
  "jpeg_compression": "heavy",
  "hand_visible": true,
  "grip_type": "both hands",
  "glove": "warehouse glove",
  "stain": {"type": "coffee", "location": "upper_right", "opacity": "heavy", "text_obstruction": "partial"},
  "cropped_header": true,
  "stapled": true,
  "stacked_sheets_behind": 2
}
```

Every string field is **free text** — cameras, angles, backgrounds, grip types. Use presets or write whatever describes your scenario.

### 22 Camera Presets (+ free text)

`galaxy_s7` `galaxy_s8` `galaxy_a5_2017` `moto_g5` `iphone_7` `iphone_8` `pixel_2` `huawei_p10` `xiaomi_note4` `galaxy_s9` `iphone_xr` `galaxy_a10` `galaxy_a50` `iphone_11` `galaxy_a21s` `iphone_12` `pixel_4a` `galaxy_a13` `iphone_14` `pixel_7` `warehouse_generic` `field_worker`

Or any free text: `PhotoVariation(camera="Nokia 3310 with cracked screen")`

### Natural Language Config

Don't know the schema? Just describe it:

```python
from penquify.generators.config import text_to_variation

config = await text_to_variation(
    "blurry photo with coffee stain, strong angle, old Samsung, paper folded in half"
)
# → returns valid PhotoVariation JSON
```

---

## REST API

```bash
uvicorn penquify.api.server:app --port 8080
```

| Method | Path | Description |
|---|---|---|
| `POST` | `/generate/document` | Document JSON → PDF + PNG |
| `POST` | `/generate/photos` | Image → realistic photos |
| `POST` | `/generate/dataset` | Document → PDF → photos (full pipeline) |
| `POST` | `/generate/config` | Natural language → variation JSON |
| `GET` | `/documents` | List generated runs |
| `GET` | `/documents/{id}/{file}` | Download file |
| `GET` | `/presets` | Photo presets |
| `GET` | `/templates` | Document templates |

---

## MCP Server

5 tools for Claude Desktop, Cursor, Windsurf, or any MCP client:

```json
{
  "mcpServers": {
    "penquify": {
      "command": "python3",
      "args": ["-m", "penquify.mcp"],
      "env": {"GEMINI_API_KEY": "your-key"}
    }
  }
}
```

Tools: `penquify_generate_document` `penquify_generate_photos` `penquify_generate_dataset` `penquify_text_to_config` `penquify_list_presets`

---

## Claude Code Skills

```bash
/penquify          # Full reference: presets, cameras, variation schema
/generate          # Generate a document from description or JSON
/dataset           # Generate large synthetic datasets
/add-template      # Add a new document template
```

---

## Agent SDK Plugin

```python
from penquify.agent_plugin import penquify_tools

agent = Agent(model="claude-sonnet-4-6", tools=penquify_tools)
```

---

## Deployment

### Docker

```bash
docker build -t penquify .
docker run -p 8080:8080 -e GEMINI_API_KEY=xxx penquify
```

### docker-compose (with PostgreSQL)

```bash
GEMINI_API_KEY=xxx docker-compose up
```

### Kubernetes

```bash
kubectl apply -f k8s/secret.yaml   # set GEMINI_API_KEY first
kubectl apply -f k8s/deployment.yaml
```

---

## Architecture

```
penquify/
  templates/         Jinja2 HTML per doc type
  generators/
    pdf.py           HTML → PDF/PNG (Playwright)
    photo.py         PNG → realistic photo (Gemini image gen)
    config.py        text → variation JSON (Gemini text)
  models/
    document.py      DocHeader + DocItem + Document
    variation.py     PhotoVariation + Stain + 8 presets
    cameras.py       22 camera presets + free text
  api/server.py      FastAPI REST
  mcp.py             MCP server (5 tools)
  agent_plugin.py    Agent SDK plugin
  storage/s3.py      AWS S3 upload
  cli.py             CLI entry point
```

---

## Roadmap

- [x] Jinja2 templates + Playwright PDF/PNG
- [x] Gemini photo gen with system instruction + variation config
- [x] 8 photo presets + 22 camera presets
- [x] CLI (`penquify demo/pdf/photos/dataset`)
- [x] FastAPI REST server (8 endpoints)
- [x] MCP server (5 tools)
- [x] Agent SDK plugin
- [x] Claude Code skills (4 commands)
- [x] Natural language → variation JSON (Gemini)
- [x] S3 upload support
- [x] Dockerfile + docker-compose + K8s manifests
- [x] GitHub Actions CI
- [x] CODE_OF_CONDUCT + CONTRIBUTING + LICENSE
- [ ] PostgreSQL persistent storage
- [ ] PostgREST auto-API
- [ ] More templates: factura SII, PO, BOL
- [ ] SII DTE XML generation
- [ ] Batch dataset generation with progress bar
- [ ] PyPI publish
- [ ] Demo images in README

---

## License

MIT

---

<div align="center">
<sub>Built by <a href="https://github.com/MAXMARDONES">Max Mardones</a> — CEO @ <a href="https://getsmartup.ai">getsmartup.ai</a></sub>
</div>
