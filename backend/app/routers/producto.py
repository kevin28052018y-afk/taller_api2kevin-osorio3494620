from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import get_database
from app.models.producto import ProductoCreate, ProductoResponse

router = APIRouter(prefix="/productos", tags=["Productos"])


@router.post("/", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: ProductoCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    data = producto.model_dump()
    resultado = await db["productos"].insert_one(data)
    data["_id"] = resultado.inserted_id
    return data


@router.get("/", response_model=list[ProductoResponse])
async def listar_productos(db: AsyncIOMotorDatabase = Depends(get_database)):
    return await db["productos"].find().to_list(length=100)
