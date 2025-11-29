"""
FastAPI application setup and configuration.
"""

import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.agents import router as agents_router
from app.api.store import router as stores_router
from app.models.schemas import BaseResponse, HealthCheck
from app.services.store_service import store_service
from app.utils.http_client import close_http_client, init_http_client
from app.utils.logger import logger
from app.utils.middleware import RequestIDMiddleware
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting AI Learning Assistant RPG application")

    # Initialize services
    try:
        init_http_client()
        await store_service.init()
        logger.info("LLM service is available")
        os.makedirs(settings.card_folder, exist_ok=True)

    except Exception as e:
        logger.error(f"Error during service initialization: {e}")

    yield
    await close_http_client()
    logger.info("Shutting down AI Learning Assistant RPG application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI Learning Assistant with RPG-style progression using FastAPI, LangChain, and local LLM",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Add Request ID middleware (should be added first to ensure it's available for all requests)
app.add_middleware(RequestIDMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(["*"]),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    err_stack = traceback.format_exc(limit=5)
    logger.error(f"Unhandled exception: {str(exc)}", extra={"stack": err_stack})
    data = {}
    if settings.debug:
        data["stack"] = err_stack
        data["detail"] = str(exc)

    return JSONResponse(
        status_code=500,
        content=BaseResponse.error(
            code=500,
            message="Internal server error",
            data=data,
        ).model_dump(),
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Application health check."""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now(),
        version=settings.app_version,
    )


# Include API routers
app.include_router(agents_router, prefix="/api/agents", tags=["agents"])
app.include_router(stores_router, prefix="/api/store", tags=["store"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
