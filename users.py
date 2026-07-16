"""Gestión de usuarios con contraseñas cifradas."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import bcrypt

from data_paths import get_data_dir
from store import init_user_data

REGISTRY_DIR = os.path.join(get_data_dir(), "_registry")
USERS_FILE = os.path.join(REGISTRY_DIR, "users.json")
TERMINOS_VERSION = "1.0"


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _load_all() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_all(users: dict):
    os.makedirs(REGISTRY_DIR, exist_ok=True)
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)


def _terminos_vigentes(user: dict) -> bool:
    return (
        user.get("terminos_version") == TERMINOS_VERSION
        and bool(user.get("terminos_aceptados_at"))
    )


def _public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "email": user["email"],
        "nombre": user.get("nombre", ""),
        "is_admin": bool(user.get("is_admin")),
        "activo": user.get("activo", True),
        "created_at": user.get("created_at"),
        "terminos_aceptados": _terminos_vigentes(user),
        "terminos_aceptados_at": user.get("terminos_aceptados_at"),
        "terminos_version": user.get("terminos_version"),
    }


def terminos_aceptados(user_id: str) -> bool:
    user = get_user(user_id)
    return bool(user and _terminos_vigentes(user))


def get_terminos_estado(user_id: str) -> dict:
    user = get_user(user_id)
    if not user:
        raise ValueError("Usuario no encontrado.")
    return {
        "version_actual": TERMINOS_VERSION,
        "aceptado": _terminos_vigentes(user),
        "aceptado_at": user.get("terminos_aceptados_at"),
        "version_aceptada": user.get("terminos_version"),
    }


def aceptar_terminos(user_id: str) -> dict:
    users = _load_all()
    if user_id not in users:
        raise ValueError("Usuario no encontrado.")
    users[user_id]["terminos_aceptados_at"] = _ahora()
    users[user_id]["terminos_version"] = TERMINOS_VERSION
    _save_all(users)
    return get_terminos_estado(user_id)


def list_users() -> list:
    return [_public_user(u) for u in _load_all().values()]


def get_user(user_id: str) -> Optional[dict]:
    return _load_all().get(user_id)


def find_by_email(email: str) -> Optional[dict]:
    email = email.strip().lower()
    for user in _load_all().values():
        if user.get("email", "").lower() == email:
            return user
    return None


def authenticate(email: str, password: str) -> Optional[dict]:
    user = find_by_email(email)
    if not user or not user.get("activo", True):
        return None
    if not _check_password(password, user["password_hash"]):
        return None
    return user


def create_user(
    email: str,
    password: str,
    nombre: str = "",
    is_admin: bool = False,
) -> dict:
    email = email.strip().lower()
    if not email or not password:
        raise ValueError("Email y contraseña obligatorios.")
    if len(password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    if find_by_email(email):
        raise ValueError("Ya existe un usuario con ese email.")

    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": email,
        "nombre": nombre.strip(),
        "password_hash": _hash_password(password),
        "is_admin": is_admin,
        "activo": True,
        "created_at": _ahora(),
    }
    users = _load_all()
    users[user_id] = user
    _save_all(users)
    init_user_data(user_id)
    return _public_user(user)


def update_password(user_id: str, new_password: str):
    if len(new_password) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
    users = _load_all()
    if user_id not in users:
        raise ValueError("Usuario no encontrado.")
    users[user_id]["password_hash"] = _hash_password(new_password)
    _save_all(users)


def set_active(user_id: str, activo: bool):
    users = _load_all()
    if user_id not in users:
        raise ValueError("Usuario no encontrado.")
    users[user_id]["activo"] = activo
    _save_all(users)


def delete_user(user_id: str):
    users = _load_all()
    if user_id not in users:
        raise ValueError("Usuario no encontrado.")
    admins = [u for u in users.values() if u.get("is_admin") and u.get("activo", True)]
    if users[user_id].get("is_admin") and len(admins) <= 1:
        raise ValueError("No puedes eliminar el último administrador.")
    del users[user_id]
    _save_all(users)


def ensure_admin(email: str, password: str):
    """Crea el admin inicial si no hay usuarios."""
    users = _load_all()
    if not users:
        create_user(email, password, nombre="Administrador", is_admin=True)
        return
    existing = find_by_email(email)
    if existing:
        if not existing.get("is_admin"):
            users[existing["id"]]["is_admin"] = True
            _save_all(users)
