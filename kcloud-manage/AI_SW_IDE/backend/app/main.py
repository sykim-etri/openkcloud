# app/main.py
from fastapi import FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import engine, Base
from app.api.router import api_router
from app.api.routes.proxy import proxy_kernelspecs, proxy_static_files, proxy_nbextensions
import csv
from app.models import user, gpu, k8s
from app.db.session import SessionLocal
from app.core.config import CORS_ORIGINS, APP_PORT, GPU_FETCH
from app.db.init_database import init_users_from_csv, init_flavors_from_csv
from app.db.fetch_gpu import sync_flavors_to_db, sync_gpu_pod_status_from_prometheus
from app.core.logger import app_logger

async def scheduled_sync_gpu_flavors():
    """GPU flavor synchronization task that runs every 30 seconds"""
    try:
        await sync_flavors_to_db()  # Synchronize gpu_flavor table
        await sync_gpu_pod_status_from_prometheus()  # Synchronize servers table
    except Exception as e:
        app_logger.error(f"GPU sync error: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables in development (use Alembic etc. for production management)
    Base.metadata.create_all(bind=engine)
    init_users_from_csv("./app/db/default_users.csv")
    init_flavors_from_csv("./app/db/default_gpu_flavors.csv")
    
    # Start APScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        scheduled_sync_gpu_flavors, 
        "interval", 
        seconds=GPU_FETCH,
        id="sync_gpu_flavors",
        replace_existing=True
    )
    scheduler.start()
    app_logger.info(f"GPU sync scheduler started ({GPU_FETCH}s interval)")
    
    yield
    
    # Cleanup scheduler on app shutdown
    scheduler.shutdown()
    app_logger.info("GPU sync scheduler stopped")

app = FastAPI(lifespan=lifespan)

# Remove middleware to avoid logging interference
# If proxy logs are too verbose, adjust with uvicorn startup options:
# uvicorn app.main:app --log-level warning

# CORS middleware configuration (use "*" in development, specify allowed domains in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
            *CORS_ORIGINS,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Register direct routers for static files like kernelspecs
app.add_api_route("/kernelspecs/{path:path}", proxy_kernelspecs, methods=["GET"])
app.add_api_route("/static/{path:path}", proxy_static_files, methods=["GET"])
app.add_api_route("/nbextensions/{path:path}", proxy_nbextensions, methods=["GET"])

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="My API",
        version="1.0.0",
        description="API using OAuth2 Password Flow",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2Password": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/login",
                    "scopes": {}
                }
            }
        }
    }
    # Add security configuration to each endpoint
    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"OAuth2Password": []})
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application."}

