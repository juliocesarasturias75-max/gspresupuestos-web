"""Parseo de archivos TXT de Aluminios Seco."""

import csv
import re

TEXTO_VERIFICACION = "ALUMINIOS SECO, S.L"
TEXTO_VERIFICACION_CIF = "B27152727"


def estructurar_descripcion(texto: str) -> str:
    """Organizar descripción: Tipo → Color → Medidas → Índices → Resto."""
    if not texto:
        return ""

    traducciones = {
        r"\\\'f1": "ñ", r"\\\'e1": "á", r"\\\'e9": "é",
        r"\\\'ed": "í", r"\\\'f3": "ó", r"\\\'fa": "ú",
        r"\\\'b7": "·", r"\'f3": "ó", r"\'e1": "á",
    }

    for c, l in traducciones.items():
        texto = texto.replace(c, l)

    texto = re.sub(r"\\[a-z0-9-]+", " ", texto)
    texto = texto.replace("{", "").replace("}", "").replace("\\", "")
    texto = texto.replace('"', "")
    texto = re.sub(r"\s+", " ", texto).strip()

    lineas = []

    match_tipo = re.search(r"^(.*?)(?=Color:)", texto, re.IGNORECASE)
    if match_tipo:
        tipo = match_tipo.group(1).strip()
        lineas.append(tipo)
        texto = texto[len(tipo):].strip()

    match_color = re.search(
        r"Color:\s*(.*?)(?=\s*Ancho:|\s*Alto:|\s*U=|$)",
        texto, re.IGNORECASE | re.DOTALL,
    )
    if match_color:
        color_texto = match_color.group(1).strip()
        lineas.append(f"• Color: {color_texto}")
        texto = texto.replace(f"Color: {color_texto}", "", 1).replace("Color:", "", 1).strip()

    ancho = re.search(r"Ancho:\s*([0-9.,\s-]+?)(?=\s*Alto:|\s*U=|$)", texto, re.IGNORECASE)
    alto = re.search(r"Alto:\s*([0-9.,\s]+?)(?=\s*U=|$)", texto, re.IGNORECASE)

    medidas_partes = []
    if ancho:
        medidas_partes.append(f"Ancho: {ancho.group(1).strip()}")
        texto = texto.replace(ancho.group(0), "", 1)
    if alto:
        medidas_partes.append(f"Alto: {alto.group(1).strip()}")
        texto = texto.replace(alto.group(0), "", 1)

    if medidas_partes:
        lineas.append(f"• {' - '.join(medidas_partes)}")

    match_indices = re.search(
        r"U=\s*[0-9.,]+\s*W/[KÁ]+[·•]?m2?\s*-?\s*Ac[úÁa°]+stica[=:]\s*(?:[0-9]+\s*\([^)]+\)|PND)\s*dB",
        texto, re.IGNORECASE,
    )
    if match_indices:
        lineas.append(f"• {match_indices.group(0).strip()}")
        texto = texto.replace(match_indices.group(0), "", 1).strip()

    texto = re.sub(r"\s+", " ", texto).strip()
    if texto:
        lineas.append(f"• {texto}")

    return "<br/>".join(lineas)


def _leer_contenido(path_or_bytes, filename: str = "") -> str:
    if isinstance(path_or_bytes, bytes):
        contenido = None
        for enc in ["utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-8-sig"]:
            try:
                contenido = path_or_bytes.decode(enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if contenido is None:
            contenido = path_or_bytes.decode("latin-1", errors="replace")
        return contenido

    contenido = None
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-8-sig"]
    for enc in encodings:
        try:
            with open(path_or_bytes, "r", encoding=enc) as f:
                contenido = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if contenido is None:
        with open(path_or_bytes, "r", encoding="latin-1", errors="replace") as f:
            contenido = f.read()
    return contenido


def parse_txt(contenido: str) -> list[dict]:
    """Parsea contenido TXT y devuelve lista de partidas."""
    if TEXTO_VERIFICACION not in contenido or TEXTO_VERIFICACION_CIF not in contenido:
        raise ValueError(
            "Archivo TXT no válido. Solo se aceptan presupuestos de ALUMINIOS SECO, S.L."
        )

    items = []
    bloques = re.split(r"Pos\.", contenido)

    for bloque in bloques[1:]:
        lineas = bloque.split("\n")
        pos_numero = lineas[0].split(",")[0].strip().replace('"', "").replace("'", "")

        item = {
            "pos": "Pos." + pos_numero,
            "desc": "",
            "coste_u": 0.0,
            "uds": 1,
            "margen_individual": None,
            "colocacion_individual": None,
            "notas": "",
            "dibujo_base64": None,
        }

        for linea in lineas:
            linea_limpia = linea.strip()

            if "Ancho:" in linea or "Color:" in linea or "Tapajuntas" in linea or "celular" in linea:
                item["desc"] = estructurar_descripcion(linea)

            if "UDS:" in linea:
                u_match = re.search(r"UDS:\s*(\d+)", linea)
                if u_match:
                    item["uds"] = int(u_match.group(1))
                precios = re.findall(r"[\d\.]+,[\d]+", linea)
                if precios:
                    total_str = precios[-1].replace(".", "").replace(",", ".")
                    total_float = float(total_str)
                    item["coste_u"] = total_float / item["uds"]

            if linea_limpia.startswith('"') and linea_limpia.count('"') >= 6:
                try:
                    campos = list(csv.reader([linea_limpia]))[0]
                    if len(campos) >= 4 and campos[0] and "Importe" not in campos[1]:
                        if "Tapajuntas" in campos[1] or "celular" in campos[1]:
                            item["desc"] = campos[1].strip()
                        try:
                            uds_str = campos[2].replace(",", ".")
                            item["uds"] = int(float(uds_str))
                        except (ValueError, IndexError):
                            pass
                        try:
                            precio_str = campos[3].replace(",", ".")
                            item["coste_u"] = float(precio_str)
                        except (ValueError, IndexError):
                            pass
                except Exception:
                    pass

        if item["coste_u"] > 0:
            items.append(item)

    return items


def parse_txt_bytes(data: bytes) -> list[dict]:
    contenido = _leer_contenido(data)
    return parse_txt(contenido)
