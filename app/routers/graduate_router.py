from fastapi import APIRouter, HTTPException, status, Query, Request
from typing import Optional
import logging

from app.services.graduate_service import GraduateService
from app.schemas.graduate import GraduateCreate, GraduateResponse, GraduateUpdate
from app.utils.responses import (
    success_response, created_response, updated_response,
    not_found_response, bad_request_response, internal_server_error_response,
    message_response
)
from app.utils.swagger_docs import ResponseDocumentation

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/egresados",
    tags=["Egresados"]
)

graduate_service = GraduateService()


@router.post(
    "",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Crear egresado con usuario (CASCADA)",
    responses=ResponseDocumentation.get_standard_responses()
)
async def create_graduate_with_user(
    request: Request,
    graduate_data: GraduateCreate
):
    try:
        result = await graduate_service.create_graduate_with_user(graduate_data)
        return created_response(
            data=result.model_dump(),
            message="Egresado creado exitosamente"
        )
    except ValueError as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error interno creando egresado: {str(e)}")
        return internal_server_error_response()


@router.get(
    "", 
    response_model=None,
    summary="Listar egresados activos",
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_all_graduates(
    request: Request
):
    try:
        graduates, _ = await graduate_service.get_all_graduates()
        return success_response(
            data=[grad.model_dump() for grad in graduates],
            message="Egresados obtenidos exitosamente"
        )
    except Exception as e:
        logger.error(f"Error al listar egresados: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{graduate_id}", 
    response_model=None,
    summary="Obtener egresado por ID",
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_graduate(
    request: Request,
    graduate_id: str
):
    try:
        result = await graduate_service.get_graduate(graduate_id)
        return success_response(
            data=result.model_dump(),
            message="Egresado obtenido exitosamente"
        )
    except Exception as e:
        return not_found_response("Egresado", graduate_id)


@router.put(
    "/{graduate_id}", 
    response_model=None,
    summary="Actualizar egresado",
    responses=ResponseDocumentation.get_standard_responses()
)
async def update_graduate(
    request: Request,
    graduate_id: str, 
    graduate_data: GraduateUpdate
):
    try:
        result = await graduate_service.update_graduate(graduate_id, graduate_data)
        return updated_response(
            data=result.model_dump(),
            message="Egresado actualizado exitosamente"
        )
    except Exception as e:
        return bad_request_response(message=str(e))


@router.delete(
    "/{graduate_id}", 
    summary="Desactivar egresado",
    responses=ResponseDocumentation.get_standard_responses()
)
async def deactivate_graduate(
    request: Request,
    graduate_id: str,
    reason: str = Query("Desactivado por administrador", description="Motivo de la desactivación")
):
    try:
        await graduate_service.deactivate_graduate(graduate_id, reason)
        return message_response(f"Egresado {graduate_id} desactivado correctamente")
    except Exception as e:
        return bad_request_response(message=str(e))