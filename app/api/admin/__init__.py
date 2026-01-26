from fastapi import APIRouter
from app.api.admin import profile, users, teachers, students, classes, results, leave, timetables, notifications, parents, fees, certificates, cms, gradebook, permissions, pages, attendance, files, exports

router = APIRouter(prefix="/admin", tags=["admin"])

router.include_router(profile.router)
router.include_router(users.router)
router.include_router(teachers.router)
router.include_router(students.router)
router.include_router(classes.router)
router.include_router(results.router)
router.include_router(leave.router)
router.include_router(timetables.router)
router.include_router(notifications.router)
router.include_router(parents.router)
router.include_router(fees.router)
router.include_router(certificates.router)
router.include_router(cms.router)
router.include_router(gradebook.router)
router.include_router(permissions.router)
router.include_router(pages.router)
router.include_router(attendance.router)
router.include_router(files.router)
router.include_router(exports.router)