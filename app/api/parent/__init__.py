from fastapi import APIRouter
from app.api.parent import students, fees, certificates, notifications, gradebook, permissions

router = APIRouter(prefix="/parent", tags=["parent"])

router.include_router(students.router)
router.include_router(fees.router)
router.include_router(certificates.router)
router.include_router(notifications.router)
router.include_router(gradebook.router)
router.include_router(permissions.router)