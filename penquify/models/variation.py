"""Photo variation schema — configurable photo imperfections for dataset generation."""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Stain:
    type: str = "coffee"  # coffee, water, grease, ink
    location: str = "upper_right"  # upper_right, center, lower_left, random
    opacity: str = "semi-transparent"  # light, semi-transparent, heavy
    text_obstruction: str = "partial"  # none, partial, severe


@dataclass
class PhotoVariation:
    """Describes how a photo of a document should look.
    These are the variable fields — the system instruction (fixed) handles
    the base behavior of generating realistic operational photos."""

    name: str = "default"

    # Meta / camera
    camera: str = "Samsung Galaxy S8"
    year_device_style: str = "2017 Android"
    aspect_ratio: str = "4:3"
    capture_intent: str = "functional document photo"

    # Scene / framing
    document_coverage: str = "90% of frame"
    background: str = "blurred warehouse hints only at edges"

    # Paper deformation
    curvature: str = "slight"  # none, slight, strong
    folds: str = "none"  # none, middle_vertical, dog_ear, multiple
    wrinkles: str = "minor"  # none, minor, medium, heavy
    corner_bends: str = "none"
    edge_curl: str = "none"

    # Capture style
    angle: str = "slight oblique"  # straight, slight_oblique, strong_oblique_45deg
    skew: str = "slight"  # none, slight, moderate, strong
    rotation_degrees: float = 0  # 0-15
    focus_plane: str = "center sharp, edges softer"

    # Photo artifacts
    motion_blur: bool = False
    blur_direction: str = ""
    glare: str = "mild"  # none, mild, strong
    glare_location: str = ""
    shadow_from_hand: bool = True
    uneven_lighting: bool = True
    jpeg_compression: str = "light"  # none, light, moderate, heavy

    # Hand presence
    hand_visible: bool = True
    grip_type: str = "thumb on lower corner"
    glove: str = "none"

    # Damage / contamination
    stain: Optional[Stain] = None
    dirt_marks: bool = False
    torn_edge: bool = False

    # Failure modes (for dataset edge cases)
    cropped_header: bool = False
    missing_area: str = ""  # "top 10-15%", "left edge"
    overexposure: float = 0.0  # 0.0 (none) to 1.0 (fully washed out)
    shadow_band: bool = False

    # Multi-page
    stapled: bool = False
    stacked_sheets_behind: int = 0

    def to_prompt_json(self) -> dict:
        """Convert to the JSON format expected by the Gemini system instruction."""
        d = {}
        d["meta"] = {
            "camera": self.camera,
            "year_device_style": self.year_device_style,
            "aspect_ratio": self.aspect_ratio,
            "capture_intent": self.capture_intent,
            "quality": "photorealistic handheld operational capture",
            "compression_artifacts": self.jpeg_compression + " jpeg" if self.jpeg_compression != "none" else "none",
            "older_phone_dynamic_range": True,
            "slight_handheld_motion": self.motion_blur,
        }
        d["scene"] = {
            "framing": "document-dominant close capture",
            "document_coverage": self.document_coverage,
            "background_visibility": "minimal edge-only context",
            "background": self.background,
        }
        d["subject"] = {
            "document": "A4 logistics document",
            "held_by": "warehouse worker hand" if self.hand_visible else "resting on surface",
            "paper_condition": f"curvature={self.curvature}, folds={self.folds}, wrinkles={self.wrinkles}",
        }
        d["capture_style"] = {
            "angle": self.angle,
            "skew": self.skew,
            "rotation": f"{self.rotation_degrees} degrees" if self.rotation_degrees else "none",
            "focus_plane": self.focus_plane,
        }
        d["photo_characteristics"] = {
            "partial_shadow_from_hand": self.shadow_from_hand,
            "mild_glare_on_paper": self.glare != "none",
            "motion_blur": self.motion_blur,
            "uneven_lighting": self.uneven_lighting,
        }
        if self.stain:
            d["damage"] = {"stain": self.stain.__dict__}
        if self.cropped_header or self.missing_area:
            d["failure_modes"] = {
                "cropped_header": self.cropped_header,
                "missing_area": self.missing_area,
            }
        if self.stapled or self.stacked_sheets_behind:
            d["multi_page"] = {
                "stapled": self.stapled,
                "stacked_sheets_behind": self.stacked_sheets_behind,
            }
        return d


# Preset variations
PRESETS = {
    "full_picture": PhotoVariation(
        name="full_picture",
        document_coverage="90% of frame",
        curvature="slight",
        angle="slight oblique",
        skew="slight",
    ),
    "folded_skewed": PhotoVariation(
        name="folded_skewed",
        document_coverage="88-93% of frame",
        curvature="strong",
        folds="dog_ear",
        angle="above-right perspective",
        skew="moderate",
        rotation_degrees=6,
    ),
    "zoomed_detail": PhotoVariation(
        name="zoomed_detail",
        document_coverage="95% of frame",
        angle="oblique 25-30 degrees",
        skew="slight",
        focus_plane="center text sharpest",
    ),
    "blurry": PhotoVariation(
        name="blurry",
        motion_blur=True,
        blur_direction="horizontal and downward",
        focus_plane="text-level softness overall",
    ),
    "cropped_header": PhotoVariation(
        name="cropped_header",
        cropped_header=True,
        missing_area="top 10-15% cut off",
    ),
    "strong_oblique": PhotoVariation(
        name="strong_oblique",
        curvature="strong",
        folds="middle_vertical",
        angle="45 degree oblique",
        skew="strong",
    ),
    "coffee_stain": PhotoVariation(
        name="coffee_stain",
        stain=Stain(type="coffee", location="upper_right", opacity="semi-transparent", text_obstruction="partial"),
        wrinkles="medium",
    ),
    "stapled_stack": PhotoVariation(
        name="stapled_stack",
        stapled=True,
        stacked_sheets_behind=2,
        folds="dog_ear",
    ),
}
