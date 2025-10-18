
from fastapi import APIRouter
from app.controllers.student_controller import (
    crear_estudiante_controlador,
    obtener_todos_estudiantes_controlador,
    actualizar_estudiante_controlador
)

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])

@router.post("/", response_description="Estudiante y usuario creados en cascada exitosamente")
def crear_estudiante(data: dict):
    return crear_estudiante_controlador(data)

@router.get("/", response_description="Lista de estudiantes obtenida exitosamente")
def obtener_estudiantes():
    return obtener_todos_estudiantes_controlador()

@router.put("/{id_estudiante}", response_description="Estudiante actualizado exitosamente")
def actualizar_estudiante(id_estudiante: str, data: dict):
    return actualizar_estudiante_controlador(id_estudiante, data)
