from typing import List, Tuple
import logging
import json
from datetime import datetime

# ✅ Repositorios
from app.repositories.guest_repository import GuestRepository
from app.repositories.user_repository import UserRepository

# ✅ Esquemas
from app.schemas.guest import (
    GuestCreateWithUser,
    GuestCreateWithExistingUser,
    GuestUpdate,
    GuestResponse
)

# ✅ Excepciones
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
        self.user_repo = UserRepository()

    # ---------------------------
    # Crear invitado + usuario en cascada
    # ---------------------------
    async def create_guest_with_user(self, guest_data: GuestCreateWithUser) -> GuestResponse:
        # Verificar si ya existe un usuario con ese correo
        existing_user = await self.user_repo.get_user_by_email(guest_data.correo)
        if existing_user:
            raise UserAlreadyExistsException(
                f"El usuario con correo {guest_data.correo} ya existe."
            )

        # Crear usuario
        user_dict = guest_data.model_dump()
        user_dict.pop("institucion_origen", None)
        user_dict.pop("motivo_visita", None)
        user_dict.pop("activo", None)

        new_user = await self.user_repo.create(user_dict)

        if isinstance(new_user, str):
            new_user = json.loads(new_user)

        # Crear invitado asociado
        guest_dict = {
            "id_usuario": new_user["id_usuario"],
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
    async def create_guest_with_existing_user(
        self, guest_data: GuestCreateWithExistingUser
    ) -> GuestResponse:
        user_exists = await self.user_repo.user_exists(guest_data.id_usuario)
        if not user_exists:
            raise UserNotFoundException(
                f"Usuario con ID {guest_data.id_usuario} no encontrado."
            )

        existing_guest = await self.guest_repo.get_by_field(
            "id_usuario", guest_data.id_usuario
        )
        if existing_guest:
            raise GuestAlreadyExistsException(
                f"El invitado para el usuario {guest_data.id_usuario} ya existe."
            )

        guest_dict = guest_data.model_dump()
        guest_dict.update(
            {
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        )
        new_guest = await self.guest_repo.create(guest_dict)
        return GuestResponse(**new_guest)

    # ---------------------------
    # Obtener todos los invitados
    # ---------------------------
    async def get_all_guests(
        self, active_only: bool = True, page: int = 1, limit: int = 20
    ) -> Tuple[List[GuestResponse], int]:
        filters = {"activo": True} if active_only else {}
        guests, total = await self.guest_repo.get_all_paginated(
            filters=filters, page=page, limit=limit
        )
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
    # Obtener invitado con datos del usuario
    # ---------------------------
    async def get_guest_with_user(self, guest_id: str):
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(f"Invitado con ID {guest_id} no encontrado.")

        user = await self.user_repo.get_by_id(guest["id_usuario"])
        if not user:
            raise UserNotFoundException(
                f"Usuario del invitado con ID {guest['id_usuario']} no encontrado."
            )

        return {
            "invitado": GuestResponse(**guest),
            "usuario": user,
        }

    # ---------------------------
    # Actualizar invitado (restringir campos)
    # ---------------------------
    async def update_guest(self, guest_id: str, guest_data: GuestUpdate) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(f"Invitado con ID {guest_id} no encontrado.")

        campos_bloqueados = {"correo", "programa", "identificacion"}
        datos = guest_data.model_dump(exclude_unset=True)

        for campo in list(datos.keys()):
            if campo in campos_bloqueados:
                datos.pop(campo)

        datos["updated_at"] = datetime.utcnow()
        updated_guest = await self.guest_repo.update(guest_id, datos)
        return GuestResponse(**updated_guest)

    # ---------------------------
    # Desactivar invitado
    # ---------------------------
    async def deactivate_guest(self, guest_id: str, reason: str) -> bool:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(f"Invitado con ID {guest_id} no encontrado.")

        await self.guest_repo.update(
            guest_id,
            {"activo": False, "updated_at": datetime.utcnow(), "desactivacion_motivo": reason},
        )
        return True

    # ---------------------------
    # Activar invitado
    # ---------------------------
    async def activate_guest(self, guest_id: str) -> bool:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            raise GuestNotFoundException(f"Invitado con ID {guest_id} no encontrado.")

        await self.guest_repo.update(
            guest_id, {"activo": True, "updated_at": datetime.utcnow()}
        )
        return True
