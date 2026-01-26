from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.core.tenant import resolve_institute_by_host
from typing import Callable
import logging
import sys

# Set up logging that goes to stdout (so it shows in uvicorn logs)
logging.basicConfig(level=logging.DEBUG, stream=sys.stdout, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware to resolve tenant (institute) from Host header."""
    
    # Paths that don't require tenant resolution (exact matches only)
    EXCLUDED_PATHS = [
        "/",  # Root - exact match only
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health"
    ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log that middleware is running
        logger.info(f"[TENANT MIDDLEWARE] ===== START =====")
        logger.info(f"[TENANT MIDDLEWARE] Request path: {request.url.path}, Method: {request.method}")
        sys.stdout.flush()
        
        # Skip tenant resolution for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            logger.info(f"[TENANT MIDDLEWARE] OPTIONS request (CORS preflight), skipping tenant resolution")
            sys.stdout.flush()
            return await call_next(request)
        
        # Skip tenant resolution for exact excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            logger.info(f"[TENANT MIDDLEWARE] Path is excluded (exact match), skipping tenant resolution")
            sys.stdout.flush()
            return await call_next(request)
        
        # Skip tenant resolution for super admin endpoints (they don't need domain)
        if request.url.path.startswith("/super-admin"):
            logger.info(f"[TENANT MIDDLEWARE] Super admin path, skipping tenant resolution")
            sys.stdout.flush()
            return await call_next(request)
        
        # Skip tenant resolution for auth endpoints (they handle it themselves)
        if request.url.path.startswith("/auth"):
            logger.info(f"[TENANT MIDDLEWARE] Auth path, skipping tenant resolution")
            sys.stdout.flush()
            return await call_next(request)
        
        # Skip tenant resolution for static file uploads (they don't need tenant context)
        if request.url.path.startswith("/uploads"):
            logger.info(f"[TENANT MIDDLEWARE] Static file path, skipping tenant resolution")
            sys.stdout.flush()
            return await call_next(request)
        
        db: Session = None
        temp_db: Session = None
        try:
            # Try custom X-Host header first (for SSR from Next.js)
            # Then fall back to standard Host header
            x_host = request.headers.get("x-host")
            host_header = request.headers.get("host", "")
            host = x_host or host_header
            
            # Debug: Log what we received (temporary for debugging)
            logger.info(f"[TENANT MIDDLEWARE] Path: {request.url.path}")
            logger.info(f"[TENANT MIDDLEWARE] X-Host: {x_host}")
            logger.info(f"[TENANT MIDDLEWARE] Host: {host_header}")
            logger.info(f"[TENANT MIDDLEWARE] Using host: {host}")
            sys.stdout.flush()
            
            if not host:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Host header is required"
                )
            
            # Create DB session for tenant resolution
            db = SessionLocal()
            
            try:
                # Resolve institute by host (exact match)
                institute = resolve_institute_by_host(db, host)
                
                logger.info(f"[TENANT MIDDLEWARE] Institute lookup result: {institute}")
                sys.stdout.flush()
                
                if not institute:
                    # Provide helpful error message
                    from app.db.models.domain import Domain
                    temp_db = SessionLocal()
                    try:
                        available_domains = temp_db.query(Domain.host_name).filter(Domain.is_active == True).all()
                        available = [d.host_name for d in available_domains]
                    finally:
                        if temp_db:
                            temp_db.rollback()
                            temp_db.close()
                            temp_db = None
                    
                    error_detail = (
                        f"Institute not found for domain '{host}'. "
                        f"Available domains: {', '.join(available) if available else 'None'}. "
                        f"Received X-Host: '{x_host}', Host: '{host_header}'. "
                        f"Make sure the domain exists in the database and matches exactly (including port)."
                    )
                    logger.error(f"[TENANT MIDDLEWARE] ERROR: {error_detail}")
                    sys.stdout.flush()
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=error_detail
                    )
                
                logger.info(f"[TENANT MIDDLEWARE] ✅ Found Institute ID: {institute.id}, Name: {institute.name}")
                
                # Attach institute_id to request state (must be set before call_next)
                request.state.institute_id = institute.id
                request.state.institute = institute
                
                logger.info(f"[TENANT MIDDLEWARE] ✅ Set request.state.institute_id = {institute.id}")
                sys.stdout.flush()
            except Exception:
                # Rollback any pending transaction before closing
                if db:
                    try:
                        db.rollback()
                    except Exception:
                        pass
                raise
            finally:
                # Always close DB session after resolution
                if db:
                    try:
                        db.close()
                    except Exception:
                        pass
                    db = None
            
        except HTTPException as he:
            # HTTP exceptions are re-raised as-is
            logger.error(f"[TENANT MIDDLEWARE] HTTPException: {he.detail}")
            sys.stdout.flush()
            # Ensure all sessions are closed
            if temp_db:
                try:
                    temp_db.rollback()
                    temp_db.close()
                except Exception:
                    pass
            if db:
                try:
                    db.rollback()
                    db.close()
                except Exception:
                    pass
            raise
        except Exception as e:
            # Any other exception is converted to 500 error
            logger.error(f"[TENANT MIDDLEWARE] Exception: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            sys.stdout.flush()
            # Ensure all sessions are closed
            if temp_db:
                try:
                    temp_db.rollback()
                    temp_db.close()
                except Exception:
                    pass
            if db:
                try:
                    db.rollback()
                    db.close()
                except Exception:
                    pass
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error resolving tenant: {str(e)}"
            )
        
        # Verify institute_id was set before proceeding
        if not hasattr(request.state, 'institute_id') or request.state.institute_id is None:
            logger.error(f"[TENANT MIDDLEWARE] ❌ CRITICAL: institute_id not set after try block!")
            sys.stdout.flush()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resolve tenant: institute_id not set"
            )
        
        logger.info(f"[TENANT MIDDLEWARE] ✅ Proceeding with institute_id = {request.state.institute_id}")
        sys.stdout.flush()
        response = await call_next(request)
        return response
