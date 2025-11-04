# app/routers/teacher_public_router.py

from fastapi import APIRouter, HTTPException
from typing import List
from app.services.teacher_service import TeacherService
from app.schemas.proyect import ProyectoBase
from app.schemas.teacher import TeacherBase

router = APIRouter(
    prefix="/api/v1/docentes-publicos",
    tags=["Docentes Públicos"]
)

teacher_service = TeacherService()

# ============================================================
# 🌐 ENDPOINTS PÚBLICOS DE DOCENTES
# ============================================================

@router.get("/proyectos", response_model=List[ProyectoBase])
async def obtener_todos_los_proyectos():
    """
    Lista todos los proyectos disponibles públicamente.
    """
    try:
        proyectos = await teacher_service.list_all_projects()
        return proyectos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyectos: {str(e)}")


@router.get("/{id_docente}/perfil")
async def obtener_informacion_docente(id_docente: str):
    """
    Obtiene información pública del docente (perfil básico).
    """
    try:
        docente = await teacher_service.get_teacher_public_info(id_docente)
        return docente
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Docente no encontrado: {str(e)}")


@router.get("/{id_docente}/materias")
async def obtener_materias_docente(id_docente: str):
    """
    Lista las materias que dicta un docente.
    """
    try:
        materias = await teacher_service.list_teacher_subjects(id_docente)
        return materias
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar materias: {str(e)}")


@router.get("/materias/{codigo_materia}/grupos")
async def obtener_grupos_materia(codigo_materia: str):
    """
    Lista los grupos asociados a una materia.
    """
    try:
        grupos = await teacher_service.list_subject_groups(codigo_materia)
        return grupos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar grupos: {str(e)}")


@router.get("/{id_docente}/proyectos", response_model=List[ProyectoBase])
async def obtener_proyectos_docente(id_docente: str):
    """
    Lista los proyectos en los que participa un docente.
    """
    try:
        proyectos = await teacher_service.list_teacher_projects(id_docente)
        return proyectos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar proyectos: {str(e)}")


@router.get("/proyectos/{id_proyecto}", response_model=ProyectoBase)
async def obtener_detalle_proyecto(id_proyecto: str):
    """
    Obtiene la información detallada de un proyecto público.
    """
    try:
        proyecto = await teacher_service.get_project_info(id_proyecto)
        return proyecto
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Proyecto no encontrado: {str(e)}")
