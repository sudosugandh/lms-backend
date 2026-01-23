from fastapi import APIRouter
from app.api.public import website

router = APIRouter(prefix="/public", tags=["public"])

router.include_router(website.router)
