"""GSPresupuestos Web - API FastAPI."""

import json
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from auth import (
    auth_habilitado,
    crear_token,
    obtener_payload,
    obtener_user_id,
    obtener_user_id_opcional,
    requiere_admin,
)
from fichas import (
    CATEGORIAS,
    add_ficha,
    delete_ficha,
    get_ficha_bytes,
    list_fichas,
    update_ficha,
)
from pdf_merge import merge_pdfs
from calculos import aplicar_margenes, calcular_totales
from generador_pdf import generar_pdf_bytes, generar_resumen_pdf_bytes
from parser_pdf import asociar_dibujos_a_partidas, extraer_dibujos
from parser_txt import parse_txt_bytes
from store import (
    delete_oferta,
    get_condiciones,
    get_logo_bytes,
    get_logo_path,
    get_oferta,
    get_perfil,
    list_ofertas,
    save_condiciones,
    save_logo,
    save_oferta,
    save_perfil,
)
from users import (
    authenticate,
    create_user,
    delete_user,
    ensure_admin,
    list_users,
    update_password,
)

load_dotenv()

app = FastAPI(title="GSPresupuestos Web")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup():
    ensure_admin(
        os.getenv("ADMIN_EMAIL", "admin@gspresupuestos.com"),
        os.getenv("ADMIN_PASSWORD", "GspAdmin2026!"),
    )


def _html_page(nombre: str) -> str:
    path = os.path.join(STATIC_DIR, nombre)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(404, f"{nombre} no encontrado")


class LoginRequest(BaseModel):
    email: str
    password: str


class CalcularRequest(BaseModel):
    items: list[dict]
    margen_global: float = 20.0
    colocacion_global: float = 50.0


class GenerarPdfRequest(BaseModel):
    items: list[dict]
    datos_cliente: dict
    condiciones_texto: str = ""


class GenerarPdfPaqueteRequest(GenerarPdfRequest):
    ficha_ids: list[str] = []


class PerfilRequest(BaseModel):
    nombre_empresa: str = ""
    telefono: str = ""
    email_empresa: str = ""
    direccion: str = ""
    cif: str = ""
    pie_texto: str = ""


class CondicionesRequest(BaseModel):
    condiciones: list[dict]


class OfertaRequest(BaseModel):
    nombre: str = "Sin nombre"
    num_oferta: str = ""
    cliente: str = ""
    datos: dict


class CrearUsuarioRequest(BaseModel):
    email: str
    password: str
    nombre: str = ""


class ResetPasswordRequest(BaseModel):
    password: str


class FichaUpdateRequest(BaseModel):
    nombre: str | None = None
    categoria: str | None = None
    activa: bool | None = None


def _perfil_pdf(user_id: str) -> dict:
    perfil = get_perfil(user_id)
    logo_bytes = get_logo_bytes(user_id)
    return {
        "es_usuario": True,
        "nombre_empresa": perfil.get("nombre_empresa") or "",
        "cif": perfil.get("cif") or "",
        "direccion": perfil.get("direccion") or "",
        "telefono": perfil.get("telefono") or "",
        "email_empresa": perfil.get("email_empresa") or "",
        "pie_texto": perfil.get("pie_texto") or "",
        "logo_bytes": logo_bytes,
        "logo_path": perfil.get("logo_path"),
    }


@app.get("/", response_class=HTMLResponse)
def inicio():
    return _html_page("index.html")


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return _html_page("login.html")


@app.get("/perfil", response_class=HTMLResponse)
def perfil_page():
    return _html_page("perfil.html")


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return _html_page("admin.html")


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": "gspresupuestos-web",
        "version": "2.1-native-auth",
        "auth_enabled": auth_habilitado(),
    }


@app.get("/api/config")
def config_publica():
    return {"auth_enabled": auth_habilitado()}


@app.post("/api/login")
def api_login(req: LoginRequest):
    user = authenticate(req.email, req.password)
    if not user:
        raise HTTPException(401, "Email o contraseña incorrectos.")
    token = crear_token(user)
    public = {
        "id": user["id"],
        "email": user["email"],
        "nombre": user.get("nombre", ""),
        "is_admin": bool(user.get("is_admin")),
    }
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": public,
    }


