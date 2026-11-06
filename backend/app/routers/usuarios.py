from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, EmailStr

from app.core.security import (
    crear_token,
    get_current_user,
    hashear_password,
    verificar_password,
)
from app.db.mongodb import get_database
from app.models.usuarios import UserCreate, UserResponse

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(
    usuario: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Registra un usuario nuevo (la contraseña se guarda con hash)."""
    email = usuario.email.lower()
    existe = await db["usuarios"].find_one(
        {"$or": [{"email": email}, {"username": usuario.username}]}
    )
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese correo o nombre de usuario",
        )

    data = usuario.model_dump(exclude={"password"})
    data["email"] = email
    data["password_hash"] = hashear_password(usuario.password)
    data["disabled"] = False
    data["created_at"] = datetime.now(timezone.utc)

    resultado = await db["usuarios"].insert_one(data)
    data["_id"] = resultado.inserted_id
    return data


@router.post("/login")
async def login(datos: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Devuelve el JWT y los datos del usuario (formato que espera Django)."""
    usuario = await db["usuarios"].find_one({"email": datos.email.lower()})
    if usuario is None or not verificar_password(datos.password, usuario.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
        )
    if usuario.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="El usuario está deshabilitado"
        )

    return {
        "access_token": crear_token(str(usuario["_id"])),
        "token_type": "bearer",
        "usuario": UserResponse.model_validate(usuario).model_dump(by_alias=True, mode="json"),
    }


@router.get("/me", response_model=UserResponse)
async def mi_perfil(usuario: dict = Depends(get_current_user)):
    """Devuelve el usuario dueño del token."""
    return usuario
