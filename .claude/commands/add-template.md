---
description: Add a new document template (factura, PO, BOL, etc.) to penquify
---

# Add New Document Template

## Steps

1. Create `penquify/templates/{name}.html` as Jinja2 template
2. Use these variables (all available from Document model):
   - `{{ header.doc_number }}`, `{{ header.date }}`, `{{ header.emitter_name }}`, etc.
   - `{% for item in items %}` → `{{ item.description }}`, `{{ item.qty }}`, `{{ item.unit }}`
   - `{{ subtotal }}`, `{{ iva }}`, `{{ total }}`
   - `{{ observations }}`
3. Wrap the document in `<div class="page">` for correct screenshot
4. Test: `penquify pdf --template {name}.html --doc-json test.json`

## Template checklist
- [ ] HTML renders correctly at 210mm width (A4)
- [ ] All header fields used where applicable
- [ ] Items table with ITEM/CODE/DESC/QTY/UM/PRICE/TOTAL columns
- [ ] Totals row (subtotal + IVA + total)
- [ ] Observations section if applicable
- [ ] `.page` wrapper div for Playwright screenshot
- [ ] Monospace font (Courier New) for document realism
- [ ] Barcode area if document has number

## Reference: existing templates
- `guia_despacho.html` — Chilean dispatch guide (complete, tested)
