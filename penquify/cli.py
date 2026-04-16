#!/usr/bin/env python3
"""Penquify CLI — generate logistics documents and realistic photos."""
import asyncio
import json
import sys
import os
from pathlib import Path

from .models import Document, DocHeader, DocItem, PhotoVariation, PRESETS
from .generators.pdf import generate_document_files, render_html
from .generators.photo import generate_dataset


def demo_guia():
    """Generate a demo guia de despacho with photos."""
    doc = Document(
        header=DocHeader(
            doc_type="guia_despacho",
            doc_number="01182034",
            date="16/04/2026",
            emitter_name="COMERCIAL AGRO SUR LTDA.",
            emitter_rut="77.234.567-1",
            emitter_giro="Comercializacion de productos alimenticios",
            emitter_address="Av. Padre Hurtado 1520, Bodega 3, Rancagua",
            emitter_phone="(072) 245 8900",
            emitter_email="despacho@agrosur.cl",
            receiver_name="ACME LOGISTICS S.A.",
            receiver_rut="96.754.321-8",
            receiver_giro="Hoteleria y entretenimiento",
            receiver_address="Av. Industrial 2500, Santiago",
            receiver_contact="Bodega Central — Danilo Gatica",
            oc_number="4500000316",
            oc_date="29/12/2025",
            payment_terms="Condicion de pago: 30 dias",
            dispatch_date="16/04/2026",
            vehicle_plate="WFKP-91",
            driver_name="Rodrigo Fuentes M.",
            driver_rut="15.234.891-K",
            sii_office="S.I.I. — RANCAGUA",
            sii_resolution="Res. Ex. N 215 del 22/06/2025",
            received_by="Danilo Gatica",
            received_rut="18.234.567-K",
            received_date="16/04/2026",
        ),
        items=[
            DocItem(pos=1, code="AS-4010", description="PAPA PREFRITA CONGELADA CORTE GRUESO",
                    qty=12, unit="CJ", unit_price=15000, total=180000,
                    sap_material="2100000000", sap_qty=150, sap_unit="KG"),
            DocItem(pos=2, code="AS-2050", description="MOZZARELLA RALLADA PREMIUM (bolsa 5kg)",
                    qty=115, unit="KG", unit_price=4900, total=563500,
                    sap_material="2100000653", sap_qty=120, sap_unit="KG"),
            DocItem(pos=3, code="AS-7015", description="FRUTILLA FRESCA SELECCION (bandeja 1kg)",
                    qty=2, unit="KG", unit_price=5990, total=11980,
                    sap_material="2100008379", sap_qty=2, sap_unit="KG"),
            DocItem(pos=4, code="AS-7042", description="JENGIBRE FRESCO PELADO",
                    qty=2, unit="UN", unit_price=1500, total=3000,
                    sap_material="2100000748", sap_qty=0.5, sap_unit="KG"),
            DocItem(pos=5, code="AS-7028", description="LIMON DE PICA FRESCO GRANEL",
                    qty=20, unit="KG", unit_price=2800, total=56000,
                    sap_material="2100000771", sap_qty=20, sap_unit="KG"),
            DocItem(pos=6, code="AS-7029", description="LIMON SUTIL FRESCO (malla 5kg)",
                    qty=24, unit="KG", unit_price=3200, total=76800,
                    sap_material="2100000772", sap_qty=25, sap_unit="L"),
            DocItem(pos=7, code="AS-7055", description="MENTA FRESCA ATADO",
                    qty=10, unit="UN", unit_price=1390, total=13900,
                    sap_material="2100000789", sap_qty=2, sap_unit="KG"),
        ],
        observations="Papa prefrita: 12 cajas. Peso por caja no indicado.\nMozzarella: 115kg despachados — faltaron 5kg.\nJengibre: 2 unidades. Peso por bolsa no indicado.\nLimon sutil: 24kg (OC indicaba 25).\nMenta: 10 atados. Peso por atado no indicado.",
    )
    return doc


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Penquify — logistics document + photo generator")
    parser.add_argument("command", choices=["demo", "pdf", "photos", "dataset", "upload"],
                        help="demo=full pipeline, pdf=PDF only, photos=from PNG, dataset=full, upload=PDF→schema→photos")
    parser.add_argument("--output", "-o", default="output", help="Output directory")
    parser.add_argument("--presets", nargs="*", help="Photo preset names (default: all)")
    parser.add_argument("--image", help="Reference image path (for photos command)")
    parser.add_argument("--doc-json", help="Document JSON file (for pdf command)")
    args = parser.parse_args()

    if args.command == "demo":
        doc = demo_guia()
        print(f"Generating demo guia de despacho...")
        files = await generate_document_files(doc, args.output)
        print(f"  HTML: {files['html']}")
        print(f"  PNG:  {files['png']}")
        print(f"  PDF:  {files['pdf']}")

        print(f"\nGenerating photo dataset...")
        results = await generate_dataset(
            files["png"], output_dir=os.path.join(args.output, "photos"),
            preset_names=args.presets,
            doc_description=f"OC {doc.header.oc_number}, guia {doc.header.doc_number}, 7 items",
        )
        ok = sum(1 for r in results if r["ok"])
        print(f"\nDone: {ok}/{len(results)} photos generated in {args.output}/photos/")

    elif args.command == "pdf":
        if args.doc_json:
            with open(args.doc_json) as f:
                data = json.load(f)
            doc = Document(
                header=DocHeader(**data["header"]),
                items=[DocItem(**it) for it in data["items"]],
                observations=data.get("observations", ""),
            )
        else:
            doc = demo_guia()
        files = await generate_document_files(doc, args.output)
        print(f"Generated: {files}")

    elif args.command == "photos":
        if not args.image:
            print("ERROR: --image required for photos command")
            sys.exit(1)
        results = await generate_dataset(
            args.image, output_dir=os.path.join(args.output, "photos"),
            preset_names=args.presets,
        )
        ok = sum(1 for r in results if r["ok"])
        print(f"Done: {ok}/{len(results)} photos")

    elif args.command == "upload":
        from .generators.upload import upload_and_generate
        if not args.image:
            print("ERROR: --image required (path to PDF or image)")
            sys.exit(1)
        print(f"Upload pipeline: {args.image}")
        result = await upload_and_generate(
            args.image, output_dir=args.output,
            preset_names=args.presets,
        )
        schema = result.get("detected_schema", {})
        photos = result.get("photos", [])
        verified = sum(1 for p in photos if p.get("verified"))
        print(f"\nSchema: {schema.get('document_type', '?')}, {len(schema.get('items', []))} items")
        print(f"Photos: {verified}/{len(photos)} verified")
        print(f"Output: {args.output}/")


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
