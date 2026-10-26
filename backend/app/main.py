from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import mongodb
from app.routers import producto


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongodb.connect_to_mongo()
    yield
    await mongodb.close_mongo_connection()


app = FastAPI(title="Mi FastAPI Project", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, limita a tu dominio del frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(producto.router)


@app.get("/")
async def raiz():
    return {"mensaje": "API funcionando 🚀"}


@app.get("/health")
async def health():
    try:
        await mongodb.client.admin.command("ping")
        return {"api": "ok", "mongodb": "ok"}
    except Exception as e:
        return {"api": "ok", "mongodb": f"error: {e}"}
