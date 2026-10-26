from datetime import datetime, timezone
from typing import Annotated, Literal
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

# Convierte el ObjectId nativo de Mongo a un str en las respuestas de la API
PyObjectId = Annotated[str, BeforeValidator(str)]

# Estados válidos permitidos para la orden
EstadoPedido = Literal["pendiente", "pagado", "enviado", "entregado", "cancelado"]


class ItemPedido(BaseModel):
    producto_id: str = Field(..., example="65fdcd3bfa1234567890abcd")
    cantidad: int = Field(..., gt=0, example=2)
    precio_unitario: float = Field(..., gt=0, example=15.99)


class PedidoBase(BaseModel):
    cliente_nombre: str = Field(..., min_length=1, max_length=100, example="Juan Pérez")
    cliente_email: str = Field(..., min_length=3, max_length=150, example="juan@example.com")
    direccion_envio: str | None = Field(default=None, example="Av. Siempre Viva 742")
    items: list[ItemPedido] = Field(..., min_length=1)


class PedidoCreate(PedidoBase):
    pass


class PedidoUpdate(BaseModel):
    estado: EstadoPedido


class PedidoResponse(PedidoBase):
    id: PyObjectId = Field(alias="_id")
    estado: EstadoPedido = "pendiente"
    total: float = Field(..., ge=0)
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)

