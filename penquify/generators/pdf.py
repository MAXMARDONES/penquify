"""PDF/PNG generator — renders Jinja2 HTML templates via Playwright."""
import asyncio
import os
import tempfile
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

from ..models.document import Document

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def render_html(doc: Document, template_name: str = "guia_despacho.html") -> str:
    """Render a Document to HTML string using Jinja2 template."""
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    tmpl = env.get_template(template_name)
    return tmpl.render(**doc.to_dict())


async def html_to_png(html_content: str, output_path: str, width: int = 900, height: int = 1270):
    """Screenshot HTML string to PNG using Playwright."""
    from playwright.async_api import async_playwright

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html_content)
        tmp_path = f.name

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(f"file://{tmp_path}")
            el = await page.query_selector(".page")
            if el:
                await el.screenshot(path=output_path)
            else:
                await page.screenshot(path=output_path, full_page=False)
            await browser.close()
    finally:
        os.unlink(tmp_path)

    return output_path


async def html_to_pdf(html_content: str, output_path: str):
    """Render HTML to PDF using Playwright."""
    from playwright.async_api import async_playwright

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        f.write(html_content)
        tmp_path = f.name

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file://{tmp_path}")
            await page.pdf(path=output_path, format="A4", print_background=True)
            await browser.close()
    finally:
        os.unlink(tmp_path)

    return output_path


async def generate_document_files(doc: Document, output_dir: str,
                                   template_name: str = "guia_despacho.html") -> dict:
    """Generate HTML, PNG, and PDF for a document. Returns paths."""
    os.makedirs(output_dir, exist_ok=True)
    slug = f"{doc.header.doc_type}_{doc.header.doc_number}"

    html = render_html(doc, template_name)

    html_path = os.path.join(output_dir, f"{slug}.html")
    with open(html_path, "w") as f:
        f.write(html)

    png_path = os.path.join(output_dir, f"{slug}.png")
    await html_to_png(html, png_path)

    pdf_path = os.path.join(output_dir, f"{slug}.pdf")
    await html_to_pdf(html, pdf_path)

    return {"html": html_path, "png": png_path, "pdf": pdf_path}
