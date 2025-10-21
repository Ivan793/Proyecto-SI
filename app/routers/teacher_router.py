# ...existing code...
from fastapi import APIRouter, HTTPException
from typing import List
from app.services import teacher_service
from app.schemas.subject import SubjectBase
from app.schemas.group import Grupo
from app.schemas.proyect import Proyecto

router = APIRouter(prefix="/docentes", tags=["Docentes"])

@router.get("/{id_docente}/asignaturas", response_model=List[SubjectBase])
def get_asignaturas(id_docente: str):
    subjects = teacher_service.listar_asignaturas_docente(id_docente)
    return subjects

@router.get("/{id_docente}/asignaturas/{codigo_asignatura}/grupos", response_model=List[Grupo])
def get_grupos(id_docente: str, codigo_asignatura: str):
    asignaturas = teacher_service.listar_asignaturas_docente(id_docente)
    codigos = [a.codigo for a in asignaturas]
    if codigo_asignatura not in codigos:
        raise HTTPException(status_code=403, detail="Asignatura no asignada al docente")
    groups = teacher_service.listar_grupos_asignatura(codigo_asignatura)
    return groups

@router.get("/{id_docente}/proyectos", response_model=List[Proyecto])
def get_proyectos(id_docente: str):
    proyectos = teacher_service.listar_proyectos_docente(id_docente)
    return proyectos

@router.get("/materias")
def get_materias():
    materias = teacher_service.get_materias()
    return materias