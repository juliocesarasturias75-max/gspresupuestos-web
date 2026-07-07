"""Extracción de dibujos desde PDF."""

import base64
from io import BytesIO

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False


def extraer_dibujos(data: bytes) -> list[str]:
    """Extrae imágenes del PDF y devuelve lista en base64."""
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError("PyMuPDF no está instalado.")

    doc = fitz.open(stream=data, filetype="pdf")
    dibujos_extraidos = []

    for page in doc:
        imgs_pagina = []
        for img in page.get_images(full=True):
            xref = img[0]
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            r = rects[0]
            if r.x0 < 280 and 40 < r.width < 500:
                pix = doc.extract_image(xref)
                imgs_pagina.append({"y": r.y0, "data": pix["image"]})
        imgs_pagina.sort(key=lambda x: x["y"])
        dibujos_extraidos.extend([i["data"] for i in imgs_pagina])

    doc.close()
    return [base64.b64encode(img).decode("utf-8") for img in dibujos_extraidos]


def asociar_dibujos_a_partidas(items: list[dict], dibujos_b64: list[str]) -> list[dict]:
    """Asocia cada dibujo con su partida correspondiente."""
    result = []
    for idx, item in enumerate(items):
        new_item = dict(item)
        if idx < len(dibujos_b64):
            new_item["dibujo_base64"] = dibujos_b64[idx]
        else:
            new_item["dibujo_base64"] = None
        result.append(new_item)
    return result
