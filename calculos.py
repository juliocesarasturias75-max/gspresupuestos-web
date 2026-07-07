"""Cálculos de márgenes y totales."""


def aplicar_margenes(items: list[dict], margen_global: float, colocacion_global: float) -> list[dict]:
    """Aplica márgenes globales o individuales y guarda valores aplicados."""
    result = []
    for item in items:
        new_item = dict(item)
        margen = new_item.get("margen_individual")
        if margen is None:
            margen = margen_global
        colocacion = new_item.get("colocacion_individual")
        if colocacion is None:
            colocacion = colocacion_global
        new_item["margen_aplicado"] = margen
        new_item["colocacion_aplicada"] = colocacion
        result.append(new_item)
    return result


def calcular_fila(item: dict) -> dict:
    margen = item.get("margen_aplicado")
    if margen is None:
        margen = item.get("margen_individual") or 0
    colocacion = item.get("colocacion_aplicada")
    if colocacion is None:
        colocacion = item.get("colocacion_individual") or 0
    pvp_u = (item["coste_u"] + colocacion) * (1 + margen / 100)
    subtotal = pvp_u * item["uds"]
    return {
        "pos": item["pos"],
        "uds": item["uds"],
        "desc": item.get("desc", ""),
        "coste_u": item["coste_u"],
        "colocacion": colocacion,
        "margen": margen,
        "pvp_u": round(pvp_u, 2),
        "subtotal": round(subtotal, 2),
    }


def calcular_totales(items: list[dict]) -> dict:
    filas = [calcular_fila(item) for item in items]
    total_base = sum(f["subtotal"] for f in filas)
    coste_total = sum(item["coste_u"] * item["uds"] for item in items)
    iva = total_base * 0.21
    total_final = total_base + iva
    margenes = [f["margen"] for f in filas]
    margen_medio = sum(margenes) / len(margenes) if margenes else 0
    return {
        "filas": filas,
        "total_base": round(total_base, 2),
        "iva": round(iva, 2),
        "total_final": round(total_final, 2),
        "coste_total": round(coste_total, 2),
        "beneficio": round(total_base - coste_total, 2),
        "margen_medio": round(margen_medio, 1),
    }
