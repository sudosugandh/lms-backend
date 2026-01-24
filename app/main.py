from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from app.middleware.tenant_middleware import TenantMiddleware
from app.api import auth, super_admin, admin, teacher, student, parent, public
from app.core.config import settings
from app.utils.exceptions import BaseAPIException
import logging

# Configure logging
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s" 
           if settings.ENVIRONMENT == "development" 
           else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
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

# Tenant resolution middleware (after CORS)
app.add_middleware(TenantMiddleware)

# Exception handlers
@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    logger.warning(f"API Exception: {exc.status_code} - {exc.detail}")
    response = JSONResponse(
        status_code=exc.status_code,
        content=exc.detail if isinstance(exc.detail, dict) else {"detail": exc.detail}
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    logger.warning(f"Validation Error on {request.url.path}: {errors}")
    error_messages = [
        f"{' -> '.join(str(l) for l in error.get('loc', []))}: {error.get('msg', 'Validation error')}" 
        for error in errors
    ]
    detail = "Validation error: " + "; ".join(error_messages) if error_messages else "Validation error"
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": detail,
            "error_code": "VALIDATION_ERROR",
            "error_data": {"errors": errors}
        }
    )
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {type(exc).__name__}: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal error occurred" if settings.ENVIRONMENT == "production" else str(exc),
            "error_code": "INTERNAL_ERROR"
        }
    )
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

# Root endpoint redirects to docs
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}

# ===== END OF FILE =====
# No uvicorn.run() here – keep run.py for local development
