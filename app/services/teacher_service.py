from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.schemas.teacher import TeacherCreateWithUser, TeacherCreateWithExistingUser, TeacherUpdate, TeacherResponse
from app.exceptions.teacher_exceptions import TeacherNotFoundException, TeacherAlreadyExistsException, TeacherHasAssignmentsException
from app.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException
from app.schemas.types import Defaults

logger = logging.getLogger(__name__)

class TeacherService:
    def __init__(self):
        self.teacher_repo = TeacherRepository()
        self.user_repo = UserRepository()

    # ---------------------------
    # Crear profesor + usuario en cascada
    # ---------------------------
    async def create_teacher_with_user(self, teacher_data: TeacherCreateWithUser) -> TeacherResponse:
        # Verificar si el correo del usuario ya existe
        existing_user = await self.user_repo.get_user_by_email(teacher_data.correo)
        if existing_user:
            raise UserAlreadyExistsException(f"El usuario con correo {teacher_data.correo} ya existe.")

        # Crear usuario
        user_dict = teacher_data.model_dump()
        user_dict.pop("categoria_docente", None)
        user_dict.pop("codigo_programa", None)
        new_user = await self.user_repo.create(user_dict)

        # ✅ Asegurarnos que new_user sea un diccionario
        if isinstance(new_user, str):
            import json
            new_user = json.loads(new_user)

        # Crear profesor con id_usuario recién creado
        teacher_dict = {
            "id_usuario": new_user["id_usuario"],
            "categoria_docente": teacher_data.categoria_docente,
            "codigo_programa": teacher_data.codigo_programa,
            "activo": teacher_data.activo,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        new_teacher = await self.teacher_repo.create(teacher_dict)
        return TeacherResponse(**new_teacher)

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

        # Aquí podrías agregar validación de asignaciones activas si existe tu lógica
        updated_teacher = await self.teacher_repo.update(teacher_id, {"activo": False, "updated_at": datetime.utcnow(), "desactivacion_motivo": reason})
        return True

    # ---------------------------
    # Activar profesor
    # ---------------------------
    async def activate_teacher(self, teacher_id: str) -> bool:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(f"Profesor con ID {teacher_id} no encontrado.")

        updated_teacher = await self.teacher_repo.update(teacher_id, {"activo": True, "updated_at": datetime.utcnow()})
        return True
