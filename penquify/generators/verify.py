"""Ground truth verification — verify generated photos against source schema.

Pipeline:
  1. Generate photo from clean document
  2. Send generated photo + source schema to vision model
  3. Extract every field from the photo
  4. Compare extracted vs source values
  5. Flag mismatches → retry or report
  6. Build occlusion manifest (which fields are intentionally hidden)
"""
import json
import os
from typing import Optional

from ..models.document import Document
from ..models.variation import PhotoVariation


EXTRACT_PROMPT = """You are a document field extractor. You receive a photo of a printed document and a list of field names to look for.

Your ONLY job: extract the value of each field from the photo. You do NOT know the correct values — just read what you see.

For each field:
- If you can read it clearly: return the extracted value + confidence 0.8-1.0
- If you can partially read it: return your best guess + confidence 0.3-0.7
- If you cannot read it (blurry, cropped, covered): return null + confidence 0.0 + reason

FIELDS TO EXTRACT:
{field_names_json}

Return ONLY this JSON:
{{
  "extractions": {{
    "<field_name>": {{
      "value": "<what you read>" or null,
      "confidence": 0.0-1.0,
      "reason": null or "blurry" or "cropped" or "occluded" or "not_in_frame"
    }}
  }}
}}"""


def _schema_from_document(doc: Document) -> dict:
    """Extract verifiable fields from a Document into a flat schema."""
    schema = {}
    h = doc.header

    # Header fields
    if h.doc_number: schema["doc_number"] = h.doc_number
    if h.date: schema["date"] = h.date
    if h.emitter_name: schema["emitter_name"] = h.emitter_name
    if h.emitter_rut: schema["emitter_rut"] = h.emitter_rut
    if h.receiver_name: schema["receiver_name"] = h.receiver_name
    if h.receiver_rut: schema["receiver_rut"] = h.receiver_rut
    if h.oc_number: schema["oc_number"] = h.oc_number
    if h.oc_date: schema["oc_date"] = h.oc_date
    if h.vehicle_plate: schema["vehicle_plate"] = h.vehicle_plate
    if h.driver_name: schema["driver_name"] = h.driver_name
    if h.received_by: schema["received_by"] = h.received_by

    # Item fields
    for i, item in enumerate(doc.items):
        prefix = f"item_{i+1}"
        if item.code: schema[f"{prefix}_code"] = item.code
        schema[f"{prefix}_description"] = item.description
        schema[f"{prefix}_qty"] = str(item.qty)
        schema[f"{prefix}_unit"] = item.unit
        if item.unit_price: schema[f"{prefix}_unit_price"] = str(int(item.unit_price))
        if item.total: schema[f"{prefix}_total"] = str(int(item.total))

    # Totals
    schema["subtotal"] = str(int(doc.subtotal))
    schema["total"] = str(int(doc.total))

    return schema


def _schema_from_dict(data: dict) -> dict:
    """Extract verifiable fields from a raw dict (for uploaded docs)."""
    schema = {}
    if "header" in data:
        for k, v in data["header"].items():
            if v: schema[k] = str(v)
    if "items" in data:
        for i, item in enumerate(data["items"]):
            prefix = f"item_{i+1}"
            for k, v in item.items():
                if v: schema[f"{prefix}_{k}"] = str(v)
    return schema


