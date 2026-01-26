from fastapi import APIRouter
from app.api.student import attendance, quizzes, assignments, results, leave, timetables, notifications, fees, certificates, gradebook, permissions, files

router = APIRouter(prefix="/student", tags=["student"])

router.include_router(attendance.router)
router.include_router(quizzes.router)
router.include_router(assignments.router)
router.include_router(results.router)
router.include_router(leave.router)
router.include_router(timetables.router)
router.include_router(notifications.router)
router.include_router(fees.router)
router.include_router(certificates.router)
router.include_router(gradebook.router)
router.include_router(permissions.router)
router.include_router(files.router)