# Contributing to Penquify

## Adding a Document Template

1. Create `penquify/templates/your_template.html` (Jinja2)
2. Use `{{ header.field }}` and `{% for item in items %}` syntax
3. Test: `penquify pdf --template your_template.html --doc-json test.json`

## Adding a Photo Preset

Edit `penquify/models/variation.py` → add to `PRESETS` dict:

```python
PRESETS["my_preset"] = PhotoVariation(
    name="my_preset",
    camera="Samsung Galaxy A10",
    motion_blur=True,
    stain=Stain(type="water", location="center"),
)
```

## Adding a Camera

Edit `penquify/models/cameras.py` → add to `CAMERAS` dict.

## Running Tests

```bash
pip install -e ".[all]"
playwright install chromium
pytest tests/ -v
```

## Code Style

- No linters enforced yet. Keep it readable.
- Type hints appreciated but not required.
- Docstrings on public functions.
