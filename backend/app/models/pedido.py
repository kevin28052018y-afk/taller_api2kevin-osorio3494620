from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

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
    """
    Acepta dos formatos:
      1) {"items": [{"producto_id": "...", "cantidad": 2}]}
      2) {"producto_id": "...", "cantidad": 2}   (el que envía Django)
    El usuario se toma del token JWT; `usuario_id` se ignora si llega.
    """
    usuario_id: Optional[str] = None
    items: Optional[list[ItemPedidoCreate]] = None
    producto_id: Optional[str] = Field(default=None, example="665f1c2e8b3a4d0012ab34cd")
    cantidad: Optional[int] = Field(default=None, gt=0, example=2)

    @model_validator(mode="after")
    def normalizar_items(self):
        if not self.items:
            if self.producto_id and self.cantidad:
                self.items = [ItemPedidoCreate(producto_id=self.producto_id, cantidad=self.cantidad)]
            else:
                raise ValueError("Envía 'items' o bien 'producto_id' y 'cantidad'")
        return self


class PedidoResponse(BaseModel):
    id: PyObjectId = Field(alias="_id")
    usuario_id: str
    items: list[ItemPedido]
    total: float
    activo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(populate_by_name=True)