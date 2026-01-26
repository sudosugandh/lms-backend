from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.middleware.tenant_middleware import TenantMiddleware
from app.api import auth, super_admin, admin, teacher, student, parent, public
from app.core.config import settings
from app.utils.exceptions import BaseAPIException
import logging
import os

# Configure logging
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s" if settings.ENVIRONMENT == "development" else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Tenant LMS API",
    description="Multi-tenant Learning Management System with domain-based tenant resolution",
    version="1.0.0"
)

# CORS middleware
cors_origins = ["*"] if settings.ENVIRONMENT == "development" else []
if settings.CORS_ORIGINS:
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant resolution middleware (must be after CORS)
app.add_middleware(TenantMiddleware)

# Global exception handlers
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions with consistent error format."""
    logger.warning(f"API Exception: {exc.status_code} - {exc.detail}")
    response = JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    )
    # Ensure CORS headers are added to error responses
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format and CORS headers."""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    # Ensure CORS headers are added to error responses
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with consistent format."""
    errors = exc.errors()
    logger.warning(f"Validation Error on {request.url.path}: {errors}")
    # Format errors for better readability
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "Validation error")
        error_messages.append(f"{loc}: {msg}")
    
    detail = "Validation error: " + "; ".join(error_messages) if error_messages else "Validation error"
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": detail,
            "error_code": "VALIDATION_ERROR",
            "error_data": {"errors": errors}
        }
    )
    # Ensure CORS headers are added to error responses
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred" if settings.ENVIRONMENT == "production" else str(exc),
            "error_code": "INTERNAL_ERROR"
        }
    )
    # Ensure CORS headers are added to error responses
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# Include routers
app.include_router(auth.router)
app.include_router(super_admin.router)
app.include_router(admin.router)
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(parent.router)
app.include_router(public.router)

# Mount static files for uploads
uploads_dir = settings.UPLOAD_DIR
# Create uploads directory if it doesn't exist
os.makedirs(uploads_dir, exist_ok=True)
os.makedirs(os.path.join(uploads_dir, "assignments"), exist_ok=True)
os.makedirs(os.path.join(uploads_dir, "submissions"), exist_ok=True)

# Mount static files - this must be after middleware but before routes
# Note: StaticFiles will handle 404 if file doesn't exist
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirects to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
