from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from typing import List
import logging
import json

from app.schemas.proyect import ProyectoCreate, ProyectoResponse, ProyectoUpdate
from app.repositories.proyect_repository import ProyectoRepository
from app.services import proyect_service
from app.exceptions.base_exceptions import AppException
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
    summary="Crear proyecto con PDF",
    description="Crea un nuevo proyecto con archivo PDF obligatorio. El campo `proyecto_data` debe ser un JSON string con la estructura de ProyectoCreate.",
    responses=ResponseDocumentation.get_standard_responses()
)
async def create_proyecto(
    proyecto_data: str = Form(..., description="Datos del proyecto en formato JSON"),
    archivo: UploadFile = File(..., description="Archivo PDF del proyecto"),
):
    """
    Crea un nuevo proyecto con archivo PDF obligatorio.
    El campo `proyecto_data` debe ser un JSON string con la estructura de ProyectoCreate.
    """
    try:
        proyecto_dict = json.loads(proyecto_data)
        new_id = await repository.create_with_pdf(proyecto_dict, archivo)
        created = await repository.get_by_id(new_id)
        
        return created_response(
            data=created,
            message="Proyecto creado exitosamente"
        )
    except json.JSONDecodeError:
        logger.error("Error: proyecto_data no es JSON válido")
        raise HTTPException(status_code=400, detail="El campo 'proyecto_data' debe ser JSON válido.")
    except AppException as e:
        logger.error(f"Error de aplicación creando proyecto: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error inesperado creando proyecto: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/",
    response_model=None,
    summary="Listar proyectos",
    description="Lista todos los proyectos registrados en el sistema.",
    responses=ResponseDocumentation.get_standard_responses()
)
async def list_proyectos(request: Request):
    """
    Lista todos los proyectos activos en el sistema.
    """
    try:
        proyectos = await repository.get_all()
        
        return success_response(
            data=proyectos,
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
async def get_proyecto(
    request: Request,
    proyecto_id: str
):
    """
    Obtiene los detalles de un proyecto específico por su ID.
    """
    try:
        proyecto = await repository.get_by_id(proyecto_id)
        
        if not proyecto:
            return not_found_response("Proyecto", proyecto_id)
        
        return success_response(
            data=proyecto,
            message="Proyecto obtenido exitosamente"
        )
    except Exception as e:
        logger.error(f"Error obteniendo proyecto {proyecto_id}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{proyecto_id}",
    response_model=None,
    summary="Actualizar proyecto",
    description="Actualiza los datos de un proyecto existente. El PDF es opcional.",
    responses=ResponseDocumentation.get_standard_responses()
)
async def update_proyecto(
    request: Request,
    proyecto_id: str,
    proyecto_data: str = Form(..., description="Datos del proyecto en formato JSON"),
    archivo: UploadFile = File(None, description="Archivo PDF del proyecto (opcional)")
):
    """
    Actualiza un proyecto. El PDF es opcional.
    Si no se proporciona archivo, solo se actualizan los datos del proyecto.
    """
    try:
        proyecto_dict = json.loads(proyecto_data)
        await repository.update_with_pdf(proyecto_id, proyecto_dict, archivo)
        updated = await repository.get_by_id(proyecto_id)
        
        if not updated:
            return not_found_response("Proyecto", proyecto_id)
        
        return updated_response(
            data=updated,
            message="Proyecto actualizado exitosamente"
        )
    except json.JSONDecodeError:
        logger.error("Error: proyecto_data no es JSON válido")
        raise HTTPException(status_code=400, detail="El campo 'proyecto_data' debe ser JSON válido.")
    except AppException as e:
        logger.error(f"Error de aplicación actualizando proyecto: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error inesperado actualizando proyecto {proyecto_id}: {str(e)}")
        return internal_server_error_response()


@router.delete(
    "/{proyecto_id}",
    summary="Eliminar proyecto",
    description="Elimina lógicamente un proyecto (marca como inactivo).",
    responses=ResponseDocumentation.get_standard_responses()
)
async def delete_proyecto(
    request: Request,
    proyecto_id: str
):
    """
    Elimina lógicamente un proyecto (marca como inactivo).
    El proyecto no se elimina físicamente de la base de datos.
    """
    try:
        success = await repository.soft_delete(proyecto_id)
        
        if not success:
            return not_found_response("Proyecto", proyecto_id)
        
        return message_response("Proyecto desactivado correctamente")
    except Exception as e:
        logger.error(f"Error eliminando proyecto {proyecto_id}: {str(e)}")
        return internal_server_error_response()