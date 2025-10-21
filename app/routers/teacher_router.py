from fastapi import APIRouter, HTTPException
from typing import List
from services import teacher_service
from schemas.subject import subject
from schemas.group import group
from schemas.proyect import project

router = APIRouter(prefix="/docentes", tags=["Docentes"])

@router.get("/{id_docente}/asignaturas", response_model=List[subject])
def get_asignaturas(id_docente: str):
    subjects = teacher_service.listar_asignaturas_docente(id_docente)
    return subjects

@router.get("/{id_docente}/asignaturas/{codigo_asignatura}/grupos", response_model=List[group])
def get_grupos(id_docente: str, codigo_asignatura: str):
    # Opción: validar que la asignatura pertenezca al docente antes de devolver grupos
    asignaturas = teacher_service.listar_asignaturas_docente(id_docente)
    codigos = [a.codigo for a in asignaturas]
    if codigo_asignatura not in codigos:
        raise HTTPException(status_code=403, detail="Asignatura no asignada al docente")
    groups = teacher_service.listar_grupos_asignatura(codigo_asignatura)
    return groups

@router.get("/{id_docente}/proyectos", response_model=List[project])
def get_proyectos(id_docente: str):
    proyectos = teacher_service.listar_proyectos_docente(id_docente)
    return proyectos