async def extract_fields(
    image_path: str,
    field_names: list[str],
    api_key: Optional[str] = None,
) -> dict:
    """Blind extraction — model reads the photo without knowing expected values.

    Args:
        image_path: Path to the photo
        field_names: List of field names to look for

    Returns:
        {"extractions": {"field_name": {"value": str|None, "confidence": float, "reason": str|None}}}
    """
    from google import genai
    from google.genai import types
    from PIL import Image

    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY required")

    client = genai.Client(api_key=key)
    photo = Image.open(image_path)

    field_names_json = json.dumps(field_names, indent=2)
    prompt = EXTRACT_PROMPT.format(field_names_json=field_names_json)

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=[photo, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    text = response.text.strip()
    return json.loads(text)


def _normalize(val: str) -> str:
    """Normalize a value for comparison: strip, lowercase, remove formatting."""
    if val is None:
        return ""
    s = str(val).strip().lower()
    # Remove common formatting: $, commas, dots in thousands
    s = s.replace("$", "").replace(",", "").replace(".", "").strip()
    return s


def compare_against_ground_truth(
    extractions: dict,
    schema: dict,
) -> dict:
    """Programmatic comparison — no model involved.

    Args:
        extractions: Output from extract_fields()
        schema: Flat dict of field_name → expected_value

    Returns:
        Verification result with per-field status + summary
    """
    fields = {}
    matched = mismatched = illegible = not_visible = 0

    for field_name, expected in schema.items():
        ext = extractions.get("extractions", {}).get(field_name, {})
        extracted_value = ext.get("value")
        confidence = ext.get("confidence", 0)
        reason = ext.get("reason")

        if extracted_value is None or confidence == 0:
            if reason in ("cropped", "not_in_frame"):
                status = "not_visible"
                not_visible += 1
            else:
                status = "illegible"
                illegible += 1
        elif confidence < 0.5:
            status = "illegible"
            illegible += 1
        elif _normalize(extracted_value) == _normalize(expected):
            status = "match"
            matched += 1
        else:
            status = "mismatch"
            mismatched += 1

        fields[field_name] = {
            "source_value": expected,
            "extracted_value": extracted_value,
            "status": status,
            "confidence": confidence,
            "extraction_reason": reason,
        }

    total = len(schema)
    return {
        "fields": fields,
        "summary": {
            "total_fields": total,
            "matched": matched,
            "mismatched": mismatched,
            "illegible": illegible,
            "not_visible": not_visible,
        },
    }


async def verify_ground_truth(
    image_path: str,
    schema: dict,
    api_key: Optional[str] = None,
) -> dict:
    """Full verification pipeline: blind extract → programmatic compare.

    The vision model NEVER sees the expected values. It only extracts.
    Comparison is done in code — no model bias.
    """
    # Step 1: Blind extraction (model doesn't know ground truth)
    extractions = await extract_fields(
        image_path, list(schema.keys()), api_key=api_key,
    )

    # Step 2: Programmatic comparison (no model involved)
    verification = compare_against_ground_truth(extractions, schema)

    return verification


def build_occlusion_manifest(
    verification: dict,
    variation: PhotoVariation,
) -> dict:
    """Cross-reference failed fields with variation config to explain WHY.

    If a field is not_visible or illegible, check if the variation config
    explains it (crop, stain, blur, etc.).

    Returns:
        Dict of field_name → status with occlusion reason
    """
    manifest = {}
    fields = verification.get("fields", {})

    for field_name, field_data in fields.items():
        status = field_data.get("status", "match")

        if status == "match":
            manifest[field_name] = "visible"
            continue

        # Determine occlusion reason from variation config
        reasons = []

        if status == "not_visible":
            if variation.cropped_header or variation.missing_area:
                reasons.append(f"occluded_by_crop({variation.missing_area or 'header'})")
            if variation.stain and variation.stain.text_obstruction in ("partial", "severe"):
                reasons.append(f"obscured_by_{variation.stain.type}_stain({variation.stain.location})")
            if variation.stapled and variation.stacked_sheets_behind:
                reasons.append("hidden_behind_stacked_page")
            if variation.hand_visible:
                reasons.append("possible_finger_occlusion")

        elif status == "illegible":
            if variation.motion_blur:
                reasons.append(f"blurred_by_motion({variation.blur_direction or 'general'})")
            if variation.overexposure > 0:
                reasons.append(f"washed_out_by_overexposure(intensity={variation.overexposure:.1f})")
            if variation.jpeg_compression in ("moderate", "heavy"):
                reasons.append(f"degraded_by_compression({variation.jpeg_compression})")
            if variation.glare in ("strong",):
                reasons.append(f"washed_out_by_glare({variation.glare_location or 'general'})")
            if "45" in variation.angle or variation.skew == "strong":
                reasons.append("distorted_by_extreme_angle")
            if variation.curvature == "strong":
                reasons.append("warped_by_paper_curvature")
            if variation.stain and variation.stain.text_obstruction in ("partial", "severe"):
                reasons.append(f"obscured_by_{variation.stain.type}_stain({variation.stain.location})")

        elif status == "mismatch":
            reasons.append("hallucinated_or_garbled_by_image_gen")

        manifest[field_name] = {
            "status": status,
            "extracted": field_data.get("extracted_value"),
            "expected": field_data.get("source_value"),
            "confidence": field_data.get("confidence"),
            "reasons": reasons or ["unknown"],
        }

    return manifest


async def generate_verified_photo(
    reference_image_path: str,
    variation: PhotoVariation,
    output_path: str,
    schema: dict,
    max_retries: int = 3,
    api_key: Optional[str] = None,
    doc_description: str = "",
) -> dict:
    """Generate a photo and verify it. Retry on mismatches.

    Returns:
        {
            "image_path": str,
            "verified": bool,
            "attempts": int,
            "ground_truth": dict,    # source schema
            "verification": dict,     # per-field verification
            "occlusion_manifest": dict,  # why each field failed
        }
    """
    from .photo import generate_photo

    for attempt in range(1, max_retries + 1):
        # Generate
        path = await generate_photo(
            reference_image_path, variation, output_path,
            api_key=api_key, doc_description=doc_description,
        )

        # Verify
        verification = await verify_ground_truth(path, schema, api_key=api_key)
        manifest = build_occlusion_manifest(verification, variation)

        summary = verification.get("summary", {})
        mismatched = summary.get("mismatched", 0)

        # If no mismatches (illegible/not_visible are OK — those are intentional from variation)
        if mismatched == 0:
            print(f"  [VERIFIED] {variation.name}: attempt {attempt}, "
                  f"{summary.get('matched',0)} match, "
                  f"{summary.get('illegible',0)} illegible, "
                  f"{summary.get('not_visible',0)} not_visible")
            return {
                "image_path": path,
                "verified": True,
                "attempts": attempt,
                "ground_truth": schema,
                "verification": verification,
                "occlusion_manifest": manifest,
            }

        # Mismatches found — these are image gen errors, not intentional occlusions
        mismatch_fields = [
            f for f, d in verification.get("fields", {}).items()
            if d.get("status") == "mismatch"
        ]
        print(f"  [RETRY {attempt}/{max_retries}] {variation.name}: "
              f"{mismatched} mismatched fields: {mismatch_fields}")

        # Update doc_description to emphasize the mismatched fields
        doc_description = (
            f"CRITICAL: These fields were WRONG in the previous attempt and MUST be fixed: "
            f"{', '.join(f'{f}={schema[f]}' for f in mismatch_fields if f in schema)}. "
            f"Preserve EXACTLY these values."
        )

    # Exhausted retries
    print(f"  [FAILED] {variation.name}: {mismatched} mismatches after {max_retries} attempts")
    return {
        "image_path": path,
        "verified": False,
        "attempts": max_retries,
        "ground_truth": schema,
        "verification": verification,
        "occlusion_manifest": manifest,
    }


async def generate_verified_dataset(
    reference_image_path: str,
    document: Document,
    variations: list[PhotoVariation] = None,
    output_dir: str = "output",
    api_key: Optional[str] = None,
    preset_names: list[str] = None,
    max_retries: int = 3,
) -> list[dict]:
    """Generate a full verified dataset.

    Returns list of results, each with image_path, ground_truth, verification, occlusion_manifest.
    Also writes ground_truth.json and occlusion_manifest.json per image.
    """
    from ..models.variation import PRESETS

    if variations is None:
        if preset_names:
            variations = [PRESETS[n] for n in preset_names if n in PRESETS]
        else:
            variations = list(PRESETS.values())

    os.makedirs(output_dir, exist_ok=True)
    schema = _schema_from_document(document)

    # Write master ground truth
    gt_path = os.path.join(output_dir, "ground_truth.json")
    with open(gt_path, "w") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    results = []
    for v in variations:
        out_img = os.path.join(output_dir, f"photo_{v.name}.png")
        try:
            result = await generate_verified_photo(
                reference_image_path, v, out_img, schema,
                max_retries=max_retries, api_key=api_key,
            )

            # Write per-image manifests
            base = os.path.join(output_dir, f"photo_{v.name}")
            with open(f"{base}_verification.json", "w") as f:
                json.dump(result["verification"], f, indent=2, ensure_ascii=False)
            with open(f"{base}_occlusion.json", "w") as f:
                json.dump(result["occlusion_manifest"], f, indent=2, ensure_ascii=False)

            results.append(result)
        except Exception as e:
            print(f"  [ERROR] {v.name}: {e}")
            results.append({"name": v.name, "verified": False, "error": str(e)})

    # Summary
    verified = sum(1 for r in results if r.get("verified"))
    total = len(results)
    print(f"\nDataset: {verified}/{total} verified, {total - verified} failed")

    # Write dataset summary
    summary_path = os.path.join(output_dir, "dataset_summary.json")
    with open(summary_path, "w") as f:
        json.dump({
            "total": total,
            "verified": verified,
            "failed": total - verified,
            "results": [{
                "name": r.get("name", os.path.basename(r.get("image_path", ""))),
                "verified": r.get("verified", False),
                "attempts": r.get("attempts", 0),
                "summary": r.get("verification", {}).get("summary", {}),
            } for r in results],
        }, f, indent=2)

    return results
