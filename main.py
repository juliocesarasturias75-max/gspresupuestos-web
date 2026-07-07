"""GSPresupuestos Web - API FastAPI."""

import json
import os

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from calculos import aplicar_margenes, calcular_totales
from generador_pdf import generar_pdf_bytes
from parser_pdf import asociar_dibujos_a_partidas, extraer_dibujos
from parser_txt import parse_txt_bytes

app = FastAPI(title="GSPresupuestos Web")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CalcularRequest(BaseModel):
    items: list[dict]
    margen_global: float = 20.0
    colocacion_global: float = 50.0


class GenerarPdfRequest(BaseModel):
    items: list[dict]
    datos_cliente: dict
    condiciones_texto: str = ""


@app.get("/", response_class=HTMLResponse)
def inicio():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>GSPresupuestos Web</h1><p>index.html no encontrado</p>"


@app.get("/api/health")
def health():
    return {"status": "ok", "app": "gspresupuestos-web", "version": "mvp-1"}


@app.post("/api/upload-txt")
async def upload_txt(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".txt"):
        raise HTTPException(400, "Solo se aceptan archivos .txt")
    data = await file.read()
    try:
        items = parse_txt_bytes(data)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Error al procesar TXT: {e}") from e
    if not items:
        raise HTTPException(400, "No se encontraron partidas con precio en el archivo.")
    return {"items": items, "count": len(items)}


@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    items_json: str = Form(...),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo se aceptan archivos .pdf")
    try:
        items = json.loads(items_json)
    except json.JSONDecodeError as e:
        raise HTTPException(400, "items_json no válido") from e
    data = await file.read()
    try:
        dibujos = extraer_dibujos(data)
        items = asociar_dibujos_a_partidas(items, dibujos)
    except RuntimeError as e:
        raise HTTPException(500, str(e)) from e
    except Exception as e:
        raise HTTPException(500, f"Error al procesar PDF: {e}") from e
    return {"items": items, "dibujos_count": len(dibujos)}


@app.post("/api/upload-condiciones")
async def upload_condiciones(file: UploadFile = File(...)):
    data = await file.read()
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            texto = data.decode(enc)
            return {"texto": texto, "filename": file.filename}
        except UnicodeDecodeError:
            continue
    texto = data.decode("latin-1", errors="replace")
    return {"texto": texto, "filename": file.filename}


@app.post("/api/calcular")
def calcular(req: CalcularRequest):
    if not req.items:
        raise HTTPException(400, "No hay partidas.")
    items = aplicar_margenes(req.items, req.margen_global, req.colocacion_global)
    totales = calcular_totales(items)
    return {"items": items, "totales": totales}


@app.post("/api/generar-pdf")
def generar_pdf(req: GenerarPdfRequest):
    if not req.items:
        raise HTTPException(400, "No hay partidas para generar el PDF.")
    try:
        pdf_bytes = generar_pdf_bytes(
            req.items,
            req.datos_cliente,
            req.condiciones_texto,
        )
    except Exception as e:
        raise HTTPException(500, f"Error al generar PDF: {e}") from e
    num = req.datos_cliente.get("num_oferta", "presupuesto").replace("/", "-")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Presupuesto_{num}.pdf"'},
    )
