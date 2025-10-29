from app.services.teacher_service import TeacherService


def get_teacher_service() -> TeacherService:
    return TeacherService()