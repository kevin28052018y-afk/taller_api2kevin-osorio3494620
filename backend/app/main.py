from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Conexión interna de tu base de datos
from app.db import mongodb
# Importación de ambos routers (Productos y Pedidos)
from app.routers import producto, pedido


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Evento de inicio del servidor: Conecta a MongoDB Atlas
    await mongodb.connect_to_mongo()
    yield
    # Evento de apagado del servidor: Cierra la conexión de forma segura
    await mongodb.close_mongo_connection()


# Inicialización de FastAPI con metadatos para la documentación de Swagger
app = FastAPI(
    title="Mi FastAPI Project", 
    version="0.1.0", 
    description="API 100% funcional con CRUD de Productos y Gestión de Pedidos",
    lifespan=lifespan
)

# Configuración de Middlewares (CORS) para permitir la comunicación con el Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción en Render, puedes limitarlo a la URL de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de los Routers en la aplicación central
app.include_router(producto.router)
app.include_router(pedido.router)


@app.get("/", tags=["General"])
async def raiz():
    """
    Endpoint raíz para verificar de forma rápida que la API responda en la Web.
    """
    return {
        "mensaje": "API funcionando exitosamente 🚀",
        "documentacion": "/docs"
    }


@app.get("/health", tags=["General"])
async def health():
    """
    Endpoint de monitoreo (Health Check) útil para plataformas como Render.
    Verifica la salud de la API y realiza un ping de conectividad a MongoDB Atlas.
    """
    try:
        # Intenta hacer un ping administrativo a la base de datos
        await mongodb.client.admin.command("ping")
        return {"api": "ok", "mongodb": "ok"}
    except Exception as e:
        return {"api": "ok", "mongodb": f"error de conexión: {str(e)}"}
