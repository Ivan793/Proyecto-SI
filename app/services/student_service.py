from typing import List, Optional, Dict, Any
import logging
from firebase_admin import auth as firebase_auth

from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.student import (
    StudentCreateWithUser, 
    StudentCreateWithExistingUser,
    StudentUpdate, 
    StudentResponse, 
    StudentWithUserResponse
)
from app.schemas.user import UserCreate
from app.exceptions.student_exceptions import (
    StudentNotFoundException,
    StudentAlreadyExistsException
)
from app.exceptions.user_exceptions import UserNotFoundException, UserAlreadyExistsException
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

class StudentService:
    
    def __init__(self):
        self.student_repo = StudentRepository()
        self.user_repo = UserRepository()
        self.auth_service = AuthService()

    async def create_student_with_user(
        self, 
        student_data: StudentCreateWithUser
    ) -> StudentResponse:
        usuario_data = student_data.usuario

        # Validar que la identificación no exista
        existing_by_id = await self.user_repo.get_by_field(
            "identificacion", 
            usuario_data.identificacion
        )
        if existing_by_id:
            raise UserAlreadyExistsException("identificacion", usuario_data.identificacion)
        
        # Validar que el correo no exista
        existing_user = await self.user_repo.get_user_by_email(usuario_data.correo)
        if existing_user:
            raise UserAlreadyExistsException("correo", usuario_data.correo)
        try:
            # Crear usuario en Firebase Authentication
            firebase_user = firebase_auth.create_user(
                email=usuario_data.correo,
                password=usuario_data.contraseña,
                display_name=f"{usuario_data.nombres} {usuario_data.apellidos}",
                disabled=False
            )
            
            user_id = firebase_user.uid
            logger.info(f"Usuario creado en Firebase Auth: {user_id}")
            
            # Crear usuario en Firestore (forzar rol de Estudiante)
            user_dict = usuario_data.model_dump(exclude={"contraseña"})
            user_dict.update({
                "estado": "ACTIVO",
                "rol": "Estudiante"  # Forzar rol de estudiante en auto-registro
            })
            
            await self.user_repo.create(user_dict, document_id=user_id)
            logger.info(f"Usuario creado en Firestore: {user_id}")
            
            # Crear estudiante asociado al usuario
            student_dict = {
                "id_usuario": user_id,
                "codigo_programa": student_data.codigo_programa,
                "semestre": student_data.semestre,
                "anio_ingreso": student_data.anio_ingreso,
                "activo": True
            }
            
            student_id = await self.student_repo.create(student_dict)
            logger.info(f"Estudiante creado y vinculado: {student_id} -> {user_id}")
            # ENVIAR EMAIL DE VERIFICACIÓN
            try:
                email_sent = await self.auth_service.send_email_verification(
                    usuario_data.correo
                )
                if email_sent:
                    logger.info(f"Email de verificación enviado a: {usuario_data.correo}")
                else:
                    logger.warning(f"No se pudo enviar email de verificación")
            except Exception as e:
                # No detener el proceso si falla el envío
                logger.error(f"Error enviando email de verificación: {str(e)}")
                
            # Obtener y retornar el estudiante creado
            student = await self.student_repo.get_by_id(student_id)
            return StudentResponse(**student)
            
        except Exception as e:
            # Rollback: si falla, eliminar el usuario de Firebase si se creó
            if 'firebase_user' in locals():
                try:
                    firebase_auth.delete_user(firebase_user.uid)
                    logger.warning(f"Usuario eliminado de Firebase por rollback: {firebase_user.uid}")
                except Exception as rollback_error:
                    logger.error(f"Error en rollback: {rollback_error}")
            
            logger.error(f"Error creando estudiante con usuario: {str(e)}")
            raise

    async def create_student_with_existing_user(
        self, 
        student_data: StudentCreateWithExistingUser
    ) -> StudentResponse:
        # Verificar que el usuario existe
        user = await self.user_repo.get_by_id(student_data.id_usuario)
        if not user:
            raise UserNotFoundException(student_data.id_usuario)

        # Verificar que NO sea ya un estudiante
        existing_student = await self.student_repo.get_student_by_user_id(
            student_data.id_usuario
        )
        if existing_student:
            raise StudentAlreadyExistsException(student_data.id_usuario)

        # Crear el estudiante
        student_dict = student_data.model_dump()
        student_id = await self.student_repo.create(student_dict)
        
        student = await self.student_repo.get_by_id(student_id)
        return StudentResponse(**student)

    async def get_student(self, student_id: str) -> StudentResponse:
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)
        return StudentResponse(**student)

    async def get_student_with_user(self, student_id: str) -> StudentWithUserResponse:
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)

        user = await self.user_repo.get_by_id(student["id_usuario"])
        if not user:
            raise UserNotFoundException(student["id_usuario"])

        return StudentWithUserResponse(
            estudiante=StudentResponse(**student),
            usuario=user
        )

    async def get_all_students(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[StudentResponse], int]:
        filters = {"activo": True} if active_only else {}
        students = await self.student_repo.get_all(filters=filters)
        
        total = len(students)
        start = (page - 1) * limit
        end = start + limit
        paginated_students = students[start:end]
        
        return [StudentResponse(**s) for s in paginated_students], total

    async def update_student(
        self, 
        student_id: str, 
        student_data: StudentUpdate
    ) -> StudentResponse:
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)

        update_dict = student_data.model_dump(exclude_none=True)
        if update_dict:
            await self.student_repo.update(student_id, update_dict)

        updated_student = await self.student_repo.get_by_id(student_id)
        return StudentResponse(**updated_student)

    async def deactivate_student(self, student_id: str, reason: str) -> bool:
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)

        return await self.student_repo.update(student_id, {
            "activo": False,
            "razon_desactivacion": reason
        })

    async def activate_student(self, student_id: str) -> bool:
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)

        return await self.student_repo.update(student_id, {"activo": True})

    async def get_students_by_program(self, program_code: str) -> List[StudentResponse]:
        students = await self.student_repo.get_students_by_program(program_code)
        return [StudentResponse(**s) for s in students]

    async def get_students_by_semester(self, semester: int) -> List[StudentResponse]:
        students = await self.student_repo.get_students_by_semester(semester)
        return [StudentResponse(**s) for s in students]

    async def get_student_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.student_repo.get_student_by_user_id(user_id)