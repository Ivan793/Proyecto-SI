# app/repositories/student_repository.py
from typing import Dict, List
from app.repositories.user_repository import create_user

# Simulación de base de datos en memoria
fake_students_db: List[Dict] = []

# Crear estudiante junto con usuario (en cascada)
def create_student(data: Dict):
    # 1️⃣ Crear primero el usuario
    user_data = data.get("usuario")
    if not user_data:
        return {"mensaje": "⚠️ Datos de usuario faltantes para creación en cascada"}
    
    user_response = create_user(user_data)
    id_usuario = user_response["data"]["id_usuario"]

    # 2️⃣ Crear estudiante asociado al usuario
    new_student = {
        "id_estudiante": f"est_{len(fake_students_db) + 1}",
        "id_usuario": id_usuario,
        "codigo_programa": data.get("codigo_programa"),
        "semestre": data.get("semestre"),
        "anio_ingreso": data.get("anio_ingreso")
    }
    fake_students_db.append(new_student)

    return {
        "mensaje": "✅ Estudiante y usuario creados exitosamente (simulado)",
        "data": {
            "usuario": user_response["data"],
            "estudiante": new_student
        }
    }

def get_all_students():
    return {"total": len(fake_students_db), "estudiantes": fake_students_db}

def update_student(id_estudiante: str, data: Dict):
    for student in fake_students_db:
        if student["id_estudiante"] == id_estudiante:
            for key, value in data.items():
                if key in student:
                    student[key] = value
            return {
                "mensaje": "✅ Estudiante actualizado exitosamente (simulado)",
                "data": student
            }
    return {"mensaje": f"⚠️ No se encontró estudiante con id {id_estudiante}"}
