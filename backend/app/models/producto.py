from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# Convierte el ObjectId de Mongo a str automáticamente en las respuestas JSON
PyObjectId = Annotated[str, BeforeValidator(str)]


class ProductoBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100, example="Laptop Gamer")
    descripcion: Optional[str] = Field(default=None, example="Procesador i7 con 16GB RAM")
    precio: float = Field(..., gt=0, example=1250.99)
    stock: int = Field(default=0, ge=0, example=10)
    categoria: Optional[str] = Field(default=None, example="Tecnología")
    activo: bool = Field(default=True)


class ProductoCreate(ProductoBase):
    pass


class ProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(default=None, min_length=1, max_length=100)
    descripcion: Optional[str] = None
    precio: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    categoria: Optional[str] = None
    activo: Optional[bool] = None


class ProductoResponse(ProductoBase):
    id: PyObjectId = Field(alias="_id")

    model_config = ConfigDict(populate_by_name=True)