@app.get("/api/me")
def api_me(payload: dict = Depends(obtener_payload)):
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "nombre": payload.get("nombre", ""),
        "is_admin": bool(payload.get("is_admin")),
    }


@app.get("/api/perfil")
def api_get_perfil(user_id: str = Depends(obtener_user_id)):
    return get_perfil(user_id)


@app.put("/api/perfil")
def api_save_perfil(req: PerfilRequest, user_id: str = Depends(obtener_user_id)):
    perfil = get_perfil(user_id)
    perfil.update(req.model_dump())
    return save_perfil(user_id, perfil)


@app.get("/api/perfil/logo")
def api_get_logo(user_id: str = Depends(obtener_user_id)):
    path = get_logo_path(user_id)
    if not path:
        raise HTTPException(404, "Sin logo.")
    return FileResponse(path)


@app.post("/api/perfil/logo")
async def api_upload_logo(
    file: UploadFile = File(...),
    user_id: str = Depends(obtener_user_id),
):
    if not file.filename:
        raise HTTPException(400, "Archivo no válido.")
    ext = os.path.splitext(file.filename.lower())[1]
    if ext not in (".png", ".jpg", ".jpeg", ".gif"):
        raise HTTPException(400, "Solo PNG, JPG o GIF.")
    data = await file.read()
    path = save_logo(user_id, data, ext)
    return {"logo_path": path, "ok": True}


@app.get("/api/condiciones")
def api_get_condiciones(user_id: str = Depends(obtener_user_id)):
    return {"condiciones": get_condiciones(user_id)}


@app.put("/api/condiciones")
def api_save_condiciones(req: CondicionesRequest, user_id: str = Depends(obtener_user_id)):
    return {"condiciones": save_condiciones(user_id, req.condiciones)}


@app.get("/api/ofertas")
def api_list_ofertas(user_id: str = Depends(obtener_user_id)):
    return {"ofertas": list_ofertas(user_id)}


@app.get("/api/ofertas/{oferta_id}")
def api_get_oferta(oferta_id: str, user_id: str = Depends(obtener_user_id)):
    oferta = get_oferta(user_id, oferta_id)
    if not oferta:
        raise HTTPException(404, "Oferta no encontrada.")
    return oferta


@app.post("/api/ofertas")
def api_save_oferta(req: OfertaRequest, user_id: str = Depends(obtener_user_id)):
    return save_oferta(user_id, req.model_dump())


@app.put("/api/ofertas/{oferta_id}")
def api_update_oferta(
    oferta_id: str,
    req: OfertaRequest,
    user_id: str = Depends(obtener_user_id),
):
    if not get_oferta(user_id, oferta_id):
        raise HTTPException(404, "Oferta no encontrada.")
    return save_oferta(user_id, req.model_dump(), oferta_id=oferta_id)


@app.delete("/api/ofertas/{oferta_id}")
def api_delete_oferta(oferta_id: str, user_id: str = Depends(obtener_user_id)):
    if not get_oferta(user_id, oferta_id):
        raise HTTPException(404, "Oferta no encontrada.")
    delete_oferta(user_id, oferta_id)
    return {"ok": True}


# ── ADMIN ───────────────────────────────────────────────

@app.get("/api/admin/usuarios")
def api_admin_list_users(_admin: dict = Depends(requiere_admin)):
    return {"usuarios": list_users()}


@app.post("/api/admin/usuarios")
def api_admin_create_user(req: CrearUsuarioRequest, _admin: dict = Depends(requiere_admin)):
    try:
        user = create_user(req.email, req.password, req.nombre)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return user


@app.put("/api/admin/usuarios/{user_id}/password")
def api_admin_reset_password(
    user_id: str,
    req: ResetPasswordRequest,
    _admin: dict = Depends(requiere_admin),
):
    try:
        update_password(user_id, req.password)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


@app.delete("/api/admin/usuarios/{user_id}")
def api_admin_delete_user(user_id: str, _admin: dict = Depends(requiere_admin)):
    if user_id == _admin.get("sub"):
        raise HTTPException(400, "No puedes eliminar tu propia cuenta.")
    try:
        delete_user(user_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"ok": True}


