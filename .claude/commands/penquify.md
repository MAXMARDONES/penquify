---
description: Generate synthetic logistics documents and realistic photos for testing OCR/vision pipelines. Full control over every variable.
---

# Penquify — Document & Photo Generator

Generate PDFs and photorealistic smartphone photos of logistics documents.
Use for OCR benchmarking, agentic vision E2E testing, and synthetic dataset generation.

## Quick Start

```bash
cd /Users/max/mathiesen/penquify
GEMINI_API_KEY=$GEMINI_API_KEY python3 -m penquify.cli demo --output output
```

## Use Cases

### 1. OCR Benchmark Dataset
Generate N variations of the same document to stress-test OCR accuracy:
```python
from penquify.models import PhotoVariation, Stain, PRESETS
from penquify.generators.photo import generate_dataset

# All 8 presets = 8 difficulty levels for the same document
results = await generate_dataset("clean_doc.png")

# Custom difficulty matrix
hard_variations = [
    PhotoVariation(name="blur_strong", motion_blur=True, blur_direction="diagonal", jpeg_compression="heavy"),
    PhotoVariation(name="stain_over_table", stain=Stain(type="coffee", location="center", text_obstruction="severe")),
    PhotoVariation(name="extreme_angle", angle="45 degree oblique", skew="strong", curvature="strong"),
    PhotoVariation(name="cropped_dark", cropped_header=True, glare="strong", uneven_lighting=True),
]
results = await generate_dataset("clean_doc.png", variations=hard_variations)
```

### 2. Agentic Vision E2E Test
Test if your agent can extract fields from realistic photos:
```python
from penquify.models import Document, DocHeader, DocItem, PhotoVariation
from penquify.generators.pdf import generate_document_files
from penquify.generators.photo import generate_photo

# Create the ground truth document
doc = Document(
    header=DocHeader(doc_type="guia_despacho", doc_number="01182034", date="16/04/2026",
                     emitter_name="COMERCIAL AGRO SUR LTDA.", oc_number="4500000316"),
    items=[
        DocItem(pos=1, code="AS-4010", description="PAPA PREFRITA CONGELADA", qty=12, unit="CJ", unit_price=15000),
        DocItem(pos=2, code="AS-2050", description="MOZZARELLA RALLADA", qty=115, unit="KG", unit_price=4900),
    ],
)

# Generate clean PDF (ground truth)
files = await generate_document_files(doc, "output/")

# Generate realistic photo (what the agent will see)
photo = await generate_photo(
    files["png"],
    PhotoVariation(camera="Samsung Galaxy A10", year_device_style="2019 budget Android",
                   curvature="strong", folds="dog_ear", angle="above-right perspective",
                   skew="moderate", rotation_degrees=6, shadow_from_hand=True),
    "output/test_photo.png",
    doc_description="OC 4500000316, guia 01182034, 2 items with codes AS-4010 and AS-2050",
)

# Now test your agent: can it extract OC number, items, quantities from the photo?
```

### 3. Natural Language Variation Config
Don't know the JSON schema? Describe what you want:
```python
from penquify.generators.config import text_to_variation

config = await text_to_variation(
    "foto borrosa con mancha de cafe, tomada desde arriba con un Samsung viejo, "
    "papel doblado por la mitad, una esquina arrugada"
)
# Returns a valid PhotoVariation JSON config
```

## Full Variation Control

Every field is independently configurable. Override only what you need:

```python
PhotoVariation(
    # Camera — free text or preset name
    camera="Motorola Moto G5 Plus",           # any string
    year_device_style="2017 budget Android",   # any string
    aspect_ratio="4:3",                        # "4:3", "16:9", "3:4"

    # Framing
    document_coverage="90% of frame",          # any string
    background="blurred warehouse loading dock",# any string
    capture_intent="quick operational capture", # any string

    # Paper deformation
    curvature="strong",          # none / slight / strong
    folds="dog_ear",             # none / middle_vertical / dog_ear / multiple
    wrinkles="medium",           # none / minor / medium / heavy
    corner_bends="top-right",    # none / any description
    edge_curl="bottom edge",     # none / any description

    # Camera angle
    angle="45 degree oblique",   # straight / slight oblique / above-right / 45 degree
    skew="strong",               # none / slight / moderate / strong
    rotation_degrees=8,          # 0-15
    focus_plane="center sharp, edges softer",  # any description

    # Artifacts
    motion_blur=True,            # bool
    blur_direction="diagonal",   # "" / horizontal / vertical / diagonal
    glare="strong",              # none / mild / strong
    glare_location="upper_right",# "" / upper_right / center / lower_left
    shadow_from_hand=True,       # bool
    uneven_lighting=True,        # bool
    jpeg_compression="heavy",    # none / light / moderate / heavy

    # Hand
    hand_visible=True,           # bool
    grip_type="both hands",      # any description
    glove="warehouse glove",     # none / warehouse glove / latex glove

    # Damage
    stain=Stain(
        type="coffee",           # coffee / water / grease / ink
        location="upper_right",  # upper_right / center / lower_left / random
        opacity="heavy",         # light / semi-transparent / heavy
        text_obstruction="partial", # none / partial / severe
    ),
    dirt_marks=True,             # bool
    torn_edge=False,             # bool

    # Failure modes
    cropped_header=True,         # bool
    missing_area="top 15%",      # "" / any description
    overexposed_patch=True,      # bool
    shadow_band=True,            # bool

    # Multi-page
    stapled=True,                # bool
    stacked_sheets_behind=3,     # 0-5
)
```

## Presets (8 built-in)

| Preset | What it tests |
|---|---|
| `full_picture` | Baseline: clean handheld shot, slight perspective |
| `folded_skewed` | Geometric distortion: dog-ear, crease, trapezoidal |
| `zoomed_detail` | Close-up OCR: tight crop, oblique angle |
| `blurry` | Motion blur: rushed capture, partial legibility |
| `cropped_header` | Missing data: top 10-15% cut off |
| `strong_oblique` | Extreme angle: 45 degrees, strong curvature |
| `coffee_stain` | Contamination: stain over text |
| `stapled_stack` | Multi-page: stapled with sheets behind |

## Cameras (22 presets + free text)

```python
from penquify.models.cameras import CAMERAS, get_camera

# Use a preset
get_camera("galaxy_s8")  # → {"camera": "Samsung Galaxy S8", "year_device_style": "2017 Android"}

# Or any free text
PhotoVariation(camera="Nokia 3310 with cracked screen protector")
```

Available: galaxy_s7, galaxy_s8, galaxy_a5_2017, moto_g5, iphone_7, iphone_8, pixel_2, huawei_p10, xiaomi_note4, galaxy_s9, iphone_xr, galaxy_a10, galaxy_a50, iphone_11, galaxy_a21s, iphone_12, pixel_4a, galaxy_a13, iphone_14, pixel_7, warehouse_generic, field_worker

## Document JSON Format

```json
{
  "header": {
    "doc_type": "guia_despacho",
    "doc_number": "01182034",
    "date": "16/04/2026",
    "emitter_name": "COMERCIAL AGRO SUR LTDA.",
    "emitter_rut": "77.234.567-1",
    "receiver_name": "INMOBILIARIA LUCKY S.A.",
    "oc_number": "4500000316"
  },
  "items": [
    {"code": "AS-4010", "description": "PAPA PREFRITA", "qty": 12, "unit": "CJ", "unit_price": 15000}
  ],
  "observations": "Papa prefrita: 12 cajas. Peso por caja no indicado."
}
```
