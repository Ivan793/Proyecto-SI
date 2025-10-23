from typing import List, Dict, Any
import logging
from datetime import datetime

from app.repositories.guest_repository import GuestRepository
from app.repositories.user_repository import UserRepository
from app.schemas.guest import (
    GuestCreate,
    GuestCreateExistingUser,
    GuestUpdate,
    GuestResponse
)
from app.exceptions.guest_exceptions import (
    GuestNotFoundException,
    GuestAlreadyExistsException
)
from app.exceptions.user_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException
)
from app.core.firebase import firebase_auth

logger = logging.getLogger(__name__)


class GuestService:
    def __init__(self):
        self.guest_repo = GuestRepository()
        self.user_repo = UserRepository()

    # ---------------------------
    # Crear invitado + usuario (CASCADA)
    # ---------------------------
    async def create_guest_with_user(self, guest_data: GuestCreate) -> GuestResponse:
        try:
            # 🔹 1. Validar que la identificación no exista
            existing_by_id = await self.user_repo.get_by_field("identificacion", guest_data.identificacion)
            if existing_by_id:
                raise UserAlreadyExistsException("identificacion", guest_data.identificacion)

            # 🔹 2. Validar que el correo no exista
            existing_user = await self.user_repo.get_user_by_email(guest_data.correo)
            if existing_user:
                raise UserAlreadyExistsException("correo", guest_data.correo)

            # 🔹 3. Crear usuario en Firebase Authentication
            firebase_user = firebase_auth.create_user(
                email=guest_data.correo,
                password=guest_data.contraseña,
                display_name=f"{guest_data.nombres} {guest_data.apellidos}",
                disabled=False
            )
            user_id = firebase_user.uid
            logger.info(f"Usuario creado en Firebase Auth: {user_id}")

            # 🔹 4. Crear usuario en Firestore (tabla usuarios)
            user_dict = guest_data.model_dump(exclude={"contraseña", "institucion_origen", "motivo_visita", "activo"})
            user_dict["estado"] = "ACTIVO"
            await self.user_repo.create(user_dict, document_id=user_id)
            logger.info(f"Usuario creado en Firestore: {user_id}")

            # 🔹 5. Crear invitado asociado al usuario
            guest_dict = {
                "id_usuario": user_id,
                "institucion_origen": guest_data.institucion_origen,
                "motivo_visita": guest_data.motivo_visita,
                "activo": guest_data.activo if guest_data.activo is not None else True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            guest_id = await self.guest_repo.create(guest_dict)
            logger.info(f"Invitado creado y vinculado: {guest_id} -> {user_id}")

            # 🔹 6. Obtener y retornar invitado completo
            guest = await self.guest_repo.get_by_id(guest_id)
            return GuestResponse(**guest)

        except Exception as e:
            # Rollback: si falla, eliminar el usuario de Firebase si se creó
            if "firebase_user" in locals():
                try:
                    firebase_auth.delete_user(firebase_user.uid)
                    logger.warning(f"Usuario eliminado de Firebase por rollback: {firebase_user.uid}")
                except Exception as rollback_error:
                    logger.error(f"Error en rollback de Firebase: {rollback_error}")

            logger.error(f"Error al crear invitado con usuario: {e}")
            raise ValueError(f"Error al crear invitado: {str(e)}")

    # ---------------------------
    # Crear invitado con usuario existente
    # ---------------------------
    async def create_guest_with_existing_user(self, guest_data: GuestCreateExistingUser) -> GuestResponse:
        # 🔹 Verificar que el usuario exista
        user_exists = await self.user_repo.user_exists(guest_data.id_usuario)
        if not user_exists:
            raise UserNotFoundException(f"Usuario con ID {guest_data.id_usuario} no encontrado.")

        # 🔹 Verificar que no exista invitado asociado
        existing_guest = await self.guest_repo.get_by_field("id_usuario", guest_data.id_usuario)
        if existing_guest:
            raise GuestAlreadyExistsException(f"Ya existe un invitado para el usuario {guest_data.id_usuario}.")

        # 🔹 Crear invitado
        guest_dict = guest_data.model_dump()
        guest_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "activo": guest_dict.get("activo", True)
        })

        new_guest = await self.guest_repo.create(guest_dict)
        if "activo" not in new_guest:
            new_guest["activo"] = guest_dict["activo"]

        return GuestResponse(**new_guest)

    # ---------------------------
    # Obtener todos los invitados (solo activos)
    # ---------------------------
    async def get_all_guests(self, page: int = 1, limit: int = 20):
        filters = {"activo": True}
        guests, total = await self.guest_repo.get_all_paginated(filters, page, limit)

        for g in guests:
            g["activo"] = g.get("activo", True)

        return [GuestResponse(**g) for g in guests], total

    # ---------------------------
    # Obtener invitado por ID
    # ---------------------------
    async def get_guest(self, guest_id: str) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            guest = await self.guest_repo.get_by_field("id_usuario", guest_id)

        if not guest:
            raise GuestNotFoundException(guest_id)

        guest["activo"] = guest.get("activo", True)
        return GuestResponse(**guest)

    # ---------------------------
    # Actualizar invitado
    # ---------------------------
    async def update_guest(self, guest_id: str, guest_data: GuestUpdate) -> GuestResponse:
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            guest = await self.guest_repo.get_by_field("id_usuario", guest_id)

        if not guest:
            raise GuestNotFoundException(guest_id)

        real_id = guest.get("id_invitado") or guest.get("id")

        updated_data = guest_data.model_dump(exclude_unset=True)
        updated_data["updated_at"] = datetime.utcnow()
        updated_data["activo"] = updated_data.get("activo", guest.get("activo", True))

        id_to_update = real_id or guest_id
        updated = await self.guest_repo.update(id_to_update, updated_data)

        if "activo" not in updated:
            updated["activo"] = updated_data["activo"]

        return GuestResponse(**updated)

    # ---------------------------
    # Desactivar invitado
    # ---------------------------
    async def deactivate_guest(self, guest_id: str, reason: str):
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            guest = await self.guest_repo.get_by_field("id_usuario", guest_id)

        if not guest:
            raise GuestNotFoundException(guest_id)

        id_to_update = guest.get("id_invitado") or guest.get("id") or guest_id

        await self.guest_repo.update(
            id_to_update,
            {
                "activo": False,
                "updated_at": datetime.utcnow(),
                "desactivacion_motivo": reason
            }
        )
        return True
