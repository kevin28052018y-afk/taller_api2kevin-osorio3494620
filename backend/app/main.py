from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db import mongodb
from app.routers import pedido, producto

# En producción reemplaza "*" por la URL de tu frontend, por ejemplo:
# ["https://mi-frontend.onrender.com"]
ORIGENES_PERMITIDOS = ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicio: conecta a MongoDB Atlas
    await mongodb.connect_to_mongo()
    yield
    # Apagado: cierra la conexión de forma segura
    await mongodb.close_mongo_connection()


app = FastAPI(
    title="Mi FastAPI Project",
    version="0.1.0",
    description="API con CRUD de Productos y gestión de Pedidos",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_credentials=False,  # No usas cookies; con "*" debe ir en False
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(producto.router)
app.include_router(pedido.router)


@app.get("/", tags=["General"])
async def raiz():
    """Verifica rápidamente que la API responde."""
    return {
        "mensaje": "API funcionando exitosamente 🚀",
        "documentacion": "/docs",
    }


@app.get("/health", tags=["General"])
async def health():
    """
    Health check para Render u otros monitores.
    Responde 200 si la API y MongoDB funcionan, 503 si MongoDB no responde.
    """
    try:
        if mongodb.client is None:
            raise RuntimeError("Sin conexión inicializada")
        await mongodb.client.admin.command("ping")
        return {"api": "ok", "mongodb": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"api": "ok", "mongodb": "error de conexión"},
        )