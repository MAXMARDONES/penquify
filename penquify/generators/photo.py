"""Photo generator — Gemini image gen with fixed system instruction + variable JSON."""
import asyncio
import json
import os
from typing import List, Optional

from ..models.variation import PhotoVariation, PRESETS

SYSTEM_INSTRUCTION = """You generate photorealistic operational smartphone photos of physical paper documents captured in real working environments.

Your job is to interpret the incoming JSON as a structured photographic brief and render a believable real-world image, not a graphic design, mockup, flat scan, or studio product shot.

Core goal:
Produce images that look like real handheld photos taken by workers in live operational settings, especially logistics, warehouse, receiving, retail backroom, transportation, field operations, and industrial workflows.

Global behavior rules:
- Treat the document as a real physical object made of paper.
- The paper must behave physically: bending, curling, wrinkling, folding, deforming under grip, reacting to light unevenly.
- The image must look captured by a real phone camera, not digitally composited.
- Preserve realistic imperfections from handheld phone photography: skew, perspective distortion, slight blur, compression, glare, uneven lighting, soft edges, partial shadows, slight framing errors.
- Do not generate scanner-like results unless explicitly requested.
- Do not generate clean graphic mockups or flattened document renders unless explicitly requested.
- Prioritize realism over readability when the JSON asks for operational imperfections.
- If the JSON implies a quick functional capture, the result should feel utilitarian, rushed, and operational rather than aesthetic.
- If the JSON says the document fills most of the frame, ensure background only appears minimally at edges or corners.
- Maintain plausible camera behavior for the requested device generation, especially older smartphones: limited dynamic range, mild over-sharpening, imperfect focus, light JPEG artifacts, blown highlights or crushed shadows when appropriate.
- Text, logos, tables, and printed fields should look like they were photographed from a printed page, not digitally overlaid.
- When requested, include failure modes common to operational document capture: motion blur, clipped fields, stained paper, staples, stacked sheets, folds, angled capture, finger occlusion, partial crop, shadow bands, glare hotspots, perspective keystone distortion.
- The image should feel like evidence of a real operational workflow, not marketing photography.

Document realism rules:
- Assume the document is printed on standard office paper unless otherwise specified.
- Paper must have thickness, slight translucency behavior, natural edge imperfections, and physical response to handling.
- Curvature and folds should affect text geometry naturally.
- Staples, stains, smudges, coffee marks, bent corners, and wrinkles must integrate physically with the paper surface.

Framing rules:
- Prefer handheld close framing for operational capture.
- If a document-first framing is requested, the paper should occupy most of the image.
- Background details should remain secondary, soft, partial, or peripheral unless composition says otherwise.

Lighting rules:
- Lighting must match real ambient conditions of the environment.
- Allow mixed light, harsh daylight, warehouse shadow, fluorescent spill, reflections, glare, and non-uniform exposure.
- Avoid perfect studio lighting.

Camera rules:
- Simulate the requested phone generation and camera limitations.
- Older Android phones should show believable computational photography artifacts and imperfect optics.

Conflict resolution:
- Operational realism overrides beauty.
- Physical document behavior overrides typographic neatness.
- Framing intent overrides scenic composition.
- Variation-specific instructions override default assumptions.

Output style:
- Return a single coherent image matching the JSON.
- No extra graphic elements, borders, UI overlays, captions, or scan effects unless explicitly requested.

CRITICAL: When a reference image of the document is provided, you MUST preserve ALL text, numbers, tables, field values, and formatting from that reference image EXACTLY as shown. Every printed field must be legible and accurate in the output photo."""


async def generate_photo(
    reference_image_path: str,
    variation: PhotoVariation,
    output_path: str,
    api_key: Optional[str] = None,
    doc_description: str = "",
) -> str:
    """Generate a single realistic photo of a document.

    Args:
        reference_image_path: Path to the clean PNG/PDF of the document
        variation: PhotoVariation config describing the photo style
        output_path: Where to save the generated photo
        api_key: Gemini API key (or GEMINI_API_KEY env var)
        doc_description: Optional text describing key fields to preserve

    Returns:
        Path to generated photo
    """
    from google import genai
    from google.genai import types
    from PIL import Image

    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY required")

    client = genai.Client(api_key=key)
    ref_image = Image.open(reference_image_path)

    # Build the user prompt: variation JSON + preservation instructions
    variation_json = json.dumps(variation.to_prompt_json(), indent=2, ensure_ascii=False)

    prompt = f"""Generate a photorealistic photo of this exact document using this variation config:

{variation_json}

{f"Key fields that MUST be legible: {doc_description}" if doc_description else ""}

The generated image must contain this EXACT document with ALL text, numbers, tables, and formatting perfectly preserved and readable."""

    response = await client.aio.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=[ref_image, prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="3:4"),
            system_instruction=[types.Part.from_text(text=SYSTEM_INSTRUCTION)],
        ),
    )

    image = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            image = part.as_image()

    if image is None:
        raise RuntimeError(f"No image generated for variation '{variation.name}'")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    image.save(output_path)
    return output_path


async def generate_dataset(
    reference_image_path: str,
    variations: Optional[List[PhotoVariation]] = None,
    output_dir: str = "output/photos",
    api_key: Optional[str] = None,
    doc_description: str = "",
    preset_names: Optional[List[str]] = None,
) -> List[dict]:
    """Generate a dataset of photos from one document with multiple variations.

    Args:
        reference_image_path: Clean document image
        variations: List of PhotoVariation configs. If None, uses presets.
        output_dir: Where to save photos
        api_key: Gemini API key
        doc_description: Key fields to preserve
        preset_names: If set, use these named presets instead of all presets

    Returns:
        List of {name, path, ok, error?}
    """
    if variations is None:
        if preset_names:
            variations = [PRESETS[n] for n in preset_names if n in PRESETS]
        else:
            variations = list(PRESETS.values())

    os.makedirs(output_dir, exist_ok=True)
    results = []

    for v in variations:
        out = os.path.join(output_dir, f"photo_{v.name}.png")
        try:
            path = await generate_photo(
                reference_image_path, v, out,
                api_key=api_key, doc_description=doc_description,
            )
            results.append({"name": v.name, "path": path, "ok": True})
            print(f"  [OK] {v.name}: {path}")
        except Exception as e:
            results.append({"name": v.name, "path": None, "ok": False, "error": str(e)})
            print(f"  [FAIL] {v.name}: {e}")

    return results
