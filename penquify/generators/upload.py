"""Upload PDF entry point — detect schema from existing document, then generate variations.

Flow:
  1. User uploads PDF or image
  2. Vision model extracts document schema (blind — no expected values)
  3. Returns detected schema for confirmation
  4. User confirms/edits → generates verified photo variations
"""
import json
import os
from typing import Optional

DETECT_SCHEMA_PROMPT = """You are a document schema detector. You receive a photo or scan of a printed document.

Your job: extract EVERY field you can find, organized by section.

Return a JSON with this structure:
{
  "document_type": "dispatch_guide" | "invoice" | "purchase_order" | "bill_of_lading" | "credit_note" | "other",
  "header": {
    "doc_number": "...",
    "date": "...",
    "emitter_name": "...",
    "emitter_rut": "...",
    "receiver_name": "...",
    "receiver_rut": "...",
    "oc_number": "...",
    ... (any other header fields you find)
  },
  "items": [
    {
      "pos": 1,
      "code": "...",
      "description": "...",
      "qty": ...,
      "unit": "...",
      "unit_price": ...,
      "total": ...
    }
  ],
  "totals": {
    "subtotal": ...,
    "tax": ...,
    "total": ...
  },
  "observations": "...",
  "confidence": 0.0-1.0
}

Extract everything you can read. Leave fields as null if not visible.
For items, extract ALL rows in the table.
Numbers should be numeric (not strings with $ or formatting)."""


async def detect_schema_from_image(
    image_path: str,
    api_key: Optional[str] = None,
) -> dict:
    """Detect document schema from a PDF/image using vision model.

    The model extracts all fields it can find — no expected values.
    Returns structured schema ready for verification pipeline.
    """
    from google import genai
    from google.genai import types
    from PIL import Image

    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY required")

    client = genai.Client(api_key=key)
    img = Image.open(image_path)

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[img, DETECT_SCHEMA_PROMPT],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    text = response.text.strip()
    return json.loads(text)


async def pdf_to_image(pdf_path: str, output_path: str) -> str:
    """Convert first page of PDF to PNG for processing."""
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 900, "height": 1270})
        await page.goto(f"file://{os.path.abspath(pdf_path)}")
        await page.screenshot(path=output_path, full_page=False)
        await browser.close()

    return output_path


def schema_to_flat(detected: dict) -> dict:
    """Convert detected schema to flat field dict for verification."""
    flat = {}

    header = detected.get("header", {})
    for k, v in header.items():
        if v is not None:
            flat[k] = str(v)

    items = detected.get("items", [])
    for i, item in enumerate(items):
        prefix = f"item_{i+1}"
        for k, v in item.items():
            if v is not None:
                flat[f"{prefix}_{k}"] = str(v)

    totals = detected.get("totals", {})
    for k, v in totals.items():
        if v is not None:
            flat[k] = str(v)

    if detected.get("observations"):
        flat["observations"] = detected["observations"]

    return flat


async def upload_and_generate(
    input_path: str,
    output_dir: str = "output/uploaded",
    preset_names: list[str] = None,
    max_retries: int = 2,
    api_key: Optional[str] = None,
) -> dict:
    """Full upload pipeline: PDF/image → detect schema → generate verified photos.

    Args:
        input_path: Path to PDF or image
        output_dir: Where to save outputs
        preset_names: Photo presets to generate
        max_retries: Retries for verification

    Returns:
        {schema, flat_schema, photos: [...]}
    """
    from .verify import generate_verified_photo, build_occlusion_manifest, verify_ground_truth
    from ..models.variation import PRESETS

    os.makedirs(output_dir, exist_ok=True)

    # Convert PDF to image if needed
    if input_path.lower().endswith(".pdf"):
        print("  Converting PDF to image...")
        img_path = os.path.join(output_dir, "source.png")
        await pdf_to_image(input_path, img_path)
    else:
        img_path = input_path

    # Step 1: Detect schema
    print("  Detecting document schema...")
    detected = await detect_schema_from_image(img_path, api_key=api_key)

    schema_path = os.path.join(output_dir, "detected_schema.json")
    with open(schema_path, "w") as f:
        json.dump(detected, f, indent=2, ensure_ascii=False)
    print(f"  Schema: {detected.get('document_type', '?')}, "
          f"{len(detected.get('items', []))} items, "
          f"confidence={detected.get('confidence', '?')}")

    # Step 2: Flatten for verification
    flat = schema_to_flat(detected)
    flat_path = os.path.join(output_dir, "ground_truth.json")
    with open(flat_path, "w") as f:
        json.dump(flat, f, indent=2, ensure_ascii=False)
    print(f"  Ground truth: {len(flat)} fields")

    # Step 3: Generate verified photos
    if preset_names is None:
        preset_names = ["full_picture", "folded_skewed", "blurry"]

    variations = [PRESETS[n] for n in preset_names if n in PRESETS]
    results = []

    for v in variations:
        out_img = os.path.join(output_dir, f"photo_{v.name}.png")
        try:
            result = await generate_verified_photo(
                img_path, v, out_img, flat,
                max_retries=max_retries, api_key=api_key,
            )

            # Save per-image files
            base = os.path.join(output_dir, f"photo_{v.name}")
            with open(f"{base}_verification.json", "w") as f:
                json.dump(result.get("verification", {}), f, indent=2, ensure_ascii=False)
            with open(f"{base}_occlusion.json", "w") as f:
                json.dump(result.get("occlusion_manifest", {}), f, indent=2, ensure_ascii=False)

            results.append(result)
        except Exception as e:
            print(f"  [ERROR] {v.name}: {e}")
            results.append({"name": v.name, "verified": False, "error": str(e)})

    verified = sum(1 for r in results if r.get("verified"))
    print(f"\n  Done: {verified}/{len(results)} verified")

    return {
        "detected_schema": detected,
        "ground_truth": flat,
        "photos": results,
    }
