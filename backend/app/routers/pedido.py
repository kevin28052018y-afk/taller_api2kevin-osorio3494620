from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.db.mongodb import get_database
from app.models.pedido import PedidoCreate, PedidoResponse

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def validar_object_id(valor: str, nombre: str = "id") -> ObjectId:
    try:
        return ObjectId(valor)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El {nombre} no es válido",
        )


async def devolver_stock(db: AsyncIOMotorDatabase, items: list[dict]) -> None:
    """Suma de vuelta al stock las cantidades de los items."""
    for item in items:
        await db["productos"].update_one(
            {"_id": ObjectId(item["producto_id"])},
            {"$inc": {"stock": item["cantidad"]}},
        )


async def descontar_stock(db: AsyncIOMotorDatabase, items: list[dict]) -> Optional[dict]:
    """
    Descuenta el stock de cada item de forma atómica.
    Si alguno falla, revierte los anteriores y devuelve ese item; si todo sale bien, devuelve None.
    """
    descontados: list[dict] = []
    for item in items:
        producto = await db["productos"].find_one_and_update(
            {
                "_id": ObjectId(item["producto_id"]),
                "activo": True,
                "stock": {"$gte": item["cantidad"]},
            },
            {"$inc": {"stock": -item["cantidad"]}},
        )
        if producto is None:
            await devolver_stock(db, descontados)
            return item
        descontados.append(item)
    return None


@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def crear_pedido(
    pedido: PedidoCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Crea un pedido: toma nombre y precio desde la BD y descuenta el stock."""
    validar_object_id(pedido.usuario_id, "id de usuario")

    items_guardados: list[dict] = []
    for item in pedido.items:
        oid = validar_object_id(item.producto_id, "id de producto")
        producto = await db["productos"].find_one({"_id": oid})
        if producto is None or not producto.get("activo", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Producto {item.producto_id} no existe o está inactivo",
            )
        items_guardados.append(
            {
                "producto_id": str(producto["_id"]),
                "nombre": producto["nombre"],
                "precio_unitario": producto["precio"],
                "cantidad": item.cantidad,
                "subtotal": round(producto["precio"] * item.cantidad, 2),
            }
        )

    fallido = await descontar_stock(db, items_guardados)
    if fallido is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente para '{fallido['nombre']}'",
        )

    data = {
        "usuario_id": pedido.usuario_id,
        "items": items_guardados,
        "total": round(sum(i["subtotal"] for i in items_guardados), 2),
        "activo": True,
        "created_at": datetime.now(timezone.utc),
    }
    resultado = await db["pedidos"].insert_one(data)
    data["_id"] = resultado.inserted_id
    return data


@router.get("/", response_model=list[PedidoResponse])
async def listar_pedidos(
    activo: Optional[bool] = None,
    usuario_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """
    Lista los últimos 100 pedidos.
    - activo=true  -> solo activos
    - activo=false -> solo cancelados (inactivos)
    - sin activo   -> todos
    """
    filtro: dict = {}
    if activo is not None:
        filtro["activo"] = activo
    if usuario_id:
        filtro["usuario_id"] = usuario_id
    return await db["pedidos"].find(filtro).sort("created_at", -1).to_list(length=100)


@router.get("/{pedido_id}", response_model=PedidoResponse)
async def obtener_pedido(
    pedido_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    oid = validar_object_id(pedido_id, "id del pedido")
    pedido = await db["pedidos"].find_one({"_id": oid})
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado"
        )
    return pedido


@router.patch("/{pedido_id}/cancelar", response_model=PedidoResponse)
async def cancelar_pedido(
    pedido_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Marca el pedido como inactivo y devuelve el stock."""
    oid = validar_object_id(pedido_id, "id del pedido")

    # El filtro activo=True evita devolver el stock dos veces
    pedido = await db["pedidos"].find_one_and_update(
        {"_id": oid, "activo": True},
        {"$set": {"activo": False}},
        return_document=ReturnDocument.AFTER,
    )
    if pedido is None:
        existe = await db["pedidos"].find_one({"_id": oid}, {"_id": 1})
        if existe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pedido ya está cancelado",
        )

    await devolver_stock(db, pedido["items"])
    return pedido


@router.patch("/{pedido_id}/activar", response_model=PedidoResponse)
async def activar_pedido(
    pedido_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Reactiva un pedido cancelado y vuelve a descontar el stock."""
    oid = validar_object_id(pedido_id, "id del pedido")

    pedido = await db["pedidos"].find_one({"_id": oid})
    if pedido is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pedido no encontrado"
        )
    if pedido["activo"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pedido ya está activo",
        )

    fallido = await descontar_stock(db, pedido["items"])
    if fallido is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede reactivar: '{fallido['nombre']}' no existe, está inactivo o no tiene stock suficiente",
        )

    actualizado = await db["pedidos"].find_one_and_update(
        {"_id": oid, "activo": False},
        {"$set": {"activo": True}},
        return_document=ReturnDocument.AFTER,
    )
    if actualizado is None:
        # Otra petición lo activó antes: se deshace el descuento
        await devolver_stock(db, pedido["items"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pedido ya está activo",
        )
    return actualizado