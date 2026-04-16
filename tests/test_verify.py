"""Test ground truth verification — programmatic comparison (no model needed)."""
from penquify.generators.verify import compare_against_ground_truth, _normalize, _schema_from_document, build_occlusion_manifest
from penquify.models import Document, DocHeader, DocItem, PhotoVariation, Stain


def test_normalize():
    assert _normalize("$180,000") == "180000"
    assert _normalize("  Hello World  ") == "hello world"
    assert _normalize("4500000316") == "4500000316"
    assert _normalize(None) == ""


def test_compare_all_match():
    schema = {"oc_number": "4500000316", "item_1_qty": "12"}
    extractions = {"extractions": {
        "oc_number": {"value": "4500000316", "confidence": 0.95, "reason": None},
        "item_1_qty": {"value": "12", "confidence": 0.9, "reason": None},
    }}
    result = compare_against_ground_truth(extractions, schema)
    assert result["summary"]["matched"] == 2
    assert result["summary"]["mismatched"] == 0


def test_compare_mismatch():
    schema = {"oc_number": "4500000316"}
    extractions = {"extractions": {
        "oc_number": {"value": "4500000317", "confidence": 0.9, "reason": None},
    }}
    result = compare_against_ground_truth(extractions, schema)
    assert result["summary"]["mismatched"] == 1
    assert result["fields"]["oc_number"]["status"] == "mismatch"


def test_compare_not_visible():
    schema = {"header_date": "16/04/2026"}
    extractions = {"extractions": {
        "header_date": {"value": None, "confidence": 0, "reason": "cropped"},
    }}
    result = compare_against_ground_truth(extractions, schema)
    assert result["summary"]["not_visible"] == 1
    assert result["fields"]["header_date"]["status"] == "not_visible"


def test_compare_illegible():
    schema = {"item_2_qty": "115"}
    extractions = {"extractions": {
        "item_2_qty": {"value": None, "confidence": 0, "reason": "blurry"},
    }}
    result = compare_against_ground_truth(extractions, schema)
    assert result["summary"]["illegible"] == 1


def test_compare_low_confidence_is_illegible():
    schema = {"total": "1077164"}
    extractions = {"extractions": {
        "total": {"value": "1077164", "confidence": 0.3, "reason": None},
    }}
    result = compare_against_ground_truth(extractions, schema)
    # Low confidence but correct value — still illegible because we can't trust it
    assert result["fields"]["total"]["status"] == "illegible"


def test_schema_from_document():
    doc = Document(
        header=DocHeader(doc_type="guia", doc_number="001", date="01/01/2026",
                         emitter_name="ACME", oc_number="4500000316"),
        items=[DocItem(pos=1, code="X", description="Test Item", qty=10, unit="KG",
                       unit_price=1000, total=10000)],
    )
    schema = _schema_from_document(doc)
    assert schema["doc_number"] == "001"
    assert schema["oc_number"] == "4500000316"
    assert schema["item_1_description"] == "Test Item"
    assert schema["item_1_qty"] == "10"
    assert schema["subtotal"] == "10000"


def test_occlusion_manifest_crop():
    verification = {"fields": {
        "doc_number": {"status": "not_visible", "extracted_value": None, "source_value": "001", "confidence": 0},
        "item_1_qty": {"status": "match", "extracted_value": "10", "source_value": "10", "confidence": 0.9},
    }}
    variation = PhotoVariation(cropped_header=True, missing_area="top 15%")
    manifest = build_occlusion_manifest(verification, variation)
    assert manifest["doc_number"]["status"] == "not_visible"
    assert any("crop" in r for r in manifest["doc_number"]["reasons"])
    assert manifest["item_1_qty"] == "visible"


def test_occlusion_manifest_stain():
    verification = {"fields": {
        "item_2_qty": {"status": "illegible", "extracted_value": "11?", "source_value": "115", "confidence": 0.3},
    }}
    variation = PhotoVariation(stain=Stain(type="coffee", location="center", text_obstruction="partial"))
    manifest = build_occlusion_manifest(verification, variation)
    assert "coffee_stain" in str(manifest["item_2_qty"]["reasons"])


def test_occlusion_manifest_blur():
    verification = {"fields": {
        "total": {"status": "illegible", "extracted_value": None, "source_value": "1077164", "confidence": 0},
    }}
    variation = PhotoVariation(motion_blur=True, blur_direction="horizontal")
    manifest = build_occlusion_manifest(verification, variation)
    assert "motion" in str(manifest["total"]["reasons"])
