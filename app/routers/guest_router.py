from fastapi import APIRouter, Body, Depends, Query, status, Request
import logging
from typing import Optional, Dict, Any

from app.schemas.types import ReasonText
from app.services.guest_service import GuestService
from app.schemas.guest import (
    GuestCreateWithExistingUser,
    GuestUpdate,
    GuestResponse
)
from app.schemas.common import PaginationParams
from app.utils.responses import (
    success_response, created_response, paginated_response,
    updated_response, not_found_response, conflict_response,
    bad_request_response, internal_server_error_response
)
from app.exceptions.guest_exceptions import GuestNotFoundException
from app.exceptions.user_exceptions import UserNotFoundException

logger = logging.getLogger(__name__)

# ✅ Agregamos un prefix para el router
router = APIRouter(
    prefix="/guests",
    tags=["Invitados"]
)

@router.post(
    "/",  # path relativo al prefix
    status_code=status.HTTP_201_CREATED,
    summary="Crear invitado con usuario existente",
    description="Crea un invitado asignándolo a un usuario que ya existe."
)
async def create_guest_with_existing_user(
    request: Request,
    guest_data: GuestCreateWithExistingUser
):
    try:
        service = GuestService()
        guest = await service.create_guest_with_existing_user(guest_data)
        logger.info(f"Invitado creado: {guest.id_invitado}")
        return created_response(
            data=guest.model_dump(),
            message="Invitado creado exitosamente"
        )
    except Exception as e:
        logger.error(f"Error creando invitado: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/",  # path relativo al prefix
    status_code=status.HTTP_200_OK,
    summary="Listar todos los invitados"
)
async def get_guests(
    request: Request,
    params: PaginationParams = Depends()
):
    try:
        service = GuestService()
        guests, total = await service.get_all_guests(
            page=params.page,
            limit=params.limit
        )
        return paginated_response(
            data=[g.model_dump() for g in guests],
            page=params.page,
            limit=params.limit,
            total_items=total
        )
    except Exception as e:
        logger.error(f"Error obteniendo invitados: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{guest_id}",
    status_code=status.HTTP_200_OK,
    summary="Obtener invitado por ID"
)
async def get_guest_by_id(
    request: Request,
    guest_id: str
):
    try:
        service = GuestService()
        guest = await service.get_guest(guest_id)
        return success_response(
            data=guest.model_dump(),
            message="Invitado obtenido correctamente"
        )
    except GuestNotFoundException:
        return not_found_response("Invitado", guest_id)
    except Exception as e:
        logger.error(f"Error obteniendo invitado {guest_id}: {str(e)}")
        return internal_server_error_response()


@router.get(
    "/{guest_id}/completo",
    status_code=status.HTTP_200_OK,
    summary="Obtener invitado con información de usuario"
)
async def get_guest_with_user(
    request: Request,
    guest_id: str
):
    try:
        service = GuestService()
        guest_with_user = await service.get_guest_with_user(guest_id)
        return success_response(
            data=guest_with_user.model_dump(),
            message="Invitado con información completa"
        )
    except GuestNotFoundException:
        return not_found_response("Invitado", guest_id)
    except UserNotFoundException:
        return not_found_response("Usuario", "asociado al invitado")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return internal_server_error_response()


@router.put(
    "/{guest_id}",
    status_code=status.HTTP_200_OK,
    summary="Actualizar invitado"
)
async def update_guest(
    request: Request,
    guest_id: str,
    guest_data: GuestUpdate
):
    try:
        service = GuestService()
        guest = await service.update_guest(guest_id, guest_data)
        logger.info(f"Invitado actualizado: {guest_id}")
        return updated_response(
            data=guest.model_dump(),
            message="Invitado actualizado exitosamente"
        )
    except GuestNotFoundException:
        return not_found_response("Invitado", guest_id)
    except Exception as e:
        logger.error(f"Error actualizando invitado {guest_id}: {str(e)}")
        return internal_server_error_response()
