from datetime import datetime
import logging
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

    # -------------------------------
    # Crear egresado con usuario (CASCADA)
    # -------------------------------
    async def create_graduate_with_user(self, graduate_data: GraduateCreate) -> GraduateResponse:
        try:
            existing_by_id = await self.user_repo.get_by_field("identificacion", graduate_data.identificacion)
            if existing_by_id:
                logger.warning(f"Identificación duplicada: {graduate_data.identificacion}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message": f"Error al crear egresado: Ya existe un usuario con identificacion: {graduate_data.identificacion}",
                        "code": "VALIDATION_ERROR",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            existing_user = await self.user_repo.get_user_by_email(graduate_data.correo)
            if existing_user:
                logger.warning(f"Correo duplicado: {graduate_data.correo}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "status": "error",
                        "message": f"Error al crear egresado: Ya existe un usuario con correo: {graduate_data.correo}",
                        "code": "VALIDATION_ERROR",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )

            firebase_user = firebase_auth.create_user(
                email=graduate_data.correo,
                password=graduate_data.contraseña,
                display_name=f"{graduate_data.primer_nombre} {graduate_data.segundo_nombre} {graduate_data.primer_apellido} {graduate_data.segundo_apellido}",
                disabled=False
            )
            uid = firebase_user.uid
            logger.info(f"Usuario creado en Firebase Auth: {uid}")

            user_dict = graduate_data.model_dump(exclude={
                "contraseña", "programa_academico", "codigo_programa", "año_graduacion",
                "titulo_obtenido", "titulado"
            })
            user_dict.update({
                "rol": "Egresado",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
            await self.user_repo.create(user_dict, document_id=uid)
            logger.info(f"Usuario creado en Firestore: {uid}")

            graduate_dict = {
                "id_usuario": uid,
                "codigo_programa": graduate_data.codigo_programa,
                "programa_academico": graduate_data.programa_academico,
                "año_graduacion": graduate_data.año_graduacion,
                "titulo_obtenido": graduate_data.titulo_obtenido,
                "titulado": graduate_data.titulado,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }

            graduate_created = await self.graduate_repo.create(graduate_dict)
            graduate_id = (
                graduate_created.get("id_egresado")
                if isinstance(graduate_created, dict)
                else graduate_created
            )

            try:
                from app.services.auth_service import AuthService
                auth_service = AuthService()
                email_sent = await auth_service.send_email_verification(graduate_data.correo)
                if email_sent:
                    logger.info(f"Email de verificación enviado a: {graduate_data.correo}")
                else:
                    logger.warning(f"No se pudo enviar email de verificación a: {graduate_data.correo}")
            except Exception as e:
                logger.error(f"Error enviando email de verificación: {str(e)}")

            graduate = await self.graduate_repo.get_by_id(graduate_id)
            return GraduateResponse(**graduate)

        except HTTPException:
            raise
        except Exception as e:
            if "firebase_user" in locals():
                try:
                    firebase_auth.delete_user(firebase_user.uid)
                    logger.warning(f"Rollback: usuario eliminado de Firebase {firebase_user.uid}")
                except Exception as rollback_error:
                    logger.error(f"Error en rollback Firebase: {rollback_error}")

            logger.error(f"Error inesperado al crear egresado: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Error interno al crear egresado: {str(e)}",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    # -------------------------------
    # Obtener egresados activos (solo campos específicos del usuario)
    # -------------------------------
    async def get_all_graduates(self, page: int = 1, limit: int = 20):
        """Obtiene los egresados cuyo usuario tenga activo=True e incluye solo los campos relevantes del usuario"""
        try:
            graduates, total = await self.graduate_repo.get_all_paginated(page=page, limit=limit)
            active_graduates = []

            for g in graduates:
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
                    active_graduates.append({
                        "egresado": g,
                        "usuario": filtered_user
                    })

            return active_graduates, len(active_graduates)

        except Exception as e:
            logger.error(f"Error al obtener egresados activos: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Error interno al listar egresados activos: {str(e)}",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    # -------------------------------
    # Obtener egresado por ID (con datos del usuario)
    # -------------------------------
    async def get_graduate(self, graduate_id: str) -> dict:
        """Obtiene un egresado junto con todos los datos del usuario asociado"""
        try:
            graduate = await self.graduate_repo.get_by_id(graduate_id)
            if not graduate:
                graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_id)
            if not graduate:
                raise GraduateNotFoundException(graduate_id)

            user_id = graduate.get("id_usuario")
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            return {
                "egresado": graduate,
                "usuario": user
            }

        except GraduateNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el egresado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except UserNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el usuario del egresado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error al obtener egresado {graduate_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Error interno al obtener egresado: {str(e)}",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    # -------------------------------
    # ✅ Actualizar egresado + usuario (solo cambio aquí)
    # -------------------------------
    async def update_graduate(self, graduate_id: str, graduate_data: GraduateUpdate) -> dict:
        """Actualiza todos los campos del egresado y del usuario excepto correo e identificación"""
        try:
            graduate = await self.graduate_repo.get_by_id(graduate_id)
            if not graduate:
                graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_id)
            if not graduate:
                raise GraduateNotFoundException(graduate_id)

            user_id = graduate.get("id_usuario")
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            # Tomar solo los datos que llegaron en el body
            input_data = graduate_data.model_dump(exclude_unset=True)

            # --- Campos permitidos para el egresado (solo estos se actualizan en la colección egresados) ---
            grad_fields_allowed = [
                "codigo_programa", "programa_academico", "año_graduacion",
                "titulo_obtenido", "titulado"
            ]
            grad_update_data = {k: v for k, v in input_data.items() if k in grad_fields_allowed}
            if grad_update_data:
                grad_update_data["updated_at"] = datetime.utcnow()
                await self.graduate_repo.update(graduate_id, grad_update_data)

            # --- Campos permitidos para el usuario (TODOS menos 'correo' e 'identificacion') ---
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

            # Obtener actualizados
            updated_grad = await self.graduate_repo.get_by_id(graduate_id)
            updated_user = await self.user_repo.get_by_id(user_id)

            # Generar nombre completo con los 4 campos
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

            logger.info(f"Egresado {graduate_id} y usuario {user_id} actualizados correctamente.")
            return {
                "egresado": updated_grad,
                "usuario": filtered_user
            }

        except GraduateNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el egresado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except UserNotFoundException as e:
            raise HTTPException(
                status_code=404,
                detail={
                    "status": "error",
                    "message": f"No se encontró el usuario del egresado: {str(e)}",
                    "code": "NOT_FOUND",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error al actualizar egresado {graduate_id}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": f"Error interno al actualizar egresado: {str(e)}",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

    # -------------------------------
    # Desactivar egresado
    # -------------------------------
    async def deactivate_graduate(self, graduate_id: str, reason: str):
        """Desactiva al egresado actualizando el campo activo del usuario"""
        graduate = await self.graduate_repo.get_by_id(graduate_id)
        if not graduate:
            graduate = await self.graduate_repo.get_by_field("id_usuario", graduate_id)
        if not graduate:
            raise GraduateNotFoundException(graduate_id)

        user_id = graduate.get("id_usuario")
        if not user_id:
            raise GraduateNotFoundException(f"No se encontró usuario asociado al egresado {graduate_id}")

        await self.user_repo.update(
            user_id,
            {
                "activo": False,
                "razon_desactivacion": reason,
                "updated_at": datetime.utcnow()
            }
        )

        logger.info(f"Egresado {graduate_id} desactivado y usuario {user_id} inactivado correctamente.")
        return True
