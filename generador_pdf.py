"""Generación de PDF de presupuesto."""

import base64
import datetime
import os
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Frame,
    Image as RLImage,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _ruta_datos(nombre: str) -> str:
    return os.path.join(BASE_DIR, "DATOS_DISTRIBUIDOR", nombre)


def _leer_pie() -> str:
    for nombre in ("DATOS_PIE", "DATOS_PIE.txt"):
        ruta = _ruta_datos(nombre)
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except OSError:
                pass
    return ""


def _formato_precio(valor: float) -> str:
    texto = f"{valor:.2f}"
    if "." in texto:
        parte_entera, parte_decimal = texto.split(".")
    else:
        parte_entera, parte_decimal = texto, "00"
    if len(parte_entera) > 3:
        parte_entera = f"{int(parte_entera):,}".replace(",", ".")
    return f"{parte_entera},{parte_decimal} €"


def _pie_de_datos(datos: dict) -> str:
    return datos.get("_pie_texto") or _leer_pie()


def _primera_pagina(canvas, doc, datos: dict):
    page_num = canvas.getPageNumber()
    canvas.saveState()
    pie_texto = _pie_de_datos(datos)
    if pie_texto:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColorRGB(0.3, 0.3, 0.3)
        y_position = 12 * mm
        for linea in reversed(pie_texto.split("\n")):
            if linea.strip():
                canvas.drawCentredString(105 * mm, y_position, linea.strip())
                y_position += 3 * mm
    canvas.setFont("Helvetica", 9)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.drawRightString(200 * mm - 15 * mm, 15 * mm, f"Pág. {page_num}")
    canvas.restoreState()


def _otras_paginas(canvas, doc, datos: dict):
    page_num = canvas.getPageNumber()
    canvas.saveState()

    num_oferta = datos.get("num_oferta") or "[NUM. OFERTA]"
    cliente = datos.get("cliente") or "[CLIENTE]"
    fecha = datetime.datetime.now().strftime("%d.%m.%Y")

    canvas.setFillColorRGB(0.941, 0.976, 1.0)
    canvas.setStrokeColorRGB(0.118, 0.251, 0.686)
    canvas.setLineWidth(1)
    canvas.rect(15 * mm, 297 * mm - 20 * mm, 180 * mm, 8 * mm, fill=1, stroke=1)
    canvas.setFillColorRGB(0, 0, 0)
    canvas.setFont("Helvetica", 9)
    y_pos = 297 * mm - 16 * mm
    canvas.drawString(20 * mm, y_pos, f"PRESUPUESTO {num_oferta}")
    canvas.drawCentredString(105 * mm, y_pos, f"Cliente: {cliente}")
    canvas.drawRightString(190 * mm, y_pos, fecha)

    pie_texto = _pie_de_datos(datos)
    if pie_texto:
        canvas.setFont("Helvetica", 8)
        canvas.setFillColorRGB(0.3, 0.3, 0.3)
        y_position = 12 * mm
        for linea in reversed(pie_texto.split("\n")):
            if linea.strip():
                canvas.drawCentredString(105 * mm, y_position, linea.strip())
                y_position += 3 * mm

    canvas.setFont("Helvetica", 9)
    canvas.setFillColorRGB(0.5, 0.5, 0.5)
    canvas.drawRightString(200 * mm - 15 * mm, 15 * mm, f"Pág. {page_num}")
    canvas.restoreState()


def _cargar_logo(perfil: dict | None) -> tuple[bool, object | None]:
    perfil = perfil or {}
    logo_bytes = perfil.get("logo_bytes")
    if logo_bytes:
        try:
            return True, RLImage(BytesIO(logo_bytes), width=180 * mm, height=25 * mm, kind="proportional")
        except Exception:
            pass
    logo_path = perfil.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        try:
            return True, RLImage(logo_path, width=180 * mm, height=25 * mm, kind="proportional")
        except Exception:
            pass
    for nombre in ("LOGO_EMPRESA", "LOGO_EMPRESA.jpg", "LOGO_EMPRESA.png", "logo_empresa.jpg"):
        ruta = _ruta_datos(nombre)
        if os.path.exists(ruta):
            try:
                return True, RLImage(ruta, width=180 * mm, height=25 * mm, kind="proportional")
            except Exception:
                continue
    return False, None


def generar_pdf_bytes(
    items: list[dict],
    datos_cliente: dict,
    condiciones_texto: str = "",
    perfil: dict | None = None,
) -> bytes:
    """Genera PDF y devuelve bytes."""
    perfil = perfil or {}
    datos_pagina = {
        **datos_cliente,
        "_pie_texto": perfil.get("pie_texto") or _leer_pie(),
    }
    nombre_empresa = perfil.get("nombre_empresa") or "VIGO Y PRADO S.L."
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=A4)
    frame_primera = Frame(15 * mm, 25 * mm, 180 * mm, 297 * mm - 25 * mm - 15 * mm, id="primera")
    frame_otras = Frame(15 * mm, 25 * mm, 180 * mm, 297 * mm - 25 * mm - 35 * mm, id="otras")

    template_primera = PageTemplate(
        id="Primera", frames=[frame_primera],
        onPage=lambda c, d: _primera_pagina(c, d, datos_pagina),
    )
    template_otras = PageTemplate(
        id="Otras", frames=[frame_otras],
        onPage=lambda c, d: _otras_paginas(c, d, datos_pagina),
    )
    doc.addPageTemplates([template_primera, template_otras])

    story = []
    styles = getSampleStyleSheet()

    style_desc = ParagraphStyle("Desc", parent=styles["Normal"], fontSize=7.5, leading=9.5)
    style_val = ParagraphStyle("Val", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=9)
    style_header = ParagraphStyle(
        "H", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9, fontName="Helvetica-Bold"
    )
    style_info = ParagraphStyle("Info", parent=styles["Normal"], fontSize=9, leading=11)
    style_info_bold = ParagraphStyle(
        "InfoBold", parent=styles["Normal"], fontSize=9, fontName="Helvetica-Bold", leading=11
    )

    logo_cargado, logo_img = _cargar_logo(perfil)
    if logo_cargado and logo_img:
        logo_table = Table([[logo_img]], colWidths=[180 * mm])
        logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ]))
        story.append(logo_table)
        story.append(Spacer(1, 3))
    else:
        story.append(Paragraph(f"<b><font size=14>{nombre_empresa}</font></b>", style_header))
        story.append(Spacer(1, 8))

    num_oferta = datos_cliente.get("num_oferta") or "[NUM. OFERTA]"
    fecha = datetime.datetime.now().strftime("%d.%m.%Y")
    referencia = datos_cliente.get("referencia") or ""

    presupuesto_info = f"<b>PRESUPUESTO {num_oferta}</b><br/>Fecha: {fecha}<br/>"
    if referencia:
        presupuesto_info += f"<br/>Referencia: {referencia}"

    cliente_final = datos_cliente.get("cliente") or "[CLIENTE]"
    dir_cliente = datos_cliente.get("direccion") or ""
    tlf_cliente = datos_cliente.get("telefono") or ""
    email_cliente = datos_cliente.get("email") or ""

    cliente_info = f"<b>{cliente_final}</b><br/>"
    if dir_cliente:
        cliente_info += f"{dir_cliente}<br/>"
    if tlf_cliente:
        cliente_info += f"Tel: {tlf_cliente}<br/>"
    if email_cliente:
        cliente_info += email_cliente

    info_table = Table(
        [[Paragraph(presupuesto_info, style_info_bold), Paragraph(cliente_info, style_info)]],
        colWidths=[92 * mm, 93 * mm],
    )
    info_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#1e40af")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    data = [[
        Paragraph("DIBUJO", style_header),
        Paragraph("DESCRIPCIÓN", style_header),
        Paragraph("UDS", style_header),
        Paragraph("PRECIO UNIT.", style_header),
        Paragraph("TOTAL", style_header),
    ]]

    total_base = 0.0
    for item in items:
        margen = item.get("margen_aplicado")
        if margen is None:
            margen = item.get("margen_individual") or 0
        colocacion = item.get("colocacion_aplicada")
        if colocacion is None:
            colocacion = item.get("colocacion_individual") or 0

        pvp_u = (item["coste_u"] + colocacion) * (1 + margen / 100)
        subtotal = pvp_u * item["uds"]
        total_base += subtotal

        img = "S/D"
        if item.get("dibujo_base64"):
            try:
                img_bytes = base64.b64decode(item["dibujo_base64"])
                img = RLImage(BytesIO(img_bytes), width=38 * mm, height=28 * mm)
            except Exception:
                img = "S/D"

        desc_completa = f"<b>{item['pos']}</b><br/>{item['desc']}"
        if item.get("notas"):
            desc_completa += f"<br/><br/><b>NOTA:</b> {item['notas']}"
        if item.get("nota_individual"):
            desc_completa += f"<br/><br/>{item['nota_individual']}"

        data.append([
            img,
            Paragraph(desc_completa, style_desc),
            Paragraph(str(item["uds"]), style_val),
            Paragraph(_formato_precio(pvp_u), style_val),
            Paragraph(_formato_precio(subtotal), style_val),
        ])

    t = Table(data, colWidths=[40 * mm, 95 * mm, 12 * mm, 24 * mm, 24 * mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.2, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))

    iva = total_base * 0.21
    total_final = total_base + iva
    style_resumen = ParagraphStyle("Resumen", parent=styles["Normal"], fontSize=10)
    style_total = ParagraphStyle(
        "Total", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold"
    )

    resumen_tab = Table([
        [Paragraph("BASE IMPONIBLE:", style_resumen), Paragraph(_formato_precio(total_base), style_resumen)],
        [Paragraph("I.V.A. (21%):", style_resumen), Paragraph(_formato_precio(iva), style_resumen)],
        [Paragraph("TOTAL PRESUPUESTO:", style_total), Paragraph(_formato_precio(total_final), style_total)],
    ], colWidths=[155 * mm, 30 * mm])
    resumen_tab.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LEFTPADDING", (1, 0), (1, -1), 15),
        ("LINEABOVE", (1, 2), (1, 2), 1.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, 1), 3),
        ("BOTTOMPADDING", (0, 2), (1, 2), 5),
    ]))
    story.append(resumen_tab)

    if condiciones_texto:
        story.append(Spacer(1, 20))
        line_style = ParagraphStyle("line", alignment=TA_CENTER, fontSize=7)
        story.append(Paragraph("━" * 80, line_style))
        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>CONDICIONES GENERALES:</b>", styles["Heading3"]))
        story.append(Spacer(1, 8))
        for parrafo in condiciones_texto.split("\n"):
            if parrafo.strip():
                story.append(Paragraph(parrafo, styles["Normal"]))
                story.append(Spacer(1, 3))
        story.append(Spacer(1, 15))
        story.append(Paragraph("━" * 80, line_style))
        story.append(Spacer(1, 20))

    firma_style = ParagraphStyle("Firma", parent=styles["Normal"], fontSize=11, leading=18)
    story.append(Paragraph("<b>Aceptación del presupuesto:</b>", firma_style))
    story.append(Spacer(1, 25))
    story.append(Paragraph("Firmado: ...........................................", firma_style))

    doc.build(
        story,
        onFirstPage=lambda c, d: _primera_pagina(c, d, datos_pagina),
        onLaterPages=lambda c, d: _otras_paginas(c, d, datos_pagina),
    )
    buffer.seek(0)
    return buffer.read()


def _formato_precio_resumen(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def generar_resumen_pdf_bytes(items: list[dict], datos_cliente: dict, perfil: dict | None = None) -> bytes:
    """Genera PDF de resumen interno de cálculos (sin dibujos)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
    )
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "TituloResumen", parent=styles["Heading1"],
        fontSize=16, textColor=colors.HexColor("#1e40af"),
        alignment=TA_CENTER, spaceAfter=10,
    )
    story.append(Paragraph("RESUMEN DE CÁLCULOS INTERNOS", titulo_style))

    num_oferta = datos_cliente.get("num_oferta") or "[NUM. OFERTA]"
    cliente = datos_cliente.get("cliente") or "[CLIENTE]"
    fecha = datetime.datetime.now().strftime("%d.%m.%Y")

    info_style = ParagraphStyle(
        "InfoResumen", parent=styles["Normal"],
        fontSize=10, alignment=TA_CENTER, spaceAfter=15,
    )
    info_texto = f"<b>Oferta:</b> {num_oferta} | <b>Cliente:</b> {cliente} | <b>Fecha:</b> {fecha}"
    story.append(Paragraph(info_texto, info_style))
    story.append(Spacer(1, 10))

    tabla_data = [[
        Paragraph("<b>Pos.</b>", styles["Normal"]),
        Paragraph("<b>Descripción</b>", styles["Normal"]),
        Paragraph("<b>Uds</b>", styles["Normal"]),
        Paragraph("<b>Coste Base</b>", styles["Normal"]),
        Paragraph("<b>Coloc</b>", styles["Normal"]),
        Paragraph("<b>% Bº.</b>", styles["Normal"]),
        Paragraph("<b>PVP Unit.</b>", styles["Normal"]),
        Paragraph("<b>Total</b>", styles["Normal"]),
    ]]

    total_base = 0.0
    for item in items:
        coste_base = item.get("coste_u", 0.0)
        uds = item.get("uds", 1)
        margen = item.get("margen_aplicado")
        if margen is None:
            margen = item.get("margen_individual") or 0
        colocacion = item.get("colocacion_aplicada")
        if colocacion is None:
            colocacion = item.get("colocacion_individual") or 0
        pvp_u = (coste_base + colocacion) * (1 + margen / 100)
        subtotal = pvp_u * uds
        total_base += subtotal

        desc_limpia = item.get("desc", "").replace("<br/>", " ").replace("<b>", "").replace("</b>", "")
        if len(desc_limpia) > 50:
            desc_limpia = desc_limpia[:47] + "..."

        tabla_data.append([
            item["pos"],
            Paragraph(desc_limpia, styles["Normal"]),
            str(uds),
            _formato_precio_resumen(coste_base),
            _formato_precio_resumen(colocacion),
            f"{margen:.1f}%",
            _formato_precio_resumen(pvp_u),
            _formato_precio_resumen(subtotal),
        ])

    tabla = Table(tabla_data, colWidths=[15 * mm, 60 * mm, 12 * mm, 22 * mm, 15 * mm, 20 * mm, 22 * mm, 24 * mm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (1, -1), "LEFT"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.black),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 15))

    iva = total_base * 0.21
    total_final = total_base + iva
    totales_style = ParagraphStyle("Totales", parent=styles["Normal"], fontSize=10, alignment=TA_RIGHT, spaceAfter=3)
    total_final_style = ParagraphStyle(
        "TotalFinal", parent=styles["Normal"], fontSize=12,
        fontName="Helvetica-Bold", alignment=TA_RIGHT, spaceAfter=5,
    )
    story.append(Paragraph(f"TOTAL BASE: {_formato_precio_resumen(total_base)}", totales_style))
    story.append(Paragraph(f"IVA (21%): {_formato_precio_resumen(iva)}", totales_style))
    story.append(Paragraph("_" * 60, totales_style))
    story.append(Paragraph(f"TOTAL FINAL: {_formato_precio_resumen(total_final)}", total_final_style))

    story.append(Spacer(1, 20))
    pie_style = ParagraphStyle("Pie", parent=styles["Normal"], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    story.append(Paragraph(
        "Este documento es un resumen interno de cálculos. No es válido como presupuesto oficial.",
        pie_style,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
