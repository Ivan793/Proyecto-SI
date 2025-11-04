from typing import List, Dict, Any
import logging
from datetime import datetime
from fastapi import HTTPException

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
                display_name=f"{guest_data.primer_nombre} {guest_data.segundo_nombre} {guest_data.primer_apellido} {guest_data.segundo_apellido}",
                disabled=False
            )
            user_id = firebase_user.uid
            logger.info(f"Usuario creado en Firebase Auth: {user_id}")

            # 🔹 4. Crear usuario en Firestore (tabla usuarios)
            user_dict = guest_data.model_dump(
                exclude={
                    "contraseña",
                    "institucion_origen",
                    "nombre_empresa",
                    "id_sector"
                }
            )
            await self.user_repo.create(user_dict, document_id=user_id)
            logger.info(f"Usuario creado en Firestore: {user_id}")

            # 🔹 5. Crear invitado asociado al usuario
            guest_dict = {
                "id_usuario": user_id,
                "institucion_origen": guest_data.institucion_origen,
                "nombre_empresa": guest_data.nombre_empresa,
                "id_sector": guest_data.id_sector,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            guest_id = await self.guest_repo.create(guest_dict)
            logger.info(f"Invitado creado y vinculado: {guest_id} -> {user_id}")

            # 🔹 6. Enviar email de verificación
            try:
                from app.services.auth_service import AuthService
                auth_service = AuthService()
                email_sent = await auth_service.send_email_verification(guest_data.correo)

                if email_sent:
                    logger.info(f"Email de verificación enviado a: {guest_data.correo}")
                else:
                    logger.warning(f"No se pudo enviar email de verificación a: {guest_data.correo}")
            except Exception as e:
                logger.error(f"Error enviando email de verificación: {str(e)}")

            # 🔹 7. Obtener y retornar invitado completo
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
        user_exists = await self.user_repo.user_exists(guest_data.id_usuario)
        if not user_exists:
            raise UserNotFoundException(f"Usuario con ID {guest_data.id_usuario} no encontrado.")

        existing_guest = await self.guest_repo.get_by_field("id_usuario", guest_data.id_usuario)
        if existing_guest:
            raise GuestAlreadyExistsException(f"Ya existe un invitado para el usuario {guest_data.id_usuario}.")

        guest_dict = guest_data.model_dump()
        guest_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })

        new_guest = await self.guest_repo.create(guest_dict)
        return GuestResponse(**new_guest)

    # ---------------------------
    # Obtener todos los invitados activos (con datos del usuario)
    # ---------------------------
    async def get_all_guests(self, page: int = 1, limit: int = 20):
        """Obtiene los invitados cuyo usuario tenga activo=True e incluye los datos básicos del usuario"""
        try:
            guests, total = await self.guest_repo.get_all_paginated(page=page, limit=limit)
            active_guests = []

            for g in guests:
                user_id = g.get("id_usuario")
                user = await self.user_repo.get_by_id(user_id)
                if user and user.get("activo", False) is True:
                    nombre_completo = f"{user.get('primer_nombre', '')} {user.get('segundo_nombre', '')} {user.get('primer_apellido', '')} {user.get('segundo_apellido', '')}".strip()
                    filtered_user = {
                        "id_usuario": user.get("id_usuario"),
                        "nombre_completo": nombre_completo,
                        "identificacion": user.get("identificacion"),
                        "correo": user.get("correo"),
                        "telefono": user.get("telefono"),
                        "activo": user.get("activo")
                    }
                    active_guests.append({
                        "invitado": g,
                        "usuario": filtered_user
                    })

            return active_guests, len(active_guests)

        except Exception as e:
            logger.error(f"Error al obtener invitados activos: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Error interno al listar invitados activos: {str(e)}",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    # ---------------------------
    # Obtener invitado por ID (con datos del usuario)
    # ---------------------------
    async def get_guest(self, guest_id: str) -> dict:
        """Obtiene un invitado junto con todos los datos del usuario asociado"""
        try:
            guest = await self.guest_repo.get_by_id(guest_id)
            if not guest:
                guest = await self.guest_repo.get_by_field("id_usuario", guest_id)
            if not guest:
                raise GuestNotFoundException(guest_id)

            user_id = guest.get("id_usuario")
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            return {
                "invitado": guest,
                "usuario": user
            }

        except GuestNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el invitado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except UserNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el usuario del invitado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error al obtener invitado {guest_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Error interno al obtener invitado: {str(e)}",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    # ---------------------------
    # ✅ Actualizar invitado + usuario
    # ---------------------------
    async def update_guest(self, guest_id: str, guest_data: GuestUpdate) -> dict:
        """Actualiza todos los campos del invitado y del usuario excepto correo e identificación"""
        try:
            guest = await self.guest_repo.get_by_id(guest_id)
            if not guest:
                guest = await self.guest_repo.get_by_field("id_usuario", guest_id)
            if not guest:
                raise GuestNotFoundException(guest_id)

            user_id = guest.get("id_usuario")
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            input_data = guest_data.model_dump(exclude_unset=True)

            # --- Actualizar invitado ---
            guest_fields_allowed = ["institucion_origen", "nombre_empresa", "id_sector"]
            guest_update_data = {k: v for k, v in input_data.items() if k in guest_fields_allowed}
            if guest_update_data:
                guest_update_data["updated_at"] = datetime.utcnow()
                await self.guest_repo.update(guest_id, guest_update_data)

            # --- Actualizar usuario (excepto correo e identificación) ---
            user_fields_allowed = [
                "primer_nombre", "segundo_nombre", "primer_apellido", "segundo_apellido",
                "sexo", "identidad_sexual", "fecha_nacimiento", "nacionalidad",
                "pais_residencia", "departamento", "municipio", "ciudad_residencia",
                "direccion_residencia", "telefono", "activo"
            ]
            user_update_data = {k: v for k, v in input_data.items() if k in user_fields_allowed}
            if user_update_data:
                user_update_data["updated_at"] = datetime.utcnow()
                await self.user_repo.update(user_id, user_update_data)

            updated_guest = await self.guest_repo.get_by_id(guest_id)
            updated_user = await self.user_repo.get_by_id(user_id)

            nombre_completo = f"{updated_user.get('primer_nombre', '')} {updated_user.get('segundo_nombre', '')} {updated_user.get('primer_apellido', '')} {updated_user.get('segundo_apellido', '')}".strip()

            filtered_user = {
                "id_usuario": updated_user.get("id_usuario"),
                "nombre_completo": nombre_completo,
                "primer_nombre": updated_user.get("primer_nombre"),
                "segundo_nombre": updated_user.get("segundo_nombre"),
                "primer_apellido": updated_user.get("primer_apellido"),
                "segundo_apellido": updated_user.get("segundo_apellido"),
                "identificacion": updated_user.get("identificacion"),  # solo lectura
                "correo": updated_user.get("correo"),                  # solo lectura
                "telefono": updated_user.get("telefono"),
                "activo": updated_user.get("activo")
            }

            logger.info(f"Invitado {guest_id} y usuario {user_id} actualizados correctamente.")
            return {
                "invitado": updated_guest,
                "usuario": filtered_user
            }

        except GuestNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el invitado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except UserNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el usuario del invitado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error al actualizar invitado {guest_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Error interno al actualizar invitado: {str(e)}",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    # ---------------------------
    # Desactivar invitado (actualiza usuario)
    # ---------------------------
    async def deactivate_guest(self, guest_id: str, reason: str):
        guest = await self.guest_repo.get_by_id(guest_id)
        if not guest:
            guest = await self.guest_repo.get_by_field("id_usuario", guest_id)
        if not guest:
            raise GuestNotFoundException(guest_id)

        user_id = guest.get("id_usuario")
        if not user_id:
            raise GuestNotFoundException(f"No se encontró usuario asociado al invitado {guest_id}")

        await self.user_repo.update(
            user_id,
            {
                "activo": False,
                "razon_desactivacion": reason,
                "updated_at": datetime.utcnow()
            }
        )

        logger.info(f"Invitado {guest_id} desactivado y usuario {user_id} inactivado correctamente.")
        return True
