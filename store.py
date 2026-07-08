"""Almacenamiento local de perfiles, condiciones y ofertas."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _user_dir(user_id: str) -> str:
    path = os.path.join(DATA_DIR, user_id)
    os.makedirs(path, exist_ok=True)
    return path


def init_user_data(user_id: str):
    """Crea perfil y condiciones por defecto para un usuario nuevo."""
    if not os.path.exists(os.path.join(_user_dir(user_id), "perfil.json")):
        save_perfil(user_id, get_perfil(user_id))
    cond_path = os.path.join(_user_dir(user_id), "condiciones.json")
    if not os.path.exists(cond_path):
        save_condiciones(user_id, get_condiciones(user_id))


# ── PERFIL ──────────────────────────────────────────────

def get_perfil(user_id: str) -> dict:
    default = {
        "user_id": user_id,
        "nombre_empresa": "",
        "telefono": "",
        "email_empresa": "",
        "direccion": "",
        "cif": "",
        "pie_texto": "",
        "logo_path": "",
    }
    path = os.path.join(_user_dir(user_id), "perfil.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return {**default, **json.load(f)}
    return default


def save_perfil(user_id: str, datos: dict) -> dict:
    datos = {**datos, "user_id": user_id, "updated_at": _ahora()}
    path = os.path.join(_user_dir(user_id), "perfil.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    return datos


def save_logo(user_id: str, data: bytes, ext: str) -> str:
    logos_dir = os.path.join(_user_dir(user_id), "logos")
    os.makedirs(logos_dir, exist_ok=True)
    filename = f"logo{ext}"
    path = os.path.join(logos_dir, filename)
    with open(path, "wb") as f:
        f.write(data)
    perfil = get_perfil(user_id)
    perfil["logo_path"] = path
    save_perfil(user_id, perfil)
    return path


def get_logo_bytes(user_id: str) -> Optional[bytes]:
    perfil = get_perfil(user_id)
    logo_path = perfil.get("logo_path")
    if logo_path and os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return f.read()
    return None


def get_logo_path(user_id: str) -> Optional[str]:
    perfil = get_perfil(user_id)
    path = perfil.get("logo_path")
    return path if path and os.path.exists(path) else None


# ── CONDICIONES ─────────────────────────────────────────

def get_condiciones(user_id: str) -> list:
    path = os.path.join(_user_dir(user_id), "condiciones.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return [
        {"id": str(uuid.uuid4()), "user_id": user_id, "nombre": "Condiciones 1", "contenido": "", "orden": 1},
        {"id": str(uuid.uuid4()), "user_id": user_id, "nombre": "Condiciones 2", "contenido": "", "orden": 2},
        {"id": str(uuid.uuid4()), "user_id": user_id, "nombre": "Condiciones 3", "contenido": "", "orden": 3},
    ]


def save_condiciones(user_id: str, condiciones: list) -> list:
    path = os.path.join(_user_dir(user_id), "condiciones.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(condiciones, f, indent=2, ensure_ascii=False)
    return condiciones


# ── OFERTAS ─────────────────────────────────────────────

def list_ofertas(user_id: str) -> list:
    path = os.path.join(_user_dir(user_id), "ofertas")
    if not os.path.isdir(path):
        return []
    result = []
    for fname in os.listdir(path):
        if fname.endswith(".json"):
            with open(os.path.join(path, fname), "r", encoding="utf-8") as f:
                o = json.load(f)
                result.append({
                    "id": o.get("id", fname.replace(".json", "")),
                    "nombre": o.get("nombre", ""),
                    "num_oferta": o.get("num_oferta", ""),
                    "cliente": o.get("cliente", ""),
                    "created_at": o.get("created_at"),
                    "updated_at": o.get("updated_at"),
                })
    result.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return result


def get_oferta(user_id: str, oferta_id: str) -> Optional[dict]:
    fpath = os.path.join(_user_dir(user_id), "ofertas", f"{oferta_id}.json")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_oferta(user_id: str, datos: dict, oferta_id: Optional[str] = None) -> dict:
    now = _ahora()
    if not oferta_id:
        oferta_id = str(uuid.uuid4())
    row = {
        "id": oferta_id,
        "user_id": user_id,
        "nombre": datos.get("nombre", "Sin nombre"),
        "num_oferta": datos.get("num_oferta", ""),
        "cliente": datos.get("cliente", ""),
        "datos": datos.get("datos", datos),
        "updated_at": now,
    }
    odir = os.path.join(_user_dir(user_id), "ofertas")
    os.makedirs(odir, exist_ok=True)
    fpath = os.path.join(odir, f"{oferta_id}.json")
    if os.path.exists(fpath):
        with open(fpath, "r", encoding="utf-8") as f:
            old = json.load(f)
        row["created_at"] = old.get("created_at", now)
    else:
        row["created_at"] = now
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(row, f, indent=2, ensure_ascii=False)
    return row


def delete_oferta(user_id: str, oferta_id: str):
    fpath = os.path.join(_user_dir(user_id), "ofertas", f"{oferta_id}.json")
    if os.path.exists(fpath):
        os.remove(fpath)
