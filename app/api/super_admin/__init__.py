from fastapi import APIRouter
from app.api.super_admin import institutes, domains

router = APIRouter(prefix="/super-admin", tags=["super-admin"])

router.include_router(institutes.router)
router.include_router(domains.router)
