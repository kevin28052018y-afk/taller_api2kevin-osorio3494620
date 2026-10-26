from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]

EstadoPedido = Literal["pendiente", "pagado", "enviado", "entregado", "cancelado"]


class ItemPedido(BaseModel):
    producto_id: str
    cantidad: int = Field(..., gt=0)
    precio_unitario: float = Field(..., gt=0)


class PedidoBase(BaseModel):
    cliente_nombre: str = Field(..., min_length=1, max_length=100)
    cliente_email: str = Field(..., min_length=3, max_length=150)
    direccion_envio: str | None = None
    items: list[ItemPedido] = Field(..., min_length=1)


class PedidoCreate(PedidoBase):
    pass


class PedidoUpdate(BaseModel):
    estado: EstadoPedido


class PedidoResponse(PedidoBase):
    id: PyObjectId = Field(alias="_id")
    estado: EstadoPedido = "pendiente"
    total: float
    fecha_creacion: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)
