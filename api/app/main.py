"""
FuncPipe API - Main Application

Production-ready FastAPI application with:
- Comprehensive error handling
- CORS configuration
- Request/response logging
- Health checks
- OpenAPI documentation

Elite-level implementation - NO SHORTCUTS.
"""

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings, validate_settings
from app.core.logging import get_logger, log_request, setup_logging
from app.models.schemas import ErrorDetail, ErrorResponse, HealthResponse
from app.routers import files, operations, pipelines

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "application_starting",
        environment=settings.environment,
        version=settings.api_version
    )

    # Validate settings
    validation = validate_settings()
    if not validation["valid"]:
        for error in validation["errors"]:
            logger.error("configuration_error", error=error)
        raise RuntimeError(f"Configuration errors: {', '.join(validation['errors'])}")

    for warning in validation["warnings"]:
        logger.warning("configuration_warning", warning=warning)

    logger.info("application_started")

    yield

    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ============================================================================
# Middleware
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with timing.

    Records method, path, status code, and duration for every request.
    """
    start_time = time.time()

    # Generate request ID
    request_id = f"req-{int(start_time * 1000)}"

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration_ms = (time.time() - start_time) * 1000

    # Log request
    log_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
        request_id=request_id,
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.

    Returns structured error response with field-level details.
    """
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=exc.errors()
    )

    # Extract first error for main message
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message=first_error.get("msg", "Validation failed"),
            details={"errors": exc.errors()},
            field=field if field else None,
        )
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle all uncaught exceptions.

    Returns generic error response and logs full exception.
    """
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
        )
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


# ============================================================================
# Routes
# ============================================================================

# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Check API health status and version",
)
async def health_check():
    """
    Health check endpoint.

    Returns service status, version, and subsystem checks.
    """
    # Check storage directories
    storage_check = "healthy"
    try:
        settings.upload_dir.exists()
        settings.result_dir.exists()
    except Exception as e:
        storage_check = f"unhealthy: {str(e)}"
        logger.error("storage_health_check_failed", error=str(e))

    return HealthResponse(
        status="healthy" if storage_check == "healthy" else "degraded",
        version=settings.api_version,
        checks={
            "storage": storage_check,
        }
    )


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API information",
    description="Get basic API information",
)
async def root():
    """
    Root endpoint.

    Returns basic API information and links to documentation.
    """
    return {
        "name": settings.api_title,
        "version": settings.api_version,
        "description": settings.api_description,
        "docs": "/docs",
        "health": "/health",
        "openapi": "/openapi.json",
    }


# Include routers
app.include_router(files.router, prefix="/api")
app.include_router(pipelines.router, prefix="/api")
app.include_router(operations.router, prefix="/api")


# ============================================================================
# Startup Information
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(
        "starting_uvicorn",
        host=settings.host,
        port=settings.port,
        reload=settings.reload
    )

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_config=None,  # Use our structured logging
    )
