"""Autenticación JWT propia (sin Supabase)."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)

JWT_SECRET = os.getenv("APP_JWT_SECRET", "gsp-cambiar-este-secreto-en-render")
JWT_DAYS = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
AUTH_ENABLED = os.getenv("AUTH_DISABLED", "").lower() != "true"


def auth_habilitado() -> bool:
    return AUTH_ENABLED


def crear_token(user: dict) -> str:
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "nombre": user.get("nombre", ""),
        "is_admin": bool(user.get("is_admin")),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verificar_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(401, "Sesión caducada. Vuelve a iniciar sesión.") from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(401, "Token no válido.") from e


def obtener_payload(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    if not AUTH_ENABLED:
        return {"sub": "dev-local", "email": "dev@local", "is_admin": True}
    if not creds or not creds.credentials:
        raise HTTPException(401, "Debes iniciar sesión.")
    return verificar_token(creds.credentials)


def obtener_user_id(payload: dict = Depends(obtener_payload)) -> str:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Token sin usuario.")
    return user_id


def obtener_user_id_opcional(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[str]:
    if not AUTH_ENABLED:
        return "dev-local"
    if not creds or not creds.credentials:
        return None
    try:
        return verificar_token(creds.credentials).get("sub")
    except HTTPException:
        return None


def requiere_admin(payload: dict = Depends(obtener_payload)) -> dict:
    if not AUTH_ENABLED:
        return payload
    if not payload.get("is_admin"):
        raise HTTPException(403, "Solo administradores.")
    return payload
