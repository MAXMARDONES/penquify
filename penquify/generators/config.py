"""Config generator — natural language → PhotoVariation JSON via Gemini."""
import json
import os
from typing import Optional


SCHEMA_PROMPT = """You are a configuration generator for Penquify, a synthetic document photo dataset tool.

Given a natural language description of how a photo should look, generate a valid PhotoVariation JSON config.

Available fields and their possible values:

- name: string (identifier for this variation)
- camera: string (free text, e.g. "Samsung Galaxy S8", "iPhone 12", "Motorola Moto G5")
- year_device_style: string (e.g. "2017 Android", "2020 flagship", "2016 budget phone")
- aspect_ratio: "4:3" | "16:9" | "3:4"
- capture_intent: "functional document photo" | "quick operational capture" | "proof of receipt"
- document_coverage: string (e.g. "90% of frame", "85% of frame", "95% tight crop")
- background: string (e.g. "blurred warehouse hints", "truck loading dock edges", "office desk surface")
- curvature: "none" | "slight" | "strong"
- folds: "none" | "middle_vertical" | "dog_ear" | "multiple"
- wrinkles: "none" | "minor" | "medium" | "heavy"
- corner_bends: "none" | "top-right dog-ear" | "lower-left crease"
- edge_curl: "none" | "bottom edge curled" | "all edges curled"
- angle: "straight" | "slight oblique" | "above-right perspective" | "45 degree oblique"
- skew: "none" | "slight" | "moderate" | "strong"
- rotation_degrees: 0-15 (float)
- focus_plane: "uniform sharp" | "center sharp, edges softer" | "text-level softness"
- motion_blur: true | false
- blur_direction: "" | "horizontal" | "vertical" | "diagonal"
- glare: "none" | "mild" | "strong"
- glare_location: "" | "upper_right" | "center" | "lower_left"
- shadow_from_hand: true | false
- uneven_lighting: true | false
- jpeg_compression: "none" | "light" | "moderate" | "heavy"
- hand_visible: true | false
- grip_type: "thumb on lower corner" | "pinched top edge" | "both hands"
- glove: "none" | "warehouse glove" | "latex glove"
- stain: null | {"type": "coffee|water|grease|ink", "location": "upper_right|center|lower_left|random", "opacity": "light|semi-transparent|heavy", "text_obstruction": "none|partial|severe"}
- dirt_marks: true | false
- torn_edge: true | false
- cropped_header: true | false
- missing_area: "" | "top 10-15%" | "left edge" | "bottom 5%"
- overexposure: 0.0-1.0 (float, 0=none, 0.3=light wash, 0.6=moderate bleaching, 1.0=fully washed out)
- shadow_band: true | false
- stapled: true | false
- stacked_sheets_behind: 0-5 (int)

Return ONLY valid JSON, no explanation."""


async def text_to_variation(description: str, api_key: Optional[str] = None) -> dict:
    """Convert natural language to PhotoVariation config JSON."""
    from google import genai
    from google.genai import types

    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY required")

    client = genai.Client(api_key=key)

    response = await client.aio.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{SCHEMA_PROMPT}\n\nDescription: {description}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    text = response.text.strip()
    return json.loads(text)
