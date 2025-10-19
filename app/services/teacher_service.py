from typing import List, Optional
import logging
from firebase_admin import auth as firebase_auth

from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.schemas.teacher import (
    TeacherCreateWithUser, 
    TeacherCreateWithExistingUser,
    TeacherUpdate, 
    TeacherResponse, 
    TeacherWithUserResponse
)
from app.schemas.user import UserCreate
from app.exceptions.teacher_exceptions import (
    TeacherNotFoundException,
    TeacherAlreadyExistsException,
    TeacherHasAssignmentsException
)
from app.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException

logger = logging.getLogger(__name__)


class TeacherService:
    
    def __init__(self):
        self.teacher_repo = TeacherRepository()
        self.user_repo = UserRepository()

# Crea un profesor CON su usuario en cascada
    async def create_teacher_with_user(
        self, 
        teacher_data: TeacherCreateWithUser
    ) -> TeacherResponse:
        usuario_data = teacher_data.usuario
        
        # 1. Validar que el correo no exista
        existing_user = await self.user_repo.get_user_by_email(usuario_data.correo)
        if existing_user:
            raise UserAlreadyExistsException("correo", usuario_data.correo)
        
        # 2. Validar que la identificación no exista
        existing_by_id = await self.user_repo.get_by_field(
            "identificacion", 
            usuario_data.identificacion
        )
        if existing_by_id:
            raise UserAlreadyExistsException("identificacion", usuario_data.identificacion)
        
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

# Crea un profesor asignándolo a un usuario YA EXISTENTE (en los squemas que me dieron asi era la logica ya que usaban en id_usuario algo asi)
    async def create_teacher_with_existing_user(
        self, 
        teacher_data: TeacherCreateWithExistingUser
    ) -> TeacherResponse:
        # Verificar que el usuario existe
        user = await self.user_repo.get_by_id(teacher_data.id_usuario)
        if not user:
            raise UserNotFoundException(teacher_data.id_usuario)

        # Verificar que NO sea ya un docente
        existing_teacher = await self.teacher_repo.get_teacher_by_user_id(
            teacher_data.id_usuario
        )
        if existing_teacher:
            raise TeacherAlreadyExistsException(teacher_data.id_usuario)

        # Crear el docente
        teacher_dict = teacher_data.model_dump()
        teacher_id = await self.teacher_repo.create(teacher_dict)
        
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        return TeacherResponse(**teacher)

    async def get_teacher(self, teacher_id: str) -> TeacherResponse:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        return TeacherResponse(**teacher)

    async def get_teacher_with_user(self, teacher_id: str) -> TeacherWithUserResponse:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)

        user = await self.user_repo.get_by_id(teacher["id_usuario"])
        if not user:
            raise UserNotFoundException(teacher["id_usuario"])

        return TeacherWithUserResponse(
            docente=TeacherResponse(**teacher),
            usuario=user
        )

    async def get_all_teachers(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[TeacherResponse], int]:
        filters = {"activo": True} if active_only else {}
        teachers = await self.teacher_repo.get_all(filters=filters)
        
        total = len(teachers)
        start = (page - 1) * limit
        end = start + limit
        paginated_teachers = teachers[start:end]
        
        return [TeacherResponse(**t) for t in paginated_teachers], total

    async def update_teacher(
        self, 
        teacher_id: str, 
        teacher_data: TeacherUpdate
    ) -> TeacherResponse:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)

        update_dict = teacher_data.model_dump(exclude_none=True)
        if update_dict:
            await self.teacher_repo.update(teacher_id, update_dict)

        updated_teacher = await self.teacher_repo.get_by_id(teacher_id)
        return TeacherResponse(**updated_teacher)

    async def deactivate_teacher(self, teacher_id: str, reason: str) -> bool:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)

        from app.repositories.teacher_subject_repository import TeacherSubjectRepository
        ts_repo = TeacherSubjectRepository()
        if await ts_repo.teacher_has_assignments(teacher_id):
            raise TeacherHasAssignmentsException(teacher_id)

        return await self.teacher_repo.update(teacher_id, {
            "activo": False,
            "razon_desactivacion": reason
        })

    async def activate_teacher(self, teacher_id: str) -> bool:
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)

        return await self.teacher_repo.update(teacher_id, {"activo": True})