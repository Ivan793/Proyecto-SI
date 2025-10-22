from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.schemas.teacher import (
    TeacherCreateWithUser,
    TeacherCreateWithExistingUser,
    TeacherUpdate,
    TeacherResponse
)
from app.exceptions.teacher_exceptions import (
    TeacherNotFoundException,
    TeacherAlreadyExistsException,
    TeacherHasAssignmentsException
)
from app.exceptions.user_exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException
)
from app.schemas.types import Defaults
from app.core.firebase import firebase_auth

logger = logging.getLogger(__name__)

class TeacherService:
    def __init__(self):
        self.teacher_repo = TeacherRepository()
        self.user_repo = UserRepository()

    # ---------------------------
    # Crear profesor + usuario en cascada
    # ---------------------------
    async def create_teacher_with_user(self, teacher_data: TeacherCreateWithUser) -> TeacherResponse:
        usuario_data = teacher_data.usuario
        
        # 1. Validar que la identificación no exista
        existing_by_id = await self.user_repo.get_by_field("identificacion", usuario_data.identificacion)
        if existing_by_id:
            raise UserAlreadyExistsException("identificacion", usuario_data.identificacion)
        
        # 2. Validar que el correo no exista
        existing_user = await self.user_repo.get_user_by_email(usuario_data.correo)
        if existing_user:
            raise UserAlreadyExistsException("correo", usuario_data.correo)
        
        try:
            # 3. Crear usuario en Firebase Authentication
            firebase_user = firebase_auth.create_user(
                email=usuario_data.correo,
                password=usuario_data.contraseña,
                display_name=f"{usuario_data.nombres} {usuario_data.apellidos}",
                disabled=False
            )
            
            user_id = firebase_user.uid
            logger.info(f"Usuario creado en Firebase Auth: {user_id}")
            
            # 4. Crear usuario en Firestore
            user_dict = usuario_data.model_dump(exclude={"contraseña"})
            user_dict["estado"] = "ACTIVO"
            await self.user_repo.create(user_dict, document_id=user_id)
            logger.info(f"Usuario creado en Firestore: {user_id}")
            
            # 5. Crear profesor asociado al usuario
            teacher_dict = {
                "id_usuario": user_id,
                "categoria_docente": teacher_data.categoria_docente,
                "codigo_programa": teacher_data.codigo_programa,
                "activo": teacher_data.activo
            }
            
            teacher_id = await self.teacher_repo.create(teacher_dict)
            logger.info(f"Profesor creado y vinculado: {teacher_id} -> {user_id}")
            
            # 6. Obtener y retornar el profesor creado
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            return TeacherResponse(**teacher)
            
        except Exception as e:
            # Rollback: si falla, eliminar el usuario de Firebase si se creó
            if 'firebase_user' in locals():
                try:
                    firebase_auth.delete_user(firebase_user.uid)
                    logger.warning(f"Usuario eliminado de Firebase por rollback: {firebase_user.uid}")
                except Exception as rollback_error:
                    logger.error(f"Error en rollback: {rollback_error}")
            
            logger.error(f"Error creando profesor con usuario: {str(e)}")
            raise

    # ---------------------------
    # Crear profesor con usuario existente
    # ---------------------------
    async def create_teacher_with_existing_user(self, teacher_data: TeacherCreateWithExistingUser) -> TeacherResponse:
        # Verificar que el usuario exista
        user_exists = await self.user_repo.user_exists(teacher_data.id_usuario)
        if not user_exists:
            raise UserNotFoundException(f"Usuario con ID {teacher_data.id_usuario} no encontrado.")

        # Verificar que el profesor no exista para ese usuario
        existing_teacher = await self.teacher_repo.get_by_field("id_usuario", teacher_data.id_usuario)
        if existing_teacher:
            raise TeacherAlreadyExistsException(f"El profesor para el usuario {teacher_data.id_usuario} ya existe.")

        # Crear profesor
        teacher_dict = teacher_data.model_dump()
        teacher_dict.update({
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        new_teacher = await self.teacher_repo.create(teacher_dict)
        return TeacherResponse(**new_teacher)

    # ---------------------------
    # Obtener todos los profesores (paginado)
    # ---------------------------
    async def get_all_teachers(self, active_only: bool = True, page: int = 1, limit: int = 20) -> tuple[List[TeacherResponse], int]:
        filters = {"activo": True} if active_only else {}
        teachers, total = await self.teacher_repo.get_all_paginated(filters=filters, page=page, limit=limit)
        return [TeacherResponse(**t) for t in teachers], total

    # ---------------------------
    # Obtener profesor por ID
    # ---------------------------
    async def get_teacher(self, teacher_id: str) -> TeacherResponse:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(f"Profesor con ID {teacher_id} no encontrado.")
        return TeacherResponse(**teacher)

    # ---------------------------
    # Obtener profesor con datos del usuario
    # ---------------------------
    async def get_teacher_with_user(self, teacher_id: str) -> TeacherResponse:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(f"Profesor con ID {teacher_id} no encontrado.")

        user = await self.user_repo.get_by_id(teacher["id_usuario"])
        if not user:
            raise UserNotFoundException(f"Usuario del profesor con ID {teacher['id_usuario']} no encontrado.")

        teacher_with_user = {
            "docente": TeacherResponse(**teacher),
            "usuario": user
        }
        return teacher_with_user

    # ---------------------------
    # Actualizar profesor
    # ---------------------------
    async def update_teacher(self, teacher_id: str, teacher_data: TeacherUpdate) -> TeacherResponse:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(f"Profesor con ID {teacher_id} no encontrado.")

        updated_dict = teacher_data.model_dump(exclude_unset=True)
        updated_dict["updated_at"] = datetime.utcnow()
        updated_teacher = await self.teacher_repo.update(teacher_id, updated_dict)
        return TeacherResponse(**updated_teacher)

    # ---------------------------
    # Desactivar profesor
    # ---------------------------
    async def deactivate_teacher(self, teacher_id: str, reason: str) -> bool:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(f"Profesor con ID {teacher_id} no encontrado.")

        updated_teacher = await self.teacher_repo.update(
            teacher_id,
            {"activo": False, "updated_at": datetime.utcnow(), "desactivacion_motivo": reason}
        )
        return True

    # ---------------------------
    # Activar profesor
    # ---------------------------
    async def activate_teacher(self, teacher_id: str) -> bool:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(f"Profesor con ID {teacher_id} no encontrado.")

        updated_teacher = await self.teacher_repo.update(
            teacher_id,
            {"activo": True, "updated_at": datetime.utcnow()}
        )
        return True
