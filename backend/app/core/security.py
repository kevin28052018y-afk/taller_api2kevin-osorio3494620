from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.db.mongodb import get_database

ALGORITMO = "HS256"
bearer = HTTPBearer(auto_error=False)


def hashear_password(password: str) -> str:
    # bcrypt solo admite 72 bytes
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode()[:72], password_hash.encode())
    except ValueError:
        return False


def crear_token(usuario_id: str) -> str:
    vence = datetime.now(timezone.utc) + timedelta(minutes=settings.TOKEN_MINUTOS)
    return jwt.encode({"sub": usuario_id, "exp": vence}, settings.SECRET_KEY, algorithm=ALGORITMO)


def _no_autorizado(detalle: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detalle)


async def get_current_user(
    credenciales: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> dict:
    """Lee el JWT del header Authorization y devuelve el usuario de MongoDB."""
    if credenciales is None:
        raise _no_autorizado("Falta el token de autenticación")
    try:
        payload = jwt.decode(credenciales.credentials, settings.SECRET_KEY, algorithms=[ALGORITMO])
        oid = ObjectId(payload["sub"])
    except (jwt.PyJWTError, KeyError, InvalidId, TypeError):
        raise _no_autorizado("Token inválido o vencido")

    usuario = await db["usuarios"].find_one({"_id": oid})
    if usuario is None or usuario.get("disabled", False):
        raise _no_autorizado("Usuario no válido")
    return usuario
