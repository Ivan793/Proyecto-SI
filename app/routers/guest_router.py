from fastapi import APIRouter, HTTPException, status, Query, Request
import logging

from app.services.guest_service import GuestService
from app.schemas.guest import GuestCreate, GuestUpdate
from app.utils.responses import (
    success_response, created_response, updated_response,
    not_found_response, bad_request_response, internal_server_error_response,
    message_response
)
from app.utils.swagger_docs import ResponseDocumentation

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/invitados",
    tags=["Invitados"]
)

guest_service = GuestService()


# -------------------------------
# Crear invitado con usuario (CASCADA)
# -------------------------------
@router.post(
    "",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
    summary="Crear invitado con usuario (CASCADA)",
    responses=ResponseDocumentation.get_standard_responses()
)
async def create_guest_with_user(
    request: Request,
    guest_data: GuestCreate
):
    try:
        result = await guest_service.create_guest_with_user(guest_data)
        return created_response(
            data=result.model_dump(),
            message="Invitado creado exitosamente"
        )
    except ValueError as e:
        return bad_request_response(message=str(e))
    except Exception as e:
        logger.error(f"Error interno creando invitado: {str(e)}")
        return internal_server_error_response()


# -------------------------------
# Listar todos los invitados activos
# -------------------------------
@router.get(
    "",
    response_model=None,
    summary="Listar todos los invitados activos",
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_all_guests(
    request: Request
):
    try:
        guests, _ = await guest_service.get_all_guests()
        return success_response(
            data=guests,  # ✅ ahora es lista de dicts {"invitado": {...}, "usuario": {...}}
            message="Invitados obtenidos exitosamente"
        )
    except Exception as e:
        logger.error(f"Error al listar invitados: {str(e)}")
        return internal_server_error_response()


# -------------------------------
# Obtener invitado por ID
# -------------------------------
@router.get(
    "/{guest_id}",
    response_model=None,
    summary="Obtener invitado por ID",
    responses=ResponseDocumentation.get_standard_responses()
)
async def get_guest(
    request: Request,
    guest_id: str
):
    try:
        result = await guest_service.get_guest(guest_id)
        return success_response(
            data=result,  # ✅ ya es {"invitado": {...}, "usuario": {...}}
            message="Invitado obtenido exitosamente"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al obtener invitado {guest_id}: {str(e)}")
        return not_found_response("Invitado", guest_id)


# -------------------------------
# Actualizar invitado
# -------------------------------
@router.put(
    "/{guest_id}",
    response_model=None,
    summary="Actualizar invitado",
    responses=ResponseDocumentation.get_standard_responses()
)
async def update_guest(
    request: Request,
    guest_id: str,
    guest_data: GuestUpdate
):
    try:
        result = await guest_service.update_guest(guest_id, guest_data)
        return updated_response(
            data=result,  # ✅ devuelve dict con invitado + usuario actualizado
            message="Invitado actualizado exitosamente"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error al actualizar invitado {guest_id}: {str(e)}")
        return bad_request_response(message=str(e))


# -------------------------------
# Desactivar invitado
# -------------------------------
@router.delete(
    "/{guest_id}",
    summary="Desactivar invitado",
    responses=ResponseDocumentation.get_standard_responses()
)
async def deactivate_guest(
    request: Request,
    guest_id: str,
    reason: str = Query("Desactivado por administrador", description="Motivo de la desactivación")
):
    try:
        await guest_service.deactivate_guest(guest_id, reason)
        return message_response(f"Invitado {guest_id} desactivado correctamente")
    except Exception as e:
        logger.error(f"Error al desactivar invitado {guest_id}: {str(e)}")
        return bad_request_response(message=str(e))
