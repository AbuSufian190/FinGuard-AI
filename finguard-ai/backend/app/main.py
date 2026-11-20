"""FinGuard AI – FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .database import init_db
from .logging_config import configure_logging
from .ml.predictor import get_predictor
from .routers import dashboard, health, models, predictions, transactions

configure_logging()
logger = logging.getLogger("finguard")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    predictor = get_predictor()
    logger.info("Startup complete. Model loaded=%s", predictor.loaded)
    yield
    logger.info("Shutdown.")


app = FastAPI(
    title="FinGuard AI",
    description="Intelligent Financial Fraud Detection Platform API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500,
                        content={"detail": "Internal server error."})


for r in (health, dashboard, transactions, predictions, models):
    app.include_router(r.router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs",
            "health": f"{settings.api_prefix}/health"}
