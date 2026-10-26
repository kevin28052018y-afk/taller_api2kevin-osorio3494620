from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

client: AsyncIOMotorClient | None = None


async def connect_to_mongo() -> None:
    """Abre la conexión con MongoDB Atlas y verifica que responde."""
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
    try:
        await client.admin.command("ping")
        print("✅ Conectado a MongoDB Atlas")
    except Exception as e:
        print(f"❌ No se pudo conectar a MongoDB Atlas: {e}")


async def close_mongo_connection() -> None:
    global client
    if client is not None:
        client.close()
        client = None


def get_database() -> AsyncIOMotorDatabase:
    if client is None:
        raise RuntimeError("La conexión a MongoDB no está inicializada")
    return client[settings.MONGODB_DB_NAME]
