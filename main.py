"""
FastAPI application setup and configuration.
"""

from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.models.schemas import ErrorResponse, HealthCheck
from app.utils.http_client import init_http_client
from app.utils.logger import logger
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting AI Learning Assistant RPG application")

    # Initialize services
    try:
        init_http_client()
        logger.info("LLM service is available")

    except Exception as e:
        logger.error(f"Error during service initialization: {e}")

    yield

    logger.info("Shutting down AI Learning Assistant RPG application")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI Learning Assistant with RPG-style progression using FastAPI, LangChain, and local LLM",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"]
        if settings.debug
        else ["http://localhost:3000", "http://127.0.0.1:3000", "http://0.0.0.0:3000"]
    ),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            timestamp=datetime.now(),
            error_code=f"HTTP_{exc.status_code}",
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            msg="Internal server error",
            detail=str(exc) if settings.debug else None,
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


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
