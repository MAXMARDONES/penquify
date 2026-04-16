"""Penquify REST API — FastAPI server."""
import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ..models.document import Document, DocHeader, DocItem
from ..models.variation import PhotoVariation, Stain, PRESETS
from ..generators.pdf import generate_document_files, render_html
from ..generators.photo import generate_dataset, generate_photo

app = FastAPI(
    title="Penquify",
    description="Synthetic logistics document & photo dataset generator",
    version="0.1.0",
)

OUTPUT_DIR = os.environ.get("PENQUIFY_OUTPUT", "output")


# ── Request models ──────────────────────────────────────────

class ItemRequest(BaseModel):
    code: str = ""
    description: str
    qty: float
    unit: str
    unit_price: float = 0
    total: float = 0
    batch: str = ""
    sap_material: str = ""
    sap_qty: float = 0
    sap_unit: str = ""

class HeaderRequest(BaseModel):
    doc_type: str = "guia_despacho"
    doc_number: str = ""
    date: str = ""
    emitter_name: str = ""
    emitter_rut: str = ""
    emitter_giro: str = ""
    emitter_address: str = ""
    emitter_phone: str = ""
    emitter_email: str = ""
    receiver_name: str = ""
    receiver_rut: str = ""
    receiver_giro: str = ""
    receiver_address: str = ""
    receiver_contact: str = ""
    oc_number: str = ""
    oc_date: str = ""
    payment_terms: str = ""
    dispatch_date: str = ""
    vehicle_plate: str = ""
    driver_name: str = ""
    driver_rut: str = ""
    sii_office: str = ""
    sii_resolution: str = ""
    received_by: str = ""
    received_rut: str = ""
    received_date: str = ""

class GenerateDocRequest(BaseModel):
    header: HeaderRequest
    items: List[ItemRequest]
    observations: str = ""
    template: str = "guia_despacho.html"

class GeneratePhotosRequest(BaseModel):
    image_path: str = ""
    presets: Optional[List[str]] = None
    variations: Optional[List[dict]] = None
    doc_description: str = ""

class GenerateDatasetRequest(BaseModel):
    header: HeaderRequest
    items: List[ItemRequest]
    observations: str = ""
    template: str = "guia_despacho.html"
    presets: Optional[List[str]] = None
    doc_description: str = ""

class ConfigFromTextRequest(BaseModel):
    description: str = Field(..., description="Natural language description of the photo variation")


# ── Helpers ──────────────────────────────────────────

def _build_doc(req) -> Document:
    return Document(
        header=DocHeader(**req.header.model_dump()),
        items=[DocItem(pos=i+1, **it.model_dump()) for i, it in enumerate(req.items)],
        observations=req.observations,
    )

def _run_id() -> str:
    return uuid.uuid4().hex[:10]


# ── Routes ──────────────────────────────────────────

@app.get("/")
def root():
    return {"name": "penquify", "version": "0.1.0", "docs": "/docs"}


@app.get("/presets")
def list_presets():
    """List available photo variation presets."""
    return {name: v.to_prompt_json() for name, v in PRESETS.items()}


@app.get("/templates")
def list_templates():
    """List available document templates."""
    tmpl_dir = Path(__file__).parent.parent / "templates"
    return [f.name for f in tmpl_dir.glob("*.html")]


@app.post("/generate/document")
async def generate_document(req: GenerateDocRequest):
    """Generate PDF + PNG from document JSON."""
    doc = _build_doc(req)
    run_id = _run_id()
    out_dir = os.path.join(OUTPUT_DIR, run_id)
    files = await generate_document_files(doc, out_dir, req.template)
    return {"run_id": run_id, "files": files}


@app.post("/generate/photos")
async def gen_photos(req: GeneratePhotosRequest):
    """Generate photos from an existing image."""
    if not req.image_path or not os.path.exists(req.image_path):
        raise HTTPException(400, "image_path required and must exist")

    run_id = _run_id()
    out_dir = os.path.join(OUTPUT_DIR, run_id, "photos")

    variations = None
    if req.variations:
        variations = [PhotoVariation(**v) for v in req.variations]

    results = await generate_dataset(
        req.image_path, variations=variations,
        output_dir=out_dir, preset_names=req.presets,
        doc_description=req.doc_description,
    )
    return {"run_id": run_id, "results": results}


@app.post("/generate/dataset")
async def gen_dataset(req: GenerateDatasetRequest):
    """Full pipeline: document JSON → PDF → photos."""
    doc = _build_doc(req)
    run_id = _run_id()
    out_dir = os.path.join(OUTPUT_DIR, run_id)

    # Step 1: Generate document files
    files = await generate_document_files(doc, out_dir, req.template)

    # Step 2: Generate photos
    results = await generate_dataset(
        files["png"],
        output_dir=os.path.join(out_dir, "photos"),
        preset_names=req.presets,
        doc_description=req.doc_description or f"doc {doc.header.doc_number}",
    )

    return {
        "run_id": run_id,
        "document": files,
        "photos": results,
    }


@app.post("/generate/config")
async def gen_config(req: ConfigFromTextRequest):
    """Convert natural language description to a PhotoVariation JSON config.
    Example: 'blurry photo with coffee stain, taken from above with strong angle'
    """
    from ..generators.config import text_to_variation
    variation = await text_to_variation(req.description)
    return variation


@app.post("/generate/from-upload")
async def gen_from_upload(file: UploadFile = File(...), presets: str = "full_picture,folded_skewed,blurry"):
    """Upload a PDF/image → detect schema → generate verified photos."""
    from ..generators.upload import upload_and_generate

    run_id = _run_id()
    out_dir = os.path.join(OUTPUT_DIR, run_id)
    os.makedirs(out_dir, exist_ok=True)

    # Save uploaded file
    ext = os.path.splitext(file.filename or "doc.pdf")[1]
    upload_path = os.path.join(out_dir, f"upload{ext}")
    with open(upload_path, "wb") as f:
        content = await file.read()
        f.write(content)

    preset_list = [p.strip() for p in presets.split(",") if p.strip()]

    result = await upload_and_generate(
        upload_path, output_dir=out_dir,
        preset_names=preset_list, max_retries=2,
    )

    return {"run_id": run_id, **result}


@app.get("/documents")
def list_documents():
    """List all generated document runs."""
    out = Path(OUTPUT_DIR)
    if not out.exists():
        return []
    runs = []
    for d in sorted(out.iterdir(), reverse=True):
        if d.is_dir():
            files = [f.name for f in d.rglob("*") if f.is_file()]
            runs.append({"run_id": d.name, "files": files})
    return runs[:50]


@app.get("/documents/{run_id}/{filename}")
def get_document_file(run_id: str, filename: str):
    """Download a specific file from a run."""
    # Search recursively
    out = Path(OUTPUT_DIR) / run_id
    matches = list(out.rglob(filename))
    if not matches:
        raise HTTPException(404, f"File {filename} not found in run {run_id}")
    return FileResponse(matches[0])
