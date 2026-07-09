"""Comprobaciones de coherencia para presupuestos."""

from calculos import calcular_fila

LIMITES = {
    "uds_max": 200,
    "uds_aviso": 50,
    "margen_min": 0.0,
    "margen_max": 150.0,
    "margen_aviso_alto": 80.0,
    "coste_max": 50000.0,
    "coloc_max": 5000.0,
}


def _fila_calculada(item: dict, margen_global: float, colocacion_global: float) -> dict:
    tmp = dict(item)
    if tmp.get("margen_aplicado") is None and tmp.get("margen_individual") is None:
        tmp["margen_aplicado"] = margen_global
    if tmp.get("colocacion_aplicada") is None and tmp.get("colocacion_individual") is None:
        tmp["colocacion_aplicada"] = colocacion_global
    return calcular_fila(tmp)


def validar_items(
    items: list[dict],
    margen_global: float = 20.0,
    colocacion_global: float = 50.0,
    datos_cliente: dict | None = None,
    requiere_cliente: bool = False,
) -> dict:
    errores: list[dict] = []
    avisos: list[dict] = []

    if not items:
        errores.append({
            "codigo": "sin_partidas",
            "mensaje": "No hay partidas en el presupuesto.",
            "nivel": "error",
        })
        return {"errores": errores, "avisos": avisos, "ok": False}

    if requiere_cliente and datos_cliente is not None:
        if not (datos_cliente.get("cliente") or "").strip():
            avisos.append({
                "codigo": "cliente_vacio",
                "mensaje": "No has indicado el nombre del cliente.",
                "nivel": "aviso",
            })
        if not (datos_cliente.get("num_oferta") or "").strip():
            avisos.append({
                "codigo": "oferta_vacia",
                "mensaje": "No has indicado el número de oferta.",
                "nivel": "aviso",
            })

    if margen_global < LIMITES["margen_min"]:
        errores.append({
            "codigo": "margen_global_negativo",
            "mensaje": "El beneficio (%) global no puede ser negativo.",
            "nivel": "error",
        })
    elif margen_global > LIMITES["margen_max"]:
        avisos.append({
            "codigo": "margen_global_alto",
            "mensaje": f"El beneficio global ({margen_global:.1f}%) es muy alto. Revísalo.",
            "nivel": "aviso",
        })

    if colocacion_global < 0:
        errores.append({
            "codigo": "coloc_global_negativa",
            "mensaje": "La colocación global no puede ser negativa.",
            "nivel": "error",
        })
    elif colocacion_global > LIMITES["coloc_max"]:
        avisos.append({
            "codigo": "coloc_global_alta",
            "mensaje": f"La colocación global ({colocacion_global:.2f} €) parece muy alta.",
            "nivel": "aviso",
        })

    filas = []
    for i, item in enumerate(items):
        pos = item.get("pos") or f"Línea {i + 1}"
        uds = item.get("uds", 0)
        coste = item.get("coste_u", 0)

        if not isinstance(uds, (int, float)) or uds <= 0 or uds != int(uds):
            errores.append({
                "codigo": "uds_invalida",
                "pos": pos,
                "mensaje": f"{pos}: las unidades deben ser un número entero mayor que 0.",
                "nivel": "error",
            })
        elif uds > LIMITES["uds_max"]:
            errores.append({
                "codigo": "uds_excesiva",
                "pos": pos,
                "mensaje": f"{pos}: {int(uds)} unidades parece un error (máximo habitual: {LIMITES['uds_max']}).",
                "nivel": "error",
            })
        elif uds > LIMITES["uds_aviso"]:
            avisos.append({
                "codigo": "uds_alta",
                "pos": pos,
                "mensaje": f"{pos}: {int(uds)} unidades es una cantidad elevada. Confírmalo.",
                "nivel": "aviso",
            })

        if coste < 0:
            errores.append({
                "codigo": "coste_negativo",
                "pos": pos,
                "mensaje": f"{pos}: el coste no puede ser negativo.",
                "nivel": "error",
            })
        elif coste == 0:
            avisos.append({
                "codigo": "coste_cero",
                "pos": pos,
                "mensaje": f"{pos}: el coste es 0 €. ¿Es correcto?",
                "nivel": "aviso",
            })
        elif coste > LIMITES["coste_max"]:
            avisos.append({
                "codigo": "coste_alto",
                "pos": pos,
                "mensaje": f"{pos}: el coste ({coste:.2f} €) parece muy alto. Revísalo.",
                "nivel": "aviso",
            })

        fila = _fila_calculada(item, margen_global, colocacion_global)
        filas.append((pos, fila))

        if fila["colocacion"] < 0:
            errores.append({
                "codigo": "coloc_negativa",
                "pos": pos,
                "mensaje": f"{pos}: la colocación no puede ser negativa.",
                "nivel": "error",
            })

        if fila["margen"] < 0:
            errores.append({
                "codigo": "margen_negativo",
                "pos": pos,
                "mensaje": f"{pos}: el margen ({fila['margen']:.1f}%) no puede ser negativo.",
                "nivel": "error",
            })
        elif fila["margen"] > LIMITES["margen_aviso_alto"]:
            avisos.append({
                "codigo": "margen_alto",
                "pos": pos,
                "mensaje": f"{pos}: margen del {fila['margen']:.1f}% — revisa si es correcto.",
                "nivel": "aviso",
            })

        if coste > 0 and fila["pvp_u"] < coste:
            avisos.append({
                "codigo": "pvp_bajo_coste",
                "pos": pos,
                "mensaje": (
                    f"{pos}: el PVP ({fila['pvp_u']:.2f} €) es MENOR que el coste "
                    f"({coste:.2f} €). Estarías vendiendo con pérdida."
                ),
                "nivel": "aviso",
            })

        coste_linea = coste * max(uds, 0)
        if coste_linea > 0 and fila["subtotal"] < coste_linea:
            avisos.append({
                "codigo": "linea_con_perdida",
                "pos": pos,
                "mensaje": (
                    f"{pos}: el total de la línea ({fila['subtotal']:.2f} €) es menor "
                    f"que su coste ({coste_linea:.2f} €)."
                ),
                "nivel": "aviso",
            })

    if filas:
        total_base = sum(f[1]["subtotal"] for f in filas)
        coste_total = sum(
            item.get("coste_u", 0) * item.get("uds", 0) for item in items
        )
        beneficio = total_base - coste_total
        if beneficio < 0:
            avisos.append({
                "codigo": "beneficio_negativo",
                "mensaje": (
                    f"El presupuesto completo tiene pérdida "
                    f"({beneficio:.2f} €). Revisa márgenes y precios."
                ),
                "nivel": "aviso",
            })
        elif beneficio == 0:
            avisos.append({
                "codigo": "beneficio_cero",
                "mensaje": "El presupuesto no genera beneficio (0 €).",
                "nivel": "aviso",
            })

    return {
        "errores": errores,
        "avisos": avisos,
        "ok": len(errores) == 0,
    }
