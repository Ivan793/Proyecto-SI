from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.repositories.graduate_repository import GraduateRepository
from app.repositories.user_repository import UserRepository
from app.schemas.graduate import (
    GraduateCreate,
    GraduateCreateExistingUser,
    GraduateUpdate,
    GraduateResponse
)
from app.exceptions.graduate_exceptions import (
    GraduateNotFoundException,
    GraduateAlreadyExistsException
)
from app.exceptions.user_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException
)

logger = logging.getLogger(__name__)


class GraduateService:
    def __init__(self):
        self.graduate_repo = GraduateRepository()
        self.user_repo = UserRepository()

    # ---------------------------
    # Crear egresado + usuario en cascada
    # ---------------------------
    async def create_graduate_with_user(self, graduate_data: GraduateCreate) -> GraduateResponse:
        try:
            existing_user = await self.user_repo.get_user_by_email(graduate_data.correo)
            if existing_user:
                raise UserAlreadyExistsException(f"El usuario con correo {graduate_data.correo} ya existe.")

            payload = graduate_data.model_dump()

            # preparación usuario (quitamos campos de egresado)
            user_dict = dict(payload)
            user_dict.pop("programa_academico", None)
            user_dict.pop("año_graduacion", None)
            user_dict.pop("titulo_obtenido", None)
            user_dict.pop("activo", None)

            new_user = await self.user_repo.create(user_dict)
            if isinstance(new_user, str):
                import json
                new_user = json.loads(new_user)

            graduate_dict = {
                "id_usuario": new_user["id_usuario"],
                "programa_academico": payload.get("programa_academico"),
                "año_graduacion": payload.get("año_graduacion"),
                "titulo_obtenido": payload.get("titulo_obtenido"),
                "activo": payload.get("activo", True),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            new_graduate = await self.graduate_repo.create(graduate_dict)
            if "activo" not in new_graduate:
                new_graduate["activo"] = graduate_dict["activo"]

            return GraduateResponse(**new_graduate)

        except UserAlreadyExistsException:
            raise
        except Exception as e:
            logger.error(f"Error al crear egresado con usuario: {e}")
            raise ValueError(f"Error al crear egresado: {str(e)}")

    # ---------------------------
    # Crear egresado con usuario existente
    # ---------------------------
    async def create_graduate_with_existing_user(self, graduate_data: GraduateCreateExistingUser) -> GraduateResponse:
        if not await self.user_repo.user_exists(graduate_data.id_usuario):
            raise UserNotFoundException(f"Usuario con ID {graduate_data.id_usuario} no encontrado.")

        existing_graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_data.id_usuario)
        if existing_graduate:
            raise GraduateAlreadyExistsException(graduate_data.id_usuario)

        graduate_dict = graduate_data.model_dump()
        graduate_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "activo": graduate_dict.get("activo", True)
        })

        new_graduate = await self.graduate_repo.create(graduate_dict)
        if "activo" not in new_graduate:
            new_graduate["activo"] = graduate_dict["activo"]

        return GraduateResponse(**new_graduate)

    # ---------------------------
    # Obtener todos los egresados (solo activos)
    # ---------------------------
    async def get_all_graduates(self, page: int = 1, limit: int = 20):
        filters = {"activo": True}  # ✅ Solo activos
        graduates, total = await self.graduate_repo.get_all_paginated(filters, page, limit)

        for g in graduates:
            g["activo"] = g.get("activo", True)

        return [GraduateResponse(**g) for g in graduates], total

    # ---------------------------
    # Obtener egresado por ID
    # ---------------------------
    async def get_graduate(self, graduate_id: str) -> GraduateResponse:
        graduate = await self.graduate_repo.get_by_id(graduate_id)
        if not graduate:
            graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_id)

        if not graduate:
            raise GraduateNotFoundException(graduate_id)

        graduate["activo"] = graduate.get("activo", True)
        return GraduateResponse(**graduate)

    # ---------------------------
    # Actualizar egresado (restricciones en campos)
    # ---------------------------
    async def update_graduate(self, graduate_id: str, graduate_data: GraduateUpdate) -> GraduateResponse:
        graduate = await self.graduate_repo.get_by_id(graduate_id)
        if not graduate:
            graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_id)

        if not graduate:
            raise GraduateNotFoundException(graduate_id)

        real_id = graduate.get("id_egresado") or graduate.get("id")

        updated_data = graduate_data.model_dump(exclude_unset=True)

        # 🚫 No permitir modificar ciertos campos
        campos_restringidos = ["correo", "programa_academico", "identificacion"]
        for campo in campos_restringidos:
            if campo in updated_data:
                updated_data.pop(campo, None)

        updated_data["updated_at"] = datetime.utcnow()
        updated_data["activo"] = updated_data.get("activo", graduate.get("activo", True))

        id_to_update = real_id or graduate_id
        updated = await self.graduate_repo.update(id_to_update, updated_data)

        if "activo" not in updated:
            updated["activo"] = updated_data["activo"]

        return GraduateResponse(**updated)

    # ---------------------------
    # Desactivar egresado (eliminación lógica)
    # ---------------------------
    async def deactivate_graduate(self, graduate_id: str, reason: str):
        graduate = await self.graduate_repo.get_by_id(graduate_id)
        if not graduate:
            graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_id)

        if not graduate:
            raise GraduateNotFoundException(graduate_id)

        id_to_update = graduate.get("id_egresado") or graduate.get("id") or graduate_id

        await self.graduate_repo.update(
            id_to_update,
            {
                "activo": False,
                "updated_at": datetime.utcnow(),
                "desactivacion_motivo": reason
            }
        )
        return True
