from fastapi import APIRouter, HTTPException
from typing import List
import logging
from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.repositories.proyect_repository import ProyectoRepository
from app.exceptions.base_exceptions import AppException
import json
from app.utils.responses import (
    success_response, created_response, updated_response,
    not_found_response, internal_server_error_response,
    message_response
)
from app.utils.swagger_docs import ResponseDocumentation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/proyectos", tags=["Proyectos"])
repository = ProyectoRepository()

@router.post(
    "/", 
    response_model=None,
    summary="Crear proyecto",
    description="Crea un nuevo proyecto en el sistema.",
    responses=ResponseDocumentation.get_standard_responses()
)
def create_proyecto(
    request: Request,
    proyecto: ProyectoCreate
):
    try:
        result = proyect_service.create_proyecto(proyecto)
        return created_response(
            data=result.model_dump(),
            message="Proyecto creado exitosamente"
        )
    except Exception as e:
        logger.error(f"Error creando proyecto: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/", 
    response_model=None,
    summary="Listar proyectos",
    description="Lista todos los proyectos registrados.",
    responses=ResponseDocumentation.get_standard_responses()
)
def list_proyectos(
    request: Request
):
    try:
        result = proyect_service.list_proyectos()
        return success_response(
            data=[proj.model_dump() for proj in result],
            message="Proyectos obtenidos exitosamente"
        )
    except Exception as e:
        logger.error(f"Error listando proyectos: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{proyecto_id}", 
    response_model=None,
    summary="Obtener proyecto por ID",
    description="Obtiene un proyecto específico por su ID.",
    responses=ResponseDocumentation.get_standard_responses()
)
def get_proyecto(
    request: Request,
    proyecto_id: str
):
    try:
        proyecto = proyect_service.get_proyecto(proyecto_id)
        if not proyecto:
            return not_found_response("Proyecto", proyecto_id)
        
        return success_response(
            data=proyecto.model_dump(),
            message="Proyecto obtenido exitosamente"
        )
    except Exception as e:
        logger.error(f"Error obteniendo proyecto: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{proyecto_id}", 
    response_model=None,
    summary="Actualizar proyecto",
    description="Actualiza los datos de un proyecto existente.",
    responses=ResponseDocumentation.get_standard_responses()
)
def update_proyecto(
    request: Request,
    proyecto_id: str, 
    proyecto: ProyectoUpdate
):
    try:
        updated = proyect_service.update_proyecto(proyecto_id, proyecto)
        if not updated:
            return not_found_response("Proyecto", proyecto_id)
        
        return updated_response(
            data=updated.model_dump(),
            message="Proyecto actualizado exitosamente"
        )
    except Exception as e:
        logger.error(f"Error actualizando proyecto: {str(e)}")
        return internal_server_error_response()


@router.delete(
    "/{proyecto_id}",
    summary="Eliminar proyecto",
    description="Elimina un proyecto por su ID.",
    responses=ResponseDocumentation.get_standard_responses()
)
def delete_proyecto(
    request: Request,
    proyecto_id: str
):
    try:
        success = proyect_service.delete_proyecto(proyecto_id)
        if not success:
            return not_found_response("Proyecto", proyecto_id)
        
        return message_response("Proyecto eliminado correctamente")
    except Exception as e:
        logger.error(f"Error eliminando proyecto: {str(e)}")
        return internal_server_error_response()