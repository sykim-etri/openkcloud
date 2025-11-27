from fastapi import APIRouter

from app.api.routes import auth, server, proxy, metrics, storage

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["login"])
api_router.include_router(server.router, prefix="/server", tags=["server"])
api_router.include_router(proxy.router, prefix="/proxy", tags=["proxy"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
