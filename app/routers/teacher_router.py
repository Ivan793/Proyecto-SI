# app/routers/teacher_public_router.py

from fastapi import APIRouter, Depends, HTTPException, Request, logger, status
from typing import Any, Dict, List

from app.dependencies.auth_dependencies import get_current_teacher_user
from app.services.teacher_service import TeacherService
from app.schemas.proyect import ProyectoBase
from app.schemas.teacher import TeacherBase
from app.utils.responses import internal_server_error_response, not_found_response, success_response

router = APIRouter(
    prefix="/docentes",
    tags=["Docentes"]
)

teacher_service = TeacherService()

# Obtener perfil del estudiante autenticado
@router.get("/mi-perfil", status_code=status.HTTP_200_OK, summary="Obtener perfil del docente actual")
async def get_my_profile(request: Request, current_teacher: Dict[str, Any] = Depends(get_current_teacher_user)):
    """
    El docente autenticado puede ver su propio perfil completo
    (incluyendo su usuario asociado).
    """
    try:
        service = TeacherService()

        
        # Buscar el docente por ID de usuario
        teacher = await service.teacher_repo.get_teacher_by_user_id(current_teacher["user_id"])
        if not teacher:
            return not_found_response("Docente", "asociado a su usuario")

        # Obtener información completa del docente
        teacher_with_user = await service.get_teacher_with_user(teacher["id_docente"])

        return success_response(
            data=teacher_with_user.model_dump(),
            message="Perfil obtenido correctamente"
        )
        
    except Exception as e:
        logger.error(f" Error obteniendo perfil: {str(e)}")
        return internal_server_error_response()

# ============================================================
# 🌐 ENDPOINTS PÚBLICOS DE DOCENTES
# ============================================================

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
    
# ============================================================

