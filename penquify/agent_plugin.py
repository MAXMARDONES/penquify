"""Penquify Agent SDK Plugin — tools for Claude Agent SDK applications.

Usage:
    from penquify.agent_plugin import penquify_tools

    agent = Agent(
        model="claude-sonnet-4-6",
        tools=penquify_tools,
    )
"""
import asyncio
import json
import os
from typing import Optional

from .models import Document, DocHeader, DocItem, PhotoVariation, PRESETS
from .models.cameras import CAMERAS
from .generators.pdf import generate_document_files
from .generators.photo import generate_dataset
from .generators.config import text_to_variation

OUTPUT_DIR = os.environ.get("PENQUIFY_OUTPUT", os.path.expanduser("~/penquify-output"))


async def generate_document(
    doc_number: str,
    date: str,
    emitter_name: str,
    items: list[dict],
    receiver_name: str = "",
    oc_number: str = "",
    observations: str = "",
    doc_type: str = "guia_despacho",
) -> dict:
    """Generate a logistics document (PDF + PNG).

    Args:
        doc_number: Document number (e.g. "01182034")
        date: Date string (e.g. "16/04/2026")
        emitter_name: Company name of emitter
        items: List of {description, qty, unit, unit_price?}
        receiver_name: Receiver company name
        oc_number: Purchase order reference
        observations: Handwritten notes
        doc_type: Template type

    Returns:
        Dict with html, png, pdf file paths
    """
    doc_items = [
        DocItem(pos=i+1, code="", description=it["description"],
                qty=it["qty"], unit=it["unit"],
                unit_price=it.get("unit_price", 0),
                total=it.get("qty", 0) * it.get("unit_price", 0))
        for i, it in enumerate(items)
    ]
    doc = Document(
        header=DocHeader(doc_type=doc_type, doc_number=doc_number, date=date,
                         emitter_name=emitter_name, receiver_name=receiver_name,
                         oc_number=oc_number),
        items=doc_items, observations=observations,
    )
    out_dir = os.path.join(OUTPUT_DIR, f"doc_{doc_number}")
    return await generate_document_files(doc, out_dir)


async def generate_photos(
    image_path: str,
    presets: Optional[list[str]] = None,
    doc_description: str = "",
) -> list[dict]:
    """Generate realistic photos from a document image.

    Args:
        image_path: Path to clean document PNG
        presets: List of preset names (default: full_picture, folded_skewed)
        doc_description: Key fields to preserve

    Returns:
        List of {name, path, ok}
    """
    out_dir = os.path.join(OUTPUT_DIR, "photos")
    return await generate_dataset(
        image_path, output_dir=out_dir,
        preset_names=presets or ["full_picture", "folded_skewed"],
        doc_description=doc_description,
    )


async def describe_to_config(description: str) -> dict:
    """Convert natural language to photo variation config.

    Args:
        description: e.g. "blurry photo with coffee stain, strong angle, old Samsung phone"

    Returns:
        PhotoVariation JSON config
    """
    return await text_to_variation(description)


def list_presets() -> dict:
    """List available presets and cameras."""
    return {
        "presets": list(PRESETS.keys()),
        "cameras": list(CAMERAS.keys()),
    }


# Export as tool-compatible functions
penquify_tools = [generate_document, generate_photos, describe_to_config, list_presets]
