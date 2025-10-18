# app/controllers/student_controller.py
from app.services.student_service import StudentService

student_service = StudentService()

def crear_estudiante_controlador(data: dict):
    return student_service.create_student(data)

def obtener_todos_estudiantes_controlador():
    return student_service.get_all_students()

def actualizar_estudiante_controlador(id_estudiante: str, data: dict):
    return student_service.update_student(id_estudiante, data)
