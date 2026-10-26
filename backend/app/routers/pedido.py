from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

# Conexión asíncrona a la base de datos
from app.db.mongodb import get_database
# IMPORTACIÓN CORREGIDA: Apunta a tu subcarpeta y archivo de modelo independiente
from app.models.pedido import PedidoCreate, PedidoResponse

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("/", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def registrar_pedido(
    pedido: PedidoCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Registra un nuevo pedido en MongoDB Atlas.
    Valida la estructura con PedidoCreate, comprueba el stock e inserta el registro.
    """
    # Convertimos el esquema de Pydantic a un diccionario ejecutable
    data_pedido = pedido.model_dump()
    total_calculado = 0.0
    operaciones_stock = []

    # 1. Validar la existencia de cada producto y verificar stock disponible en Mongo
    for item in data_pedido["items"]:
        prod_id_str = item["producto_id"]

        if not ObjectId.is_valid(prod_id_str):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ID de producto no válido: {prod_id_str}"
            )

        # Buscar el producto en la colección utilizando corchetes por consistencia con Motor
        producto = await db["productos"].find_one({"_id": ObjectId(prod_id_str)})
        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El producto con ID {prod_id_str} no existe en inventario."
            )

        # Evaluar restricciones de stock
        stock_actual = producto.get("stock", 0)
        cantidad_solicitada = item["cantidad"]

        if stock_actual < cantidad_solicitada:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para '{producto.get('nombre')}'. Disponible: {stock_actual}, Solicitado: {cantidad_solicitada}"
            )

        # Acumular el valor total multiplicando por el precio unitario del ítem
        total_calculado += item["precio_unitario"] * cantidad_solicitada
        
        # Almacenar la tupla con los cambios listos para aplicar
        operaciones_stock.append((ObjectId(prod_id_str), stock_actual - cantidad_solicitada))

    # 2. Descontar el stock de forma efectiva si ningún ítem falló
    for prod_obj_id, nuevo_stock in operaciones_stock:
        await db["productos"].update_one(
            {"_id": prod_obj_id},
            {"$set": {"stock": nuevo_stock}}
        )

    # 3. Completar campos implícitos requeridos por PedidoResponse
    data_pedido["estado"] = "pendiente"
    data_pedido["total"] = total_calculado

    # Insertar el nuevo pedido en la base de datos
    resultado = await db["pedidos"].insert_one(data_pedido)
    data_pedido["_id"] = resultado.inserted_id

    return data_pedido
