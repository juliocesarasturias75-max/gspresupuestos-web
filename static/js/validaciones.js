/** Comprobaciones de coherencia para presupuestos (cliente). */

const GSP_LIMITES = {
    uds_max: 200,
    uds_aviso: 50,
    margen_min: 0,
    margen_max: 150,
    margen_aviso_alto: 80,
    coste_max: 50000,
    coloc_max: 5000,
};

function gspCalcularFila(item, margenGlobal, colocGlobal) {
    let margen = item.margen_individual;
    if (margen === null || margen === undefined) margen = item.margen_aplicado;
    if (margen === null || margen === undefined) margen = margenGlobal;
    let coloc = item.colocacion_individual;
    if (coloc === null || coloc === undefined) coloc = item.colocacion_aplicada;
    if (coloc === null || coloc === undefined) coloc = colocGlobal;
    const pvp_u = (item.coste_u + coloc) * (1 + margen / 100);
    const subtotal = pvp_u * item.uds;
    return { margen, colocacion: coloc, pvp_u, subtotal };
}

function validarPresupuesto(items, opts = {}) {
    const margenGlobal = opts.margenGlobal ?? 20;
    const colocGlobal = opts.colocGlobal ?? 50;
    const datosCliente = opts.datosCliente || {};
    const requiereCliente = !!opts.requiereCliente;

    const errores = [];
    const avisos = [];
    const filasConProblema = new Set();

    function marcar(pos) {
        if (pos) filasConProblema.add(pos);
    }

    if (!items || !items.length) {
        errores.push({ codigo: "sin_partidas", mensaje: "No hay partidas en el presupuesto.", nivel: "error" });
        return { errores, avisos, ok: false, filasConProblema };
    }

    if (requiereCliente) {
        if (!(datosCliente.cliente || "").trim()) {
            avisos.push({ codigo: "cliente_vacio", mensaje: "No has indicado el nombre del cliente.", nivel: "aviso" });
        }
        if (!(datosCliente.num_oferta || "").trim()) {
            avisos.push({ codigo: "oferta_vacia", mensaje: "No has indicado el número de oferta.", nivel: "aviso" });
        }
    }

    if (margenGlobal < GSP_LIMITES.margen_min) {
        errores.push({ codigo: "margen_global_negativo", mensaje: "El beneficio (%) global no puede ser negativo.", nivel: "error" });
    } else if (margenGlobal > GSP_LIMITES.margen_max) {
        avisos.push({ codigo: "margen_global_alto", mensaje: `El beneficio global (${margenGlobal.toFixed(1)}%) es muy alto. Revísalo.`, nivel: "aviso" });
    }

    if (colocGlobal < 0) {
        errores.push({ codigo: "coloc_global_negativa", mensaje: "La colocación global no puede ser negativa.", nivel: "error" });
    } else if (colocGlobal > GSP_LIMITES.coloc_max) {
        avisos.push({ codigo: "coloc_global_alta", mensaje: `La colocación global (${colocGlobal.toFixed(2)} €) parece muy alta.`, nivel: "aviso" });
    }

    const filas = [];
    for (let i = 0; i < items.length; i++) {
        const item = items[i];
        const pos = item.pos || `Línea ${i + 1}`;
        const uds = Number(item.uds);
        const coste = Number(item.coste_u);

        if (!uds || uds <= 0 || !Number.isFinite(uds) || Math.floor(uds) !== uds) {
            errores.push({ codigo: "uds_invalida", pos, mensaje: `${pos}: las unidades deben ser un número entero mayor que 0.`, nivel: "error" });
            marcar(pos);
        } else if (uds > GSP_LIMITES.uds_max) {
            errores.push({ codigo: "uds_excesiva", pos, mensaje: `${pos}: ${uds} unidades parece un error (máximo habitual: ${GSP_LIMITES.uds_max}).`, nivel: "error" });
            marcar(pos);
        } else if (uds > GSP_LIMITES.uds_aviso) {
            avisos.push({ codigo: "uds_alta", pos, mensaje: `${pos}: ${uds} unidades es una cantidad elevada. Confírmalo.`, nivel: "aviso" });
            marcar(pos);
        }

        if (!Number.isFinite(coste) || coste < 0) {
            errores.push({ codigo: "coste_negativo", pos, mensaje: `${pos}: el coste no puede ser negativo.`, nivel: "error" });
            marcar(pos);
        } else if (coste === 0) {
            avisos.push({ codigo: "coste_cero", pos, mensaje: `${pos}: el coste es 0 €. ¿Es correcto?`, nivel: "aviso" });
            marcar(pos);
        } else if (coste > GSP_LIMITES.coste_max) {
            avisos.push({ codigo: "coste_alto", pos, mensaje: `${pos}: el coste (${coste.toFixed(2)} €) parece muy alto. Revísalo.`, nivel: "aviso" });
            marcar(pos);
        }

        const fila = gspCalcularFila(item, margenGlobal, colocGlobal);
        filas.push(fila);

        if (fila.colocacion < 0) {
            errores.push({ codigo: "coloc_negativa", pos, mensaje: `${pos}: la colocación no puede ser negativa.`, nivel: "error" });
            marcar(pos);
        }

        if (fila.margen < 0) {
            errores.push({ codigo: "margen_negativo", pos, mensaje: `${pos}: el margen (${fila.margen.toFixed(1)}%) no puede ser negativo.`, nivel: "error" });
            marcar(pos);
        } else if (fila.margen > GSP_LIMITES.margen_aviso_alto) {
            avisos.push({ codigo: "margen_alto", pos, mensaje: `${pos}: margen del ${fila.margen.toFixed(1)}% — revisa si es correcto.`, nivel: "aviso" });
            marcar(pos);
        }

        if (coste > 0 && fila.pvp_u < coste) {
            avisos.push({
                codigo: "pvp_bajo_coste",
                pos,
                mensaje: `${pos}: el PVP (${fila.pvp_u.toFixed(2)} €) es MENOR que el coste (${coste.toFixed(2)} €). Estarías vendiendo con pérdida.`,
                nivel: "aviso",
            });
            marcar(pos);
        }

        const costeLinea = coste * Math.max(uds || 0, 0);
        if (costeLinea > 0 && fila.subtotal < costeLinea) {
            avisos.push({
                codigo: "linea_con_perdida",
                pos,
                mensaje: `${pos}: el total de la línea (${fila.subtotal.toFixed(2)} €) es menor que su coste (${costeLinea.toFixed(2)} €).`,
                nivel: "aviso",
            });
            marcar(pos);
        }
    }

    if (filas.length) {
        const totalBase = filas.reduce((s, f) => s + f.subtotal, 0);
        const costeTotal = items.reduce((s, it) => s + (it.coste_u || 0) * (it.uds || 0), 0);
        const beneficio = totalBase - costeTotal;
        if (beneficio < 0) {
            avisos.push({
                codigo: "beneficio_negativo",
                mensaje: `El presupuesto completo tiene pérdida (${beneficio.toFixed(2)} €). Revisa márgenes y precios.`,
                nivel: "aviso",
            });
        } else if (beneficio === 0) {
            avisos.push({ codigo: "beneficio_cero", mensaje: "El presupuesto no genera beneficio (0 €).", nivel: "aviso" });
        }
    }

    return { errores, avisos, ok: errores.length === 0, filasConProblema };
}

