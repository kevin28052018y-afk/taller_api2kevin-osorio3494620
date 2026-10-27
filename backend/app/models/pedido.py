from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

PyObjectId = Annotated[str, BeforeValidator(str)]


class ItemPedidoCreate(BaseModel):
    producto_id: str = Field(..., example="665f1c2e8b3a4d0012ab34cd")
    cantidad: int = Field(..., gt=0, example=2)


class ItemPedido(BaseModel):
    """Item guardado: copia nombre y precio al momento de la compra."""
    producto_id: str
    nombre: str
    precio_unitario: float
    cantidad: int
    subtotal: float


class PedidoCreate(BaseModel):
    usuario_id: str = Field(..., example="665f1c2e8b3a4d0012ab34ce")
    items: list[ItemPedidoCreate] = Field(..., min_length=1)


class PedidoResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    usuario_id: str
    items: list[ItemPedido]
    total: float
    activo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)