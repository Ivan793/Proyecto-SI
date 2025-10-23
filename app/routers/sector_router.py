from fastapi import APIRouter, Depends, status, Body, Request
from typing import List, Dict, Any
import logging

from app.schemas.sector import SectorCreate, SectorUpdate, SectorResponse
from app.services.sector_service import SectorService
from app.dependencies.auth_dependencies import get_current_admin_user
from app.core.rate_limiter import admin_rate_limit
from app.utils.responses import (
    success_response, created_response, updated_response, 
    not_found_response, conflict_response, internal_server_error_response,
    message_response
)
from app.utils.swagger_docs import ResponseDocumentation
from app.exceptions.sector_exceptions import SectorNotFoundException, SectorAlreadyExistsException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sectores - Administración"])


@router.post(
    "", 
    status_code=status.HTTP_201_CREATED,
    summary="Crear sector",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def create_sector(
    request: Request,
    sector_data: SectorCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SectorService()
        sector = await service.create_sector(sector_data)
        return created_response(
            data=sector.model_dump(), 
            message="Sector creado exitosamente"
        )
    except SectorAlreadyExistsException as e:
        return conflict_response(message=str(e))
    except Exception as e:
        logger.error(f"Error creando sector: {str(e)}")
        return internal_server_error_response()


@router.get(
    "", 
    status_code=status.HTTP_200_OK,
    summary="Obtener todos los sectores",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_sectors(
    request: Request,
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SectorService()
        sectors = await service.get_all_sectors()
        return success_response(
            data=[s.model_dump() for s in sectors], 
            message="Sectores obtenidos correctamente"
        )
    except Exception as e:
        logger.error(f"Error obteniendo sectores: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{sector_id}", 
    status_code=status.HTTP_200_OK,
    summary="Obtener sector por ID",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def get_sector(
    sector_id: str, 
    request: Request, 
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SectorService()
        sector = await service.get_sector(sector_id)
        return success_response(
            data=sector.model_dump(), 
            message="Sector obtenido correctamente"
        )
    except SectorNotFoundException:
        return not_found_response("Sector", sector_id)
    except Exception as e:
        logger.error(f"Error obteniendo sector {sector_id}: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{sector_id}", 
    status_code=status.HTTP_200_OK,
    summary="Actualizar sector",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def update_sector(
    sector_id: str, 
    sector_data: SectorUpdate, 
    request: Request, 
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SectorService()
        sector = await service.update_sector(sector_id, sector_data)
        return updated_response(
            data=sector.model_dump(), 
            message="Sector actualizado correctamente"
        )
    except SectorNotFoundException:
        return not_found_response("Sector", sector_id)
    except Exception as e:
        logger.error(f"Error actualizando sector {sector_id}: {str(e)}")
        return internal_server_error_response()


@router.delete(
    "/{sector_id}", 
    status_code=status.HTTP_200_OK,
    summary="Eliminar sector",
    responses=ResponseDocumentation.get_standard_responses()
)
@admin_rate_limit()
async def delete_sector(
    sector_id: str, 
    request: Request, 
    current_admin: Dict[str, Any] = Depends(get_current_admin_user)
):
    try:
        service = SectorService()
        success = await service.delete_sector(sector_id)
        return message_response("Sector eliminado correctamente")
    except SectorNotFoundException:
        return not_found_response("Sector", sector_id)
    except Exception as e:
        logger.error(f"Error eliminando sector {sector_id}: {str(e)}")
        return internal_server_error_response()