from fastapi import APIRouter
from app.api.teacher import classes, attendance, quizzes, assignments, leave, timetables, notifications, gradebook, permissions, files

router = APIRouter(prefix="/teacher", tags=["teacher"])

router.include_router(classes.router)
router.include_router(attendance.router)
router.include_router(quizzes.router)
router.include_router(assignments.router)
router.include_router(leave.router)
router.include_router(timetables.router)
router.include_router(notifications.router)
router.include_router(gradebook.router)
router.include_router(permissions.router)
router.include_router(files.router)