import logging
from datetime import datetime
from fastapi import HTTPException

from app.core.firebase import firebase_auth
from app.repositories.user_repository import UserRepository
from app.repositories.graduate_repository import GraduateRepository
from app.schemas.graduate import (
    GraduateCreate,
    GraduateCreateExistingUser,
    GraduateUpdate,
    GraduateResponse
)
from app.exceptions.user_exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException
)
from app.exceptions.graduate_exceptions import (
    GraduateNotFoundException,
    GraduateAlreadyExistsException
)

logger = logging.getLogger(__name__)


class GraduateService:
    def __init__(self):
        self.user_repo = UserRepository()
        self.graduate_repo = GraduateRepository()

    # ---------------------------
    # Crear egresado + usuario (CASCADA)
    # ---------------------------
    async def create_graduate_with_user(self, graduate_data: GraduateCreate) -> GraduateResponse:
        try:
            # 🔹 1. Validar identificación y correo
            existing_by_id = await self.user_repo.get_by_field("identificacion", graduate_data.identificacion)
            if existing_by_id:
                raise UserAlreadyExistsException("identificacion", graduate_data.identificacion)

            existing_user = await self.user_repo.get_user_by_email(graduate_data.correo)
            if existing_user:
                raise UserAlreadyExistsException("correo", graduate_data.correo)

            # 🔹 2. Crear usuario en Firebase Auth
            firebase_user = firebase_auth.create_user(
                email=graduate_data.correo,
                password=graduate_data.contraseña,  # ✅ corregido (antes: contrasena)
                display_name=f"{graduate_data.nombres} {graduate_data.apellidos}",
                disabled=False
            )
            uid = firebase_user.uid
            logger.info(f"Usuario creado en Firebase Auth: {uid}")

            # 🔹 3. Crear usuario en Firestore
            user_dict = {
                "id_usuario": uid,
                "tipo_documento": graduate_data.tipo_documento,
                "identificacion": graduate_data.identificacion,
                "nombres": graduate_data.nombres,
                "apellidos": graduate_data.apellidos,
                "genero": graduate_data.genero,
                "identidad_sexual": graduate_data.identidad_sexual,
                "fecha_nacimiento": graduate_data.fecha_nacimiento,
                "nacionalidad": graduate_data.nacionalidad,
                "pais_residencia": graduate_data.pais_residencia,
                "departamento": graduate_data.departamento,
                "municipio": graduate_data.municipio,
                "ciudad_residencia": graduate_data.ciudad_residencia,
                "direccion_residencia": graduate_data.direccion_residencia,
                "telefono": graduate_data.telefono,
                "correo": graduate_data.correo,
                "rol": "Egresado",
                "activo": True,
                "estado": "ACTIVO",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            await self.user_repo.create(user_dict, document_id=uid)
            logger.info(f"Usuario creado en Firestore: {uid}")

            # 🔹 4. Crear egresado asociado
            graduate_dict = {
                "id_usuario": uid,
                "programa_academico": graduate_data.programa_academico,
                "año_graduacion": graduate_data.año_graduacion,
                "titulo_obtenido": graduate_data.titulo_obtenido,
                "activo": graduate_data.activo if graduate_data.activo is not None else True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            graduate_created = await self.graduate_repo.create(graduate_dict)

            # ✅ FIX AQUÍ: obtener correctamente el ID real
            graduate_id = (
                graduate_created.get("id_egresado")
                if isinstance(graduate_created, dict)
                else graduate_created
            )

            logger.info(f"Egresado creado y vinculado: {graduate_id} -> {uid}")

            # 🔹 5. Obtener y retornar
            graduate = await self.graduate_repo.get_by_id(graduate_id)
            return GraduateResponse(**graduate)

        except Exception as e:
            # Rollback: si falla, eliminar el usuario en Firebase
            if "firebase_user" in locals():
                try:
                    firebase_auth.delete_user(firebase_user.uid)
                    logger.warning(f"Usuario eliminado de Firebase por rollback: {firebase_user.uid}")
                except Exception as rollback_error:
                    logger.error(f"Error en rollback de Firebase: {rollback_error}")

            logger.error(f"Error al crear egresado con usuario: {e}")
            raise HTTPException(status_code=400, detail=f"Error al crear egresado: {str(e)}")

    # ---------------------------
    # Crear egresado con usuario existente
    # ---------------------------
    async def create_graduate_with_existing_user(self, graduate_data: GraduateCreateExistingUser) -> GraduateResponse:
        user_exists = await self.user_repo.user_exists(graduate_data.id_usuario)
        if not user_exists:
            raise UserNotFoundException(f"Usuario con ID {graduate_data.id_usuario} no encontrado.")

        existing_graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_data.id_usuario)
        if existing_graduate:
            raise GraduateAlreadyExistsException(f"Ya existe un egresado para el usuario {graduate_data.id_usuario}.")

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
    # Obtener todos los egresados activos
    # ---------------------------
    async def get_all_graduates(self, page: int = 1, limit: int = 20):
        filters = {"activo": True}
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
    # Actualizar egresado
    # ---------------------------
    async def update_graduate(self, graduate_id: str, graduate_data: GraduateUpdate) -> GraduateResponse:
        graduate = await self.graduate_repo.get_by_id(graduate_id)
        if not graduate:
            graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_id)

        if not graduate:
            raise GraduateNotFoundException(graduate_id)

        real_id = graduate.get("id_egresado") or graduate.get("id")

        updated_data = graduate_data.model_dump(exclude_unset=True)
        updated_data["updated_at"] = datetime.utcnow()
        updated_data["activo"] = updated_data.get("activo", graduate.get("activo", True))

        
        success = await self.graduate_repo.update(real_id, updated_data)  # ← Devuelve True/False

        if not success:
            raise ValueError("No se pudo actualizar")

        # Obtener el documento ACTUALIZADO
        updated_graduate = await self.graduate_repo.get_by_id(real_id)  # ← Esto devuelve el dict

        return GraduateResponse(**updated_graduate) 

    # ---------------------------
    # Desactivar egresado
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
