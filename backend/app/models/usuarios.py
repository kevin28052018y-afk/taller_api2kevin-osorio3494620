from datetime import datetime, timezone
from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, EmailStr

# Convierte el ObjectId nativo de Mongo a un str en las respuestas de la API
PyObjectId = Annotated[str, BeforeValidator(str)]


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="juan_perez")
    email: EmailStr = Field(..., example="juan@example.com")
    full_name: Optional[str] = Field(None, example="Juan Pérez")


class UserCreate(UserBase):
    """
    Esquema utilizado exclusivamente para el registro de nuevos usuarios.
    Exige la contraseña obligatoria con un mínimo de seguridad.
    """
    password: str = Field(..., min_length=6, example="PasswordSeguro123!")


class UserResponse(UserBase):
    """
    Esquema público retornado por la API.
    Oculta la contraseña por seguridad y formatea los datos de salida.
    """
    id: PyObjectId = Field(alias="_id")
    disabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Configuración requerida en Pydantic v2 para serializar los alias de MongoDB (_id)
    model_config = ConfigDict(populate_by_name=True)
