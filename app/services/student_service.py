# app/services/student_service.py
from typing import List, Optional, Dict, Any
import logging
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError

from app.exceptions.base_exceptions import ValidationException, DatabaseException
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.student import (
    StudentCreateWithUser, 
    StudentUpdate, 
    StudentResponse,
    StudentWithFullUserResponse, 
    StudentWithUserResponse
)
from app.schemas.user import UserCreate,UserBasicInfo, UserResponse
from app.exceptions.student_exceptions import (
    StudentNotFoundException,
    StudentAlreadyExistsException
)
from app.exceptions.user_exceptions import (
    InvalidEmailDomainException, 
    UserNotFoundException, 
    UserAlreadyExistsException
)
from firebase_admin._auth_utils import (
    EmailAlreadyExistsError,
    UserNotFoundError
)
from app.core.validators import validate_user_role_email_match
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
        
        try:
            await self._validate_student_creation_prerequisites(usuario_data)
            
            # Variables para rollback
            firebase_user = None
            user_created = False
            student_created = False
            
            try:
                firebase_user = await self._create_firebase_user(usuario_data)
                user_id = firebase_user.uid
                logger.info(f"Usuario creado en Firebase Auth: {user_id}")
                
                await self._create_firestore_user(usuario_data, user_id)
                user_created = True
                logger.info(f"Usuario creado en Firestore: {user_id}")
                
                student_id = await self._create_student_record(student_data, user_id)
                student_created = True
                logger.info(f"Estudiante creado y vinculado: {student_id} -> {user_id}")
                
                # Enviar email de verificación
                try:
                    email_sent = await self.auth_service.send_email_verification(
                        usuario_data.correo
                    )
                    if email_sent:
                        logger.info(f"Email de verificación enviado a: {usuario_data.correo}")
                    else:
                        logger.warning(f"No se pudo enviar email de verificación a: {usuario_data.correo}")
                except Exception as e:
                    # No detener el proceso si falla el envío de email
                    logger.error(f"Error enviando email de verificación: {str(e)}")
                
                return await self._get_created_student(student_id)
                
            except FirebaseError as e:
                logger.error(f"Error de Firebase al crear usuario: {str(e)}")
                raise DatabaseException(
                    message="Error al crear usuario en el sistema de autenticación",
                    details={"firebase_error": str(e)}
                )
            except Exception as e:
                logger.error(f"Error inesperado durante creación: {str(e)}")
                await self._rollback_student_creation(
                    firebase_user, user_created, student_created
                )
                raise DatabaseException(
                    message="Error durante la creación del estudiante",
                    details={"internal_error": str(e)}
                )
                
        except (ValidationException, UserAlreadyExistsException, InvalidEmailDomainException) as e:
            logger.warning(f"Error de validación/negocio: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en validaciones iniciales: {str(e)}")
            raise DatabaseException("Error interno del sistema")

    async def _validate_student_creation_prerequisites(self, usuario_data: UserCreate) -> None:
        # Validar rol
        if usuario_data.rol != "Estudiante":
            raise ValidationException(
                message="El rol debe ser 'Estudiante' para este endpoint",
                field="rol"
            )
        
        # Validar identificación única
        existing_by_id = await self.user_repo.get_by_field(
            "identificacion", 
            usuario_data.identificacion
        )
        if existing_by_id:
            raise UserAlreadyExistsException(
                field="identificacion", 
                value=usuario_data.identificacion
            )
        
        # Validar correo único
        existing_user = await self.user_repo.get_user_by_email(usuario_data.correo)
        if existing_user:
            raise UserAlreadyExistsException(
                field="correo", 
                value=usuario_data.correo
            )
        
        # Validar correo único en Firebase Auth
        if await self._email_exists_in_firebase_auth(usuario_data.correo):
            raise UserAlreadyExistsException(
                field="correo", 
                value=usuario_data.correo
            )
        
        # Validar dominio de correo
        try:
            validate_user_role_email_match(usuario_data.correo, usuario_data.rol)
        except ValueError as e:
            raise InvalidEmailDomainException(role=usuario_data.rol, custom_message=str(e))
        
    async def _email_exists_in_firebase_auth(self, email: str) -> bool:
        """Verifica si el email ya existe en Firebase Authentication"""
        try:
            firebase_auth.get_user_by_email(email)
            return True  # Si no lanza excepción, el usuario existe
        except firebase_auth.UserNotFoundError:
            return False  # Usuario no encontrado
        except Exception as e:
            logger.warning(f"Error verificando email en Firebase Auth: {str(e)}")
            # En caso de error, asumimos que no existe para permitir que el flujo continúe
            # La creación fallará después si realmente existe
            return False

    async def _create_firebase_user(self, usuario_data: UserCreate) -> Any:
        try:
            return firebase_auth.create_user(
                email=usuario_data.correo,
                password=usuario_data.contraseña,
                display_name=f"{usuario_data.primer_nombre} {usuario_data.segundo_nombre} {usuario_data.primer_apellido} {usuario_data.segundo_apellido}",
                disabled=False
            )
        except EmailAlreadyExistsError:
            # Esta excepción específica de email duplicado
            logger.warning(f"Email ya existe en Firebase Auth: {usuario_data.correo}")
            raise UserAlreadyExistsException(
                field="correo", 
                value=usuario_data.correo
            )
        except FirebaseError as e:
            logger.error(f"Error de Firebase al crear usuario: {str(e)}")
            raise DatabaseException(
                message="Error al crear usuario en el sistema de autenticación",
                details={"firebase_error": str(e)}
            )

    async def _create_firestore_user(self, usuario_data: UserCreate, user_id: str) -> None:
        user_dict = usuario_data.model_dump(exclude={"contraseña"})
        user_dict.update({
            "activo": True,
            "razon_desactivacion": None
        })
        
        await self.user_repo.create(user_dict, document_id=user_id)

    async def _create_student_record(self, student_data: StudentCreateWithUser, user_id: str) -> str:
        """Crea registro de estudiante"""
        student_dict = {
            "id_usuario": user_id,
            "codigo_programa": student_data.codigo_programa,
            "semestre": student_data.semestre,
            "anio_ingreso": student_data.anio_ingreso,
            "periodo": student_data.periodo,
        }
        
        return await self.student_repo.create(student_dict)

    async def _get_created_student(self, student_id: str) -> StudentResponse:
        """Obtiene estudiante creado"""
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)
        return StudentResponse(**student)

    async def _rollback_student_creation(
        self, 
        firebase_user: Any, 
        user_created: bool, 
        student_created: bool
    ) -> None:
        rollback_errors = []
        
        try:
            if student_created:
                logger.info("Rollback: eliminando estudiante creado")
                # await self.student_repo.delete(student_id)  # Si implementas delete
                pass
                
        except Exception as e:
            rollback_errors.append(f"Error eliminando estudiante: {str(e)}")
            logger.error(f"Error durante rollback de estudiante: {str(e)}")
        
        try:
            if user_created and firebase_user:
                await self.user_repo.delete(firebase_user.uid)
                logger.info(f"Rollback: usuario eliminado de Firestore: {firebase_user.uid}")
                
        except Exception as e:
            rollback_errors.append(f"Error eliminando usuario Firestore: {str(e)}")
            logger.error(f"Error durante rollback de usuario Firestore: {str(e)}")
        
        try:
            if firebase_user:
                firebase_auth.delete_user(firebase_user.uid)
                logger.info(f"Rollback: usuario eliminado de Firebase Auth: {firebase_user.uid}")
                
        except FirebaseError as e:
            rollback_errors.append(f"Error eliminando usuario Firebase Auth: {str(e)}")
            logger.error(f"Error durante rollback de Firebase Auth: {str(e)}")
        
        if rollback_errors:
            logger.warning(f"Errores durante rollback: {rollback_errors}")

    async def get_student(self, student_id: str) -> StudentResponse:
        """Obtiene estudiante por ID"""
        try:
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundException(student_id)
            return StudentResponse(**student)
            
        except StudentNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo estudiante {student_id}: {str(e)}")
            raise DatabaseException("Error al obtener estudiante")

    async def get_student_with_user(self, student_id: str) -> StudentWithFullUserResponse:
        try:
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundException(student_id)

            user_id = student.get("id_usuario")
            if not user_id:
                raise ValidationException("Estudiante no tiene usuario asociado")

            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            user_info = UserResponse(**user)

            return StudentWithFullUserResponse(
                estudiante=StudentResponse(**student),
                usuario=user_info
            )
            
        except (StudentNotFoundException, UserNotFoundException, ValidationException) as e:
            logger.warning(f"Error obteniendo estudiante con usuario {student_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado obteniendo estudiante con usuario {student_id}: {str(e)}")
            raise DatabaseException("Error al obtener información completa del estudiante")

    async def get_all_students(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[StudentWithUserResponse], int]:
        try:
            students = await self.student_repo.get_all()
            
            if active_only is not None:
                students = await self._filter_active_students(students, active_only)
            
            # Enriquecer con información del usuario
            enriched_students = await self._enrich_students_with_user_info(students)

            return await self._paginate_enriched_students(enriched_students, page, limit)
            
        except Exception as e:
            logger.error(f"Error obteniendo todos los estudiantes: {str(e)}")
            raise DatabaseException("Error al obtener la lista de estudiantes")
    
    async def _enrich_students_with_user_info(
        self, 
        students: List[dict]
    ) -> List[StudentWithUserResponse]:
        """Enriquece lista de estudiantes con información del usuario asociado"""
        enriched_students = []
        
        for student in students:
            try:
                user_id = student.get("id_usuario")
                if not user_id:
                    logger.warning(f"Estudiante {student.get('id_estudiante')} sin usuario asociado")
                    continue
                
                # Obtener información del usuario
                user = await self.user_repo.get_by_id(user_id)
                if not user:
                    logger.warning(f"Usuario {user_id} no encontrado para estudiante {student.get('id_estudiante')}")
                    continue
                
                # Usar el método de clase para crear UserBasicInfo
                user_info = UserBasicInfo.from_user_data(user)
                
                enriched_students.append(
                    StudentWithUserResponse(
                        estudiante=StudentResponse(**student),
                        usuario=user_info
                    )
                )
                
            except Exception as e:
                logger.warning(
                    f"Error enriqueciendo estudiante {student.get('id_estudiante')}: {str(e)}"
                )
                continue
        
        return enriched_students

    async def _filter_active_students(self, students: List[dict], active_only: bool) -> List[dict]:
        """Filtra estudiantes por estado activo/inactivo"""
        filtered_students = []
        for student in students:
            user_id = student.get("id_usuario")
            if user_id:
                user = await self.user_repo.get_by_id(user_id)
                if user:
                    user_active = user.get("activo", True)
                    if (active_only and user_active) or (not active_only and not user_active):
                        filtered_students.append(student)
        return filtered_students

    async def _paginate_enriched_students(
        self, 
        students: List[StudentWithUserResponse], 
        page: int, 
        limit: int
    ) -> tuple[List[StudentWithUserResponse], int]:
        """Pagina lista de estudiantes enriquecidos"""
        total = len(students)
        start = (page - 1) * limit
        end = start + limit
        paginated_students = students[start:end]
        
        return paginated_students, total

    async def update_student(
        self, 
        student_id: str, 
        student_data: StudentUpdate
    ) -> StudentResponse:
        try:
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundException(student_id)

            update_dict = student_data.model_dump(exclude_none=True)
            if not update_dict:
                raise ValidationException("No se proporcionaron campos para actualizar")

            await self.student_repo.update(student_id, update_dict)

            updated_student = await self.student_repo.get_by_id(student_id)
            if not updated_student:
                raise StudentNotFoundException(student_id)
            
            logger.info(f"Estudiante actualizado: {student_id}")
            return StudentResponse(**updated_student)
            
        except (StudentNotFoundException, ValidationException) as e:
            raise
        except Exception as e:
            logger.error(f"Error actualizando estudiante {student_id}: {str(e)}")
            raise DatabaseException("Error al actualizar estudiante")

    async def deactivate_student(self, student_id: str, reason: str) -> bool:
        try:
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundException(student_id)
            if not reason or len(reason.strip()) < 10:
                raise ValidationException(
                    message="Debe proporcionar una razón de desactivación válida (mínimo 10 caracteres)",
                    field="razon"
                )
            
            user_id = student["id_usuario"]
            success = await self.user_repo.deactivate_user(user_id, reason)
            
            if success:
                logger.info(f"Estudiante desactivado: {student_id}")
            else:
                raise DatabaseException("No se pudo desactivar el estudiante")
                
            return success
            
        except (StudentNotFoundException, ValidationException) as e:
            logger.warning(f"Error desactivando estudiante {student_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado desactivando estudiante {student_id}: {str(e)}")
            raise DatabaseException("Error al desactivar estudiante")

    async def activate_student(self, student_id: str) -> bool:
        try:
            student = await self.student_repo.get_by_id(student_id)
            if not student:
                raise StudentNotFoundException(student_id)

            user_id = student["id_usuario"]
            success = await self.user_repo.activate_user(user_id)
            
            if success:
                logger.info(f"Estudiante activado: {student_id}")
            else:
                raise DatabaseException("No se pudo activar el estudiante")
                
            return success
            
        except StudentNotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error activando estudiante {student_id}: {str(e)}")
            raise DatabaseException("Error al activar estudiante")

    async def get_students_by_program(self, program_code: str) -> List[StudentResponse]:
        try:
            students = await self.student_repo.get_students_by_program(program_code)
            return [StudentResponse(**student) for student in students]
            
        except Exception as e:
            logger.error(f"Error obteniendo estudiantes del programa {program_code}: {str(e)}")
            raise DatabaseException("Error al obtener estudiantes por programa")

    async def student_exists(self, student_id: str) -> bool:
        try:
            student = await self.student_repo.get_by_id(student_id)
            return student is not None
        except Exception as e:
            logger.error(f"Error verificando existencia del estudiante {student_id}: {str(e)}")
            return False

    async def get_student_by_user_id(self, user_id: str) -> Optional[StudentResponse]:
        try:
            student_data = await self.student_repo.get_student_by_user_id(user_id)
            if student_data:
                return StudentResponse(**student_data)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo estudiante por usuario {user_id}: {str(e)}")
            return None