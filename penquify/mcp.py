#!/usr/bin/env python3
"""Penquify MCP Server — exposes document/photo generation as MCP tools.

Usage in claude_desktop_config.json or .claude/settings.json:
{
  "mcpServers": {
    "penquify": {
      "command": "python3",
      "args": ["-m", "penquify.mcp"],
      "env": {"GEMINI_API_KEY": "your-key"}
    }
  }
}
"""
import asyncio
import json
import os
import sys
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
    sys.exit(1)

from .models import Document, DocHeader, DocItem, PhotoVariation, PRESETS
from .models.cameras import CAMERAS
from .generators.pdf import generate_document_files
from .generators.photo import generate_dataset, generate_photo
from .generators.config import text_to_variation

server = Server("penquify")
OUTPUT_DIR = os.environ.get("PENQUIFY_OUTPUT", os.path.expanduser("~/penquify-output"))


@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="penquify_generate_document",
            description="Generate a logistics document (PDF + PNG) from structured data. Returns file paths.",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_type": {"type": "string", "description": "Template: guia_despacho, factura_sii, purchase_order, bill_of_lading", "default": "guia_despacho"},
                    "doc_number": {"type": "string"},
                    "date": {"type": "string", "description": "DD/MM/YYYY"},
                    "emitter_name": {"type": "string"},
                    "receiver_name": {"type": "string"},
                    "oc_number": {"type": "string", "default": ""},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "qty": {"type": "number"},
                                "unit": {"type": "string"},
                                "unit_price": {"type": "number", "default": 0},
                            },
                            "required": ["description", "qty", "unit"],
                        },
                    },
                    "observations": {"type": "string", "default": ""},
                },
                "required": ["doc_number", "date", "emitter_name", "items"],
            },
        ),
        Tool(
            name="penquify_generate_photos",
            description="Generate realistic smartphone photos of a document image. Returns photo file paths.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_path": {"type": "string", "description": "Path to document PNG/PDF"},
                    "presets": {
                        "type": "array",
                        "items": {"type": "string", "enum": list(PRESETS.keys())},
                        "description": "Photo variation presets to generate",
                        "default": ["full_picture", "folded_skewed"],
                    },
                    "doc_description": {"type": "string", "description": "Key fields to preserve in photos", "default": ""},
                },
                "required": ["image_path"],
            },
        ),
        Tool(
            name="penquify_generate_dataset",
            description="Full pipeline: document data → PDF → realistic photos. Returns all file paths.",
            inputSchema={
                "type": "object",
                "properties": {
                    "doc_number": {"type": "string"},
                    "date": {"type": "string"},
                    "emitter_name": {"type": "string"},
                    "receiver_name": {"type": "string", "default": ""},
                    "oc_number": {"type": "string", "default": ""},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "qty": {"type": "number"},
                                "unit": {"type": "string"},
                                "unit_price": {"type": "number", "default": 0},
                            },
                            "required": ["description", "qty", "unit"],
                        },
                    },
                    "presets": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["full_picture", "folded_skewed", "blurry"],
                    },
                },
                "required": ["doc_number", "date", "emitter_name", "items"],
            },
        ),
        Tool(
            name="penquify_text_to_config",
            description="Convert natural language to a photo variation JSON config. Example: 'blurry photo with coffee stain taken from above'",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "Natural language description of desired photo variation"},
                },
                "required": ["description"],
            },
        ),
        Tool(
            name="penquify_list_presets",
            description="List all available photo variation presets and camera models.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if name == "penquify_list_presets":
        result = {
            "presets": list(PRESETS.keys()),
            "cameras": list(CAMERAS.keys()),
            "preset_details": {k: v.to_prompt_json() for k, v in PRESETS.items()},
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    if name == "penquify_text_to_config":
        config = await text_to_variation(arguments["description"])
        return [TextContent(type="text", text=json.dumps(config, indent=2))]

    if name == "penquify_generate_document":
        items = [DocItem(pos=i+1, code="", description=it["description"],
                         qty=it["qty"], unit=it["unit"],
                         unit_price=it.get("unit_price", 0),
                         total=it.get("qty", 0) * it.get("unit_price", 0))
                 for i, it in enumerate(arguments.get("items", []))]

        doc = Document(
            header=DocHeader(
                doc_type=arguments.get("doc_type", "guia_despacho"),
                doc_number=arguments["doc_number"],
                date=arguments["date"],
                emitter_name=arguments["emitter_name"],
                receiver_name=arguments.get("receiver_name", ""),
                oc_number=arguments.get("oc_number", ""),
            ),
            items=items,
            observations=arguments.get("observations", ""),
        )

        out_dir = os.path.join(OUTPUT_DIR, f"doc_{doc.header.doc_number}")
        files = await generate_document_files(doc, out_dir)
        return [TextContent(type="text", text=json.dumps(files, indent=2))]

    if name == "penquify_generate_photos":
        image_path = arguments["image_path"]
        if not os.path.exists(image_path):
            return [TextContent(type="text", text=f"Error: {image_path} not found")]

        presets = arguments.get("presets", ["full_picture", "folded_skewed"])
        out_dir = os.path.join(OUTPUT_DIR, "photos")
        results = await generate_dataset(
            image_path, output_dir=out_dir, preset_names=presets,
            doc_description=arguments.get("doc_description", ""),
        )
        return [TextContent(type="text", text=json.dumps(results, indent=2, default=str))]

    if name == "penquify_generate_dataset":
        items = [DocItem(pos=i+1, code="", description=it["description"],
                         qty=it["qty"], unit=it["unit"],
                         unit_price=it.get("unit_price", 0),
                         total=it.get("qty", 0) * it.get("unit_price", 0))
                 for i, it in enumerate(arguments.get("items", []))]

        doc = Document(
            header=DocHeader(
                doc_type="guia_despacho",
                doc_number=arguments["doc_number"],
                date=arguments["date"],
                emitter_name=arguments["emitter_name"],
                receiver_name=arguments.get("receiver_name", ""),
                oc_number=arguments.get("oc_number", ""),
            ),
            items=items,
        )

        out_dir = os.path.join(OUTPUT_DIR, f"dataset_{doc.header.doc_number}")
        files = await generate_document_files(doc, out_dir)
        presets = arguments.get("presets", ["full_picture", "folded_skewed", "blurry"])
        photos = await generate_dataset(
            files["png"], output_dir=os.path.join(out_dir, "photos"),
            preset_names=presets,
            doc_description=f"doc {doc.header.doc_number}",
        )

        return [TextContent(type="text", text=json.dumps({
            "document": files,
            "photos": photos,
        }, indent=2, default=str))]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
