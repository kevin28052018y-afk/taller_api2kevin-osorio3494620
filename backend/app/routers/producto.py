from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

# Conexión a la base de datos
from app.db.mongodb import get_database
# IMPORTACIÓN CORREGIDA: Apunta directamente al archivo independiente de modelos de producto
from app.models.producto import ProductoCreate, ProductoResponse

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: ProductoCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Crea un nuevo producto en MongoDB Atlas.
    Valida los datos de entrada con el esquema ProductoCreate.
    """
    data = producto.model_dump()
    resultado = await db["productos"].insert_one(data)
    data["_id"] = resultado.inserted_id
    return data


@router.get("/", response_model=list[ProductoResponse])
async def listar_productos(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Obtiene el listado de los primeros 100 productos activos en la base de datos.
    """
    return await db["productos"].find().to_list(length=100)
