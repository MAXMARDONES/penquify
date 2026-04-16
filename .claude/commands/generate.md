---
description: Generate a document PDF + photos from a description or JSON payload. Just describe what you need.
---

# Generate Document

Takes any of these inputs and produces PDF + realistic photos:

1. **Natural language**: "genera una guia de despacho de 5 items de frutas para ACME Warehouse"
2. **JSON payload**: structured header + items
3. **OC number**: if SAP creds are available, reads the OC and generates the guia

## What to do

1. Parse the user's request into a Document JSON
2. Run `penquify pdf` or use the Python API to generate PDF + PNG
3. Optionally generate photos with `penquify photos`

## Example: from description

User says: "genera una guia de 3 items: 20kg frutilla, 10 cajas coca cola, 5 UN servilletas. Proveedor Comercial Sur, para ACME Warehouse"

```bash
cd $(pwd)
GEMINI_API_KEY=$GEMINI_API_KEY python3 -c "
import asyncio, json
from penquify.models import Document, DocHeader, DocItem
from penquify.generators.pdf import generate_document_files

doc = Document(
    header=DocHeader(
        doc_type='guia_despacho', doc_number='00999001', date='$(date +%d/%m/%Y)',
        emitter_name='COMERCIAL SUR LTDA.', emitter_rut='77.000.000-1',
        receiver_name='ACME LOGISTICS S.A.',
        receiver_address='Av. Industrial 2500, Santiago',
        receiver_contact='Bodega Central',
    ),
    items=[
        DocItem(pos=1, code='CS-001', description='FRUTILLA FRESCA', qty=20, unit='KG', unit_price=5990, total=119800),
        DocItem(pos=2, code='CS-002', description='COCA COLA LATA 350CC', qty=10, unit='CJ', unit_price=4290, total=42900),
        DocItem(pos=3, code='CS-003', description='SERVILLETA ESTANDAR', qty=5, unit='UN', unit_price=1500, total=7500),
    ],
)
asyncio.run(generate_document_files(doc, 'output/'))
print('Done! Check output/')
"
```

## Example: generate photos after

```bash
GEMINI_API_KEY=$GEMINI_API_KEY python3 -m penquify.cli photos \
  --image output/guia_despacho_00999001.png \
  --presets full_picture folded_skewed blurry coffee_stain \
  --output output/
```
