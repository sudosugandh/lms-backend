from fastapi import APIRouter
from app.api.auth import routes

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(routes.router)
