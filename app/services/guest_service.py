from typing import List, Tuple
import logging
from datetime import datetime, date

from app.repositories.guest_repository import GuestRepository
from app.services.user_service import create_user, get_user
from app.schemas.guest import (
    GuestCreateWithUser,
    GuestCreateWithExistingUser,
    GuestUpdate,
    GuestResponse
)
from app.schemas.user import UserCreate
from app.exceptions.guest_exceptions import (
    GuestNotFoundException,
    GuestAlreadyExistsException,
)
from app.exceptions.user_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
)

logger = logging.getLogger(__name__)

class GuestService:
    def __init__(self):
        self.guest_repo = GuestRepository()

    # ---------------------------
    # Crear invitado + usuario en cascada (con validaciones de user_service)
    # ---------------------------
    async def create_guest_with_user(self, guest_data: GuestCreateWithUser) -> GuestResponse:
        try:
            # ✅ Asegurar que la fecha de nacimiento sea tipo date (no datetime)
            fecha_nacimiento = guest_data.fecha_nacimiento
            if isinstance(fecha_nacimiento, datetime):
                fecha_nacimiento = fecha_nacimiento.date()
            elif isinstance(fecha_nacimiento, str):
                fecha_nacimiento = datetime.fromisoformat(fecha_nacimiento).date()

            # Crear el usuario con validaciones de user_service
            user_data = UserCreate(
                tipo_documento=guest_data.tipo_documento,
                identificacion=guest_data.identificacion,
                nombres=guest_data.nombres,
                apellidos=guest_data.apellidos,
                genero=guest_data.genero,
                identidad_sexual=guest_data.identidad_sexual,
                fecha_nacimiento=fecha_nacimiento,
                nacionalidad=guest_data.nacionalidad,
                pais_residencia=guest_data.pais_residencia,
                departamento=guest_data.departamento,
                municipio=guest_data.municipio,
                direccion_residencia=guest_data.direccion_residencia,
                telefono=guest_data.telefono,
                correo=guest_data.correo,
                contraseña=guest_data.contraseña,
                rol=guest_data.rol,
            )

            # 🔒 Validaciones de dominio, edad, etc. siguen aplicándose aquí
            new_user = await create_user(user_data)

        except UserAlreadyExistsException as e:
            raise e
        except Exception as e:
            logger.error(f"Error creando usuario para invitado: {e}")
            raise ValueError(f"Error al crear usuario: {e}")

        # Obtener el id del usuario recién creado
        user_id = (
            getattr(new_user, "id_usuario", None)
            or (new_user.get("id_usuario") if isinstance(new_user, dict) else None)
        )
        if not user_id:
            raise ValueError("No se pudo obtener el id_usuario del usuario creado.")

        # Crear invitado asociado
        guest_dict = {
            "id_usuario": user_id,
            "institucion_origen": guest_data.institucion_origen,
            "motivo_visita": guest_data.motivo_visita,
            "activo": guest_data.activo,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        new_guest = await self.guest_repo.create(guest_dict)
        return GuestResponse(**new_guest)

    # ---------------------------
    # Crear invitado con usuario existente
    # ---------------------------
    async def create_guest_with_existing_user(self, guest_data: GuestCreateWithExistingUser) -> GuestResponse:
        user = await get_user(guest_data.id_usuario)
        if not user:
            raise UserNotFoundException(f"Usuario con ID {guest_data.id_usuario} no encontrado.")

        existing_guest = await self.guest_repo.get_by_field("id_usuario", guest_data.id_usuario)
        if existing_guest:
            raise GuestAlreadyExistsException(f"El invitado para el usuario {guest_data.id_usuario} ya existe.")

        guest_dict = guest_data.model_dump()
        guest_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })

        new_guest = await self.guest_repo.create(guest_dict)
        return GuestResponse(**new_guest)

    # ---------------------------
    # Obtener todos los invitados
    # ---------------------------
    async def get_all_guests(self, active_only: bool = True, page: int = 1, limit: int = 20):
        filters = {"activo": True} if active_only else {}
        guests, total = await self.guest_repo.get_all_paginated(filters=filters, page=page, limit=limit)
        return [GuestResponse(**g) for g in guests], total

    # ---------------------------
    # Obtener invitado por ID
    # ---------------------------
    async def get_guest(self, guest_id: str) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(f"Invitado con ID {guest_id} no encontrado.")
        return GuestResponse(**guest)

    # ---------------------------
    # Actualizar invitado
    # ---------------------------
    async def update_guest(self, guest_id: str, guest_data: GuestUpdate) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(f"Invitado con ID {guest_id} no encontrado.")

        datos = guest_data.model_dump(exclude_unset=True)
        datos["updated_at"] = datetime.utcnow()

        updated_guest = await self.guest_repo.update(guest_id, datos)
        return GuestResponse(**updated_guest)
