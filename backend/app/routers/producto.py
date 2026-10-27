from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ReturnDocument

from app.db.mongodb import get_database
from app.models.producto import ProductoCreate, ProductoResponse, ProductoUpdate

router = APIRouter(prefix="/productos", tags=["Productos"])


def validar_object_id(producto_id: str) -> ObjectId:
    """Convierte el id recibido en la URL a ObjectId o lanza 400 si no es válido."""
    try:
        return ObjectId(producto_id)
    except (InvalidId, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El id del producto no es válido",
        )


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: ProductoCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Crea un nuevo producto en MongoDB Atlas."""
    data = producto.model_dump()
    resultado = await db["productos"].insert_one(data)
    data["_id"] = resultado.inserted_id
    return data


@router.get("/", response_model=list[ProductoResponse])
async def listar_productos(db: AsyncIOMotorDatabase = Depends(get_database)):
    """Obtiene el listado de los primeros 100 productos."""
    return await db["productos"].find().to_list(length=100)


@router.get("/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(
    producto_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Obtiene un producto por su id."""
    oid = validar_object_id(producto_id)
    producto = await db["productos"].find_one({"_id": oid})
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado"
        )
    return producto


@router.patch("/{producto_id}", response_model=ProductoResponse)
async def editar_producto(
    producto_id: str,
    cambios: ProductoUpdate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    """Actualiza parcialmente un producto: solo se modifican los campos enviados."""
    oid = validar_object_id(producto_id)

    datos = cambios.model_dump(exclude_unset=True)
    if not datos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes enviar al menos un campo para actualizar",
        )

    producto = await db["productos"].find_one_and_update(
        {"_id": oid},
        {"$set": datos},
        return_document=ReturnDocument.AFTER,
    )
    if producto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado"
        )
    return producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(
    producto_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Elimina definitivamente un producto de la base de datos."""
    oid = validar_object_id(producto_id)

    resultado = await db["productos"].delete_one({"_id": oid})
    if resultado.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado"
        )