function validarCampoNumerico(tipo, valor) {
    const n = parseFloat(valor);
    if (isNaN(n)) return { ok: false, mensaje: "Introduce un número válido." };
    if (tipo === "uds") {
        const u = parseInt(valor, 10);
        if (!u || u <= 0) return { ok: false, mensaje: "Las unidades deben ser mayor que 0." };
        if (u > GSP_LIMITES.uds_max) return { ok: false, mensaje: `Máximo habitual: ${GSP_LIMITES.uds_max} unidades.` };
    }
    if (tipo === "coste" && n < 0) return { ok: false, mensaje: "El coste no puede ser negativo." };
    if (tipo === "coloc" && n < 0) return { ok: false, mensaje: "La colocación no puede ser negativa." };
    if (tipo === "margen" && n < 0) return { ok: false, mensaje: "El margen no puede ser negativo." };
    return { ok: true, valor: n };
}

function formatearListaValidacion(resultado) {
    const lineas = [];
    for (const e of resultado.errores) lineas.push("❌ " + e.mensaje);
    for (const a of resultado.avisos) lineas.push("⚠️ " + a.mensaje);
    return lineas.join("\n");
}

function confirmarSiHayAvisos(resultado, accion) {
    const errores = resultado?.errores || [];
    const avisos = resultado?.avisos || [];
    if (!resultado?.ok) {
        alert(
            "No se puede continuar. Corrige estos errores:\n\n" +
            errores.map((e) => "• " + e.mensaje).join("\n")
        );
        return false;
    }
    if (avisos.length) {
        const lista = avisos.slice(0, 8).map((a) => "• " + a.mensaje).join("\n");
        const extra = avisos.length > 8 ? `\n... y ${avisos.length - 8} aviso(s) más.` : "";
        return confirm(
            `ATENCIÓN — Se han detectado ${avisos.length} aviso(s):\n\n${lista}${extra}\n\n¿${accion} igualmente bajo tu responsabilidad?`
        );
    }
    return true;
}
