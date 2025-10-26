from app.services.teacher_service import TeacherService
from app.services.teacher_subject_service import TeacherSubjectService


def get_teacher_service() -> TeacherService:
    return TeacherService()

def get_teacher_subject_service() -> TeacherSubjectService:
    return TeacherSubjectService()