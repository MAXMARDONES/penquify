"""Test document and variation models."""
from penquify.models import Document, DocHeader, DocItem, PhotoVariation, Stain, PRESETS
from penquify.models.cameras import CAMERAS, get_camera


def test_document_totals():
    doc = Document(
        header=DocHeader(doc_type="guia_despacho", doc_number="001", date="2026-01-01"),
        items=[
            DocItem(pos=1, code="A", description="Item A", qty=10, unit="KG", unit_price=1000, total=10000),
            DocItem(pos=2, code="B", description="Item B", qty=5, unit="UN", unit_price=2000, total=10000),
        ],
    )
    assert doc.subtotal == 20000
    assert doc.iva == 3800
    assert doc.total == 23800


def test_document_to_dict():
    doc = Document(
        header=DocHeader(doc_type="test", doc_number="999", date="2026-01-01"),
        items=[DocItem(pos=1, code="X", description="Test", qty=1, unit="UN", unit_price=100, total=100)],
    )
    d = doc.to_dict()
    assert d["header"]["doc_number"] == "999"
    assert len(d["items"]) == 1
    assert d["subtotal"] == 100


def test_variation_to_prompt_json():
    v = PhotoVariation(name="test", camera="iPhone 12", motion_blur=True)
    j = v.to_prompt_json()
    assert j["meta"]["camera"] == "iPhone 12"
    assert j["meta"]["slight_handheld_motion"] is True


def test_variation_with_stain():
    v = PhotoVariation(
        name="stained",
        stain=Stain(type="coffee", location="upper_right"),
    )
    j = v.to_prompt_json()
    assert "damage" in j
    assert j["damage"]["stain"]["type"] == "coffee"


def test_presets_exist():
    assert len(PRESETS) >= 8
    assert "full_picture" in PRESETS
    assert "blurry" in PRESETS
    assert "coffee_stain" in PRESETS


def test_overexposure_default():
    v = PhotoVariation(name="clean")
    assert v.overexposure == 0.0
    j = v.to_prompt_json()
    assert "failure_modes" not in j or "overexposure" not in j.get("failure_modes", {})


def test_overexposure_in_prompt_json():
    v = PhotoVariation(name="washed", overexposure=0.7)
    j = v.to_prompt_json()
    assert "failure_modes" in j
    assert j["failure_modes"]["overexposure"] == 0.7
    assert "severely washed out" in j["failure_modes"]["overexposure_description"]


def test_overexposure_light():
    v = PhotoVariation(name="light_wash", overexposure=0.2)
    j = v.to_prompt_json()
    assert "light wash" in j["failure_modes"]["overexposure_description"]


def test_overexposure_moderate():
    v = PhotoVariation(name="mod_wash", overexposure=0.5)
    j = v.to_prompt_json()
    assert "moderate bleaching" in j["failure_modes"]["overexposure_description"]


def test_overexposed_preset_exists():
    assert "overexposed" in PRESETS
    assert PRESETS["overexposed"].overexposure == 0.7


def test_cameras_library():
    assert len(CAMERAS) >= 20
    assert "galaxy_s8" in CAMERAS
    assert "warehouse_generic" in CAMERAS


def test_get_camera_preset():
    c = get_camera("galaxy_s8")
    assert c["camera"] == "Samsung Galaxy S8"


def test_get_camera_free_text():
    c = get_camera("Nokia 3310")
    assert c["camera"] == "Nokia 3310"
