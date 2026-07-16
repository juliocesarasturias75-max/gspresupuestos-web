"""Fichas técnicas PDF (series, vidrios, garantías, etc.)."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from data_paths import get_data_dir

FICHAS_DIR = os.path.join(get_data_dir(), "_fichas")
FILES_DIR = os.path.join(FICHAS_DIR, "files")
CATALOGO_FILE = os.path.join(FICHAS_DIR, "catalogo.json")

CATEGORIAS = {
    "series": "Series de ventana",
    "vidrios": "Vidrios",
    "cajones": "Cajones",
    "garantias": "Garantías",
    "otros": "Otros",
}


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dirs():
    os.makedirs(FILES_DIR, exist_ok=True)


def _load() -> list:
    _ensure_dirs()
    if not os.path.exists(CATALOGO_FILE):
        return []
    with open(CATALOGO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(fichas: list):
    _ensure_dirs()
    with open(CATALOGO_FILE, "w", encoding="utf-8") as f:
        json.dump(fichas, f, indent=2, ensure_ascii=False)


def list_fichas(solo_activas: bool = False) -> list:
    fichas = _load()
    fichas.sort(key=lambda x: (x.get("categoria", "otros"), x.get("orden", 0), x.get("nombre", "")))
    if solo_activas:
        fichas = [f for f in fichas if f.get("activa", True)]
    return [_publica(f) for f in fichas]


def _publica(f: dict) -> dict:
    return {
        "id": f["id"],
        "nombre": f.get("nombre", ""),
        "categoria": f.get("categoria", "otros"),
        "categoria_label": CATEGORIAS.get(f.get("categoria", "otros"), "Otros"),
        "activa": f.get("activa", True),
        "orden": f.get("orden", 0),
        "created_at": f.get("created_at"),
    }


def get_ficha(ficha_id: str) -> Optional[dict]:
    for f in _load():
        if f["id"] == ficha_id:
            return f
    return None


def get_ficha_bytes(ficha_id: str) -> Optional[bytes]:
    f = get_ficha(ficha_id)
    if not f:
        return None
    path = os.path.join(FILES_DIR, f.get("filename", ""))
    if not os.path.exists(path):
        return None
    with open(path, "rb") as fh:
        return fh.read()


def add_ficha(nombre: str, categoria: str, data: bytes, activa: bool = True) -> dict:
    _ensure_dirs()
    if categoria not in CATEGORIAS:
        categoria = "otros"
    ficha_id = str(uuid.uuid4())
    filename = f"{ficha_id}.pdf"
    path = os.path.join(FILES_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    fichas = _load()
    orden = max([x.get("orden", 0) for x in fichas], default=0) + 1
    row = {
        "id": ficha_id,
        "nombre": nombre.strip(),
        "categoria": categoria,
        "activa": activa,
        "orden": orden,
        "filename": filename,
        "created_at": _ahora(),
    }
    fichas.append(row)
    _save(fichas)
    return _publica(row)


def update_ficha(ficha_id: str, nombre: str = None, categoria: str = None, activa: bool = None, orden: int = None) -> dict:
    fichas = _load()
    for f in fichas:
        if f["id"] == ficha_id:
            if nombre is not None:
                f["nombre"] = nombre.strip()
            if categoria is not None and categoria in CATEGORIAS:
                f["categoria"] = categoria
            if activa is not None:
                f["activa"] = activa
            if orden is not None:
                f["orden"] = orden
            _save(fichas)
            return _publica(f)
    raise ValueError("Ficha no encontrada.")


def delete_ficha(ficha_id: str):
    fichas = _load()
    target = None
    for f in fichas:
        if f["id"] == ficha_id:
            target = f
            break
    if not target:
        raise ValueError("Ficha no encontrada.")
    path = os.path.join(FILES_DIR, target.get("filename", ""))
    if os.path.exists(path):
        os.remove(path)
    _save([f for f in fichas if f["id"] != ficha_id])
