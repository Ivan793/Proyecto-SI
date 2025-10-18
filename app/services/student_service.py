# app/services/student_service.py
from app.repositories.student_repository import create_student, get_all_students, update_student

class StudentService:
    def create_student(self, data):
        return create_student(data)
    
    def get_all_students(self):
        return get_all_students()
    
    def update_student(self, id_estudiante, data):
        return update_student(id_estudiante, data)
