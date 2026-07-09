"""Unir varios PDF en uno."""

from io import BytesIO

from pypdf import PdfReader, PdfWriter


def merge_pdfs(partes: list[bytes]) -> bytes:
    writer = PdfWriter()
    for data in partes:
        if not data:
            continue
        reader = PdfReader(BytesIO(data))
        for page in reader.pages:
            writer.add_page(page)
    out = BytesIO()
    writer.write(out)
    return out.getvalue()