# ── FICHAS TÉCNICAS ─────────────────────────────────────

@app.get("/api/fichas")
def api_list_fichas(user_id: str = Depends(obtener_user_id)):
    return {"fichas": list_fichas(solo_activas=True), "categorias": CATEGORIAS}


@app.get("/api/admin/fichas")
def api_admin_list_fichas(_admin: dict = Depends(requiere_admin)):
    return {"fichas": list_fichas(solo_activas=False), "categorias": CATEGORIAS}


@app.post("/api/admin/fichas")
async def api_admin_add_ficha(
    file: UploadFile = File(...),
    nombre: str = Form(...),
    categoria: str = Form("otros"),
    activa: bool = Form(True),
    _admin: dict = Depends(requiere_admin),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Solo archivos PDF.")
    data = await file.read()
    if not data:
        raise HTTPException(400, "Archivo vacío.")
    try:
        return add_ficha(nombre, categoria, data, activa=activa)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@app.put("/api/admin/fichas/{ficha_id}")
def api_admin_update_ficha(
    ficha_id: str,
    req: FichaUpdateRequest,
    _admin: dict = Depends(requiere_admin),
):
    try:
        return update_ficha(ficha_id, nombre=req.nombre, categoria=req.categoria, activa=req.activa)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@app.delete("/api/admin/fichas/{ficha_id}")
def api_admin_delete_ficha(ficha_id: str, _admin: dict = Depends(requiere_admin)):
    try:
        delete_ficha(ficha_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    return {"ok": True}


@app.post("/api/generar-pdf-paquete")
def generar_pdf_paquete(
    req: GenerarPdfPaqueteRequest,
    user_id: str = Depends(obtener_user_id),
):
    if not req.items:
        raise HTTPException(400, "No hay partidas para generar el PDF.")
    perfil = _perfil_pdf(user_id)
    try:
        pdf_presupuesto = generar_pdf_bytes(
            req.items,
            req.datos_cliente,
            req.condiciones_texto,
            perfil=perfil,
        )
    except Exception as e:
        raise HTTPException(500, f"Error al generar PDF: {e}") from e

    partes = [pdf_presupuesto]
    for ficha_id in req.ficha_ids:
        data = get_ficha_bytes(ficha_id)
        if data:
            partes.append(data)

    if len(partes) == 1:
        pdf_final = pdf_presupuesto
        sufijo = ""
    else:
        try:
            pdf_final = merge_pdfs(partes)
        except Exception as e:
            raise HTTPException(500, f"Error al unir fichas: {e}") from e
        sufijo = "_completo"

    num = req.datos_cliente.get("num_oferta", "presupuesto").replace("/", "-")
    return Response(
        content=pdf_final,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Presupuesto_{num}{sufijo}.pdf"'},
    )


# ── PRESUPUESTOS ────────────────────────────────────────

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
def generar_pdf(
    req: GenerarPdfRequest,
    user_id: str = Depends(obtener_user_id),
):
    if not req.items:
        raise HTTPException(400, "No hay partidas para generar el PDF.")
    perfil = _perfil_pdf(user_id)
    try:
        pdf_bytes = generar_pdf_bytes(
            req.items,
            req.datos_cliente,
            req.condiciones_texto,
            perfil=perfil,
        )
    except Exception as e:
        raise HTTPException(500, f"Error al generar PDF: {e}") from e
    num = req.datos_cliente.get("num_oferta", "presupuesto").replace("/", "-")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Presupuesto_{num}.pdf"'},
    )


@app.post("/api/generar-resumen-pdf")
def generar_resumen_pdf(
    req: GenerarPdfRequest,
    user_id: str | None = Depends(obtener_user_id_opcional),
):
    if not req.items:
        raise HTTPException(400, "No hay partidas para generar el resumen.")
    perfil = _perfil_pdf(user_id) if user_id else None
    try:
        pdf_bytes = generar_resumen_pdf_bytes(req.items, req.datos_cliente, perfil=perfil)
    except Exception as e:
        raise HTTPException(500, f"Error al generar resumen: {e}") from e
    num = req.datos_cliente.get("num_oferta", "resumen").replace("/", "-")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Resumen_Calculos_{num}.pdf"'},
    )
