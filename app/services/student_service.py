from typing import List, Optional, Dict, Any
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError
from firebase_admin._auth_utils import EmailAlreadyExistsError, UserNotFoundError
from google.cloud.firestore_v1 import transactional, Transaction

from app.exceptions.base_exceptions import TransactionException, ValidationException, DatabaseException
from app.repositories.academic_repository import ProgramRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.student import (
    StudentCreateWithUser,
    StudentProfileUpdate, 
    StudentUpdate, 
    StudentResponse,
    StudentWithFullUserResponse, 
    StudentWithUserResponse
)
from app.schemas.user import UserCreate, UserBasicInfo, UserResponse
from app.exceptions.student_exceptions import (
    StudentNotFoundException,
    StudentAlreadyExistsException
)
from app.exceptions.user_exceptions import (
    InvalidEmailDomainException, 
    UserNotFoundException, 
    UserAlreadyExistsException
)
from google.cloud.exceptions import GoogleCloudError
from app.exceptions.base_exceptions import (
    DatabaseException, 
    ValidationException,
)
from app.services.auth_service import AuthService
from app.validators.student_validators import StudentValidators
from app.validators.user_validators import UserValidators

logger = logging.getLogger(__name__)


class StudentService:
    """
    Servicio de gestión de estudiantes con inyección de dependencias completa.
    
    Características:
        - Transacciones atómicas en Firestore
        - Operaciones async-safe con Firebase Auth
        - Patrón saga para compensación de errores
        - Validaciones robustas de negocio
        - Logging estructurado
    
    Args:
        student_repo: Repositorio de estudiantes
        user_repo: Repositorio de usuarios
        program_repo: Repositorio de programas académicos
        auth_service: Servicio de autenticación
        student_validators: Validadores de estudiante
        user_validators: Validadores de usuario
    """
    
    def __init__(
        self,
        student_repo: StudentRepository,
        user_repo: UserRepository,
        program_repo: ProgramRepository,
        auth_service: AuthService,
        student_validators: StudentValidators,
        user_validators: UserValidators
    ):
        self.student_repo = student_repo
        self.user_repo = user_repo
        self.program_repo = program_repo
        self.auth_service = auth_service
        self.student_validators = student_validators
        self.user_validators = user_validators
        
        # Thread pool para operaciones bloqueantes (Firebase Auth)
        self._executor = ThreadPoolExecutor(max_workers=5)



    async def create_student_with_user(
        self, 
        student_data: StudentCreateWithUser
    ) -> StudentResponse:
        """
        Crea un estudiante con su usuario asociado en una transacción atómica.
        
        Flujo:
            1. Valida datos de usuario y estudiante
            2. Crea usuario en Firebase Auth (async-safe)
            3. Crea usuario y estudiante en Firestore (transacción)
            4. Envía email de verificación (best-effort)
            5. Si falla cualquier paso en Firestore, ejecuta compensación
        
        Args:
            student_data: Datos completos del estudiante y usuario
        
        Returns:
            StudentResponse con los datos del estudiante creado
        
        Raises:
            ValidationException: Si los datos no cumplen las reglas de validación
            UserAlreadyExistsException: Si el correo o identificación ya existe
            InvalidEmailDomainException: Si el dominio del correo no corresponde al rol
            DatabaseException: Si falla la creación en Firebase o Firestore
        
        Examples:
            >>> student = await service.create_student_with_user(student_data)
            >>> print(student.id_estudiante)
        """
        usuario_data = student_data.usuario
        firebase_user = None
        
        # VALIDACIONES INICIALES
        await self.user_validators.validate_all_user_fields(
            usuario_data, 
            expected_role="Estudiante"
        )
        await self.student_validators.validate_all_student_fields(student_data)
        
        # CREAR EN FIREBASE AUTH (async-safe)
        firebase_user = await self._create_firebase_user_async(usuario_data)
        user_id = firebase_user.uid
        logger.info(f"Usuario creado en Firebase Auth: {user_id}")
        
        # TRANSACCIÓN FIRESTORE (User + Student)
        try:
            student_id = await self._create_user_and_student_atomic(
                usuario_data=usuario_data,
                user_id=user_id,
                student_data=student_data
            )
            logger.info(f"Transacción exitosa: User {user_id} + Student {student_id}")
        except Exception:
            # Solo compensación en caso de error - luego propaga la excepción
            await self._compensate_firebase_user(firebase_user)
            raise
        
        # ENVIAR EMAIL DE VERIFICACIÓN (no crítico - no propaga excepciones)
        try:
            email_sent = await self.auth_service.send_email_verification(
                usuario_data.correo
            )
            if email_sent:
                logger.info(f"Email de verificación enviado a: {usuario_data.correo}")
        except Exception as e:
            logger.warning(f"Error enviando email de verificación: {str(e)}")
        
        return await self._get_created_student(student_id)
    

    async def update_student(
        self, 
        student_id: str, 
        student_data: StudentProfileUpdate
    ) -> StudentWithFullUserResponse:
        """
        Actualiza el perfil completo del estudiante (datos estudiante + usuario).
        
        Operaciones:
            - Valida datos con UserValidators y StudentValidators
            - Actualiza datos del estudiante (semestre, programa)
            - Actualiza datos del usuario (nombre, teléfono, etc.)
            - Actualiza contraseña en Firebase Auth (si se proporciona)
            - Todas las actualizaciones de Firestore se ejecutan en transacción atómica
        
        Args:
            student_id: ID del estudiante a actualizar
            student_data: Datos parciales del perfil a actualizar
        
        Returns:
            StudentWithFullUserResponse con los datos actualizados
        
        Raises:
            StudentNotFoundException: Si el estudiante no existe
            UserNotFoundException: Si el usuario no existe
            ValidationException: Si los datos de actualización son inválidos
            UserAlreadyExistsException: Si email/identificación ya existen
            InvalidEmailDomainException: Si el dominio no corresponde al rol
            DatabaseException: Si falla la actualización
        """
        # 1. OBTENER Y VALIDAR EXISTENCIA DEL ESTUDIANTE
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)
        
        user_id = student.get("id_usuario")
        if not user_id:
            raise ValidationException("Estudiante no tiene usuario asociado")
        
        # Obtener usuario actual para comparaciones
        current_user = await self.user_repo.get_by_id(user_id)
        if not current_user:
            raise UserNotFoundException(user_id)
        
        # 2. PREPARAR DATOS DE ACTUALIZACIÓN
        student_updates = {}
        user_updates = {}
        password_update = None
        
        # Procesar datos del estudiante
        if student_data.datos_estudiante:
            student_updates = student_data.datos_estudiante.model_dump(
                exclude_none=True, 
                exclude_unset=True
            )

        # Procesar datos del usuario
        if student_data.datos_usuario:
            user_updates = student_data.datos_usuario.model_dump(
                exclude_none=True,
                exclude_unset=True
            )
            password_update = user_updates.pop("contraseña", None)

        # Verificar que haya al menos un campo para actualizar
        if not student_updates and not user_updates and not password_update:
            raise ValidationException("No se proporcionaron campos para actualizar")
        
        if student_updates:
            await self._validate_student_updates(student_updates)
        
        # 4. TRANSACCIÓN ATÓMICA: Actualizar Student + User en Firestore
        if student_updates or user_updates:
            await self._update_student_and_user_atomic(
                student_id=student_id,
                user_id=user_id,
                student_updates=student_updates,
                user_updates=user_updates
            )

        # 5. ACTUALIZAR CONTRASEÑA (fuera de transacción, Firebase Auth separado)
        if password_update:
            await self._update_firebase_password_async(user_id, password_update)
        
        # 6. RETORNAR DATOS ACTUALIZADOS
        updated_student = await self.student_repo.get_by_id(student_id)
        if not updated_student:
            raise StudentNotFoundException(student_id)
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        
        return StudentWithFullUserResponse(
            estudiante=StudentResponse(**updated_student),
            usuario=UserResponse(**user)
        )
    
    async def _validate_student_updates(self, student_updates: dict) -> None:
        """
        Valida actualizaciones de estudiante usando StudentValidators.
        """
        # VALIDACIÓN: Semestre válido (si cambió)
        new_semester = student_updates.get("semestre")
        if new_semester:
            await self.student_validators.validate_semester_range(new_semester)
            logger.info(f"Semestre validado: {new_semester}")
        
        logger.debug("Validaciones de estudiante completadas")

    async def _update_student_and_user_atomic(
        self,
        student_id: str,
        user_id: str,
        student_updates: dict,
        user_updates: dict
    ):
        """
        Actualiza Student + User en una transacción atómica de Firestore.
        Similar a _create_user_and_student_atomic pero para UPDATE.
        """
        @transactional
        def run_transaction(transaction):
            timestamp = datetime.now(timezone.utc)
            
            if student_updates:
                student_ref = self.student_repo.db.collection(
                    self.student_repo.collection_name
                ).document(student_id)
                student_updates["updated_at"] = timestamp
                transaction.update(student_ref, student_updates)
            
            if user_updates:
                user_ref = self.user_repo.db.collection(
                    self.user_repo.collection_name
                ).document(user_id)
                user_updates["updated_at"] = timestamp
                transaction.update(user_ref, user_updates)
        
        try:
            transaction = self.student_repo.db.transaction()
            run_transaction(transaction)
            logger.info(f"Transacción exitosa: Student {student_id} + User {user_id}")
        except Exception as e:
            logger.error(f"Error en transacción atómica: {str(e)}")
            raise DatabaseException(
                message="Error al actualizar estudiante y usuario",
                details={"error": str(e)}
            )
    async def _update_firebase_password_async(self, user_id: str, new_password: str):
        """
        Actualiza contraseña en Firebase Auth de forma async-safe.
        Igual que en create pero para UPDATE.
        """
        loop = asyncio.get_event_loop()
        
        try:
            await loop.run_in_executor(
                self._executor,
                lambda: firebase_auth.update_user(user_id, password=new_password)
            )
            logger.info(f"Contraseña actualizada en Firebase Auth: {user_id}")
        except FirebaseError as e:
            logger.error(f"Error actualizando contraseña: {str(e)}")
            raise DatabaseException(
                message="Error al actualizar contraseña",
                details={"firebase_error": str(e)}
            )
        
    async def _create_firebase_user_async(self, usuario_data: UserCreate) -> Any:
        """
        Crea usuario en Firebase Auth de forma async-safe.
        Firebase Admin SDK es síncrono, se ejecuta en thread pool.
        
        Args:
            usuario_data: Datos del usuario a crear
        
        Returns:
            UserRecord de Firebase
        
        Raises:
            UserAlreadyExistsException: Si el email ya existe
            DatabaseException: Si falla la creación
        """
        loop = asyncio.get_event_loop()
        
        def create_user():
            return firebase_auth.create_user(
                email=usuario_data.correo,
                password=usuario_data.contraseña,
                display_name=f"{usuario_data.primer_nombre} {usuario_data.segundo_nombre or ''} {usuario_data.primer_apellido} {usuario_data.segundo_apellido or ''}".strip(),
                disabled=False
            )
        
        try:
            firebase_user = await loop.run_in_executor(self._executor, create_user)
            return firebase_user
        except EmailAlreadyExistsError:
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


    async def _create_user_and_student_atomic(
        self,
        usuario_data: UserCreate,
        user_id: str,
        student_data: StudentCreateWithUser
    ) -> str:
        """
        Ejecuta la creación de User + Student en una transacción Firestore.
        
        Args:
            usuario_data: Datos del usuario
            user_id: ID generado por Firebase Auth
            student_data: Datos del estudiante
        
        Returns:
            str: ID del estudiante creado
        
        Raises:
            TransactionException: Si falla la transacción Firestore
            DatabaseException: Si hay error de base de datos
            ValidationException: Si los datos son inválidos
        """
        @transactional
        def run_transaction(transaction: Transaction) -> str:
            try:
                timestamp = datetime.now(timezone.utc)
                
                # Validar datos antes de la transacción
                if not user_id or not usuario_data.correo:
                    raise ValidationException("Datos de usuario inválidos para transacción")
                
                # Crear documento de usuario
                user_ref = self.user_repo.db.collection(
                    self.user_repo.collection_name
                ).document(user_id)
                
                # Verificar que el usuario no existe ya
                existing_user = user_ref.get(transaction=transaction)
                if existing_user.exists:
                    raise TransactionException(
                        message="El usuario ya existe en Firestore",
                        details={"user_id": user_id}
                    )
                
                user_dict = usuario_data.model_dump(exclude={"contraseña"})
                user_dict.update({
                    "activo": True,
                    "razon_desactivacion": None,
                    "created_at": timestamp,
                    "updated_at": timestamp
                })
                transaction.set(user_ref, user_dict)
                
                # Crear documento de estudiante
                student_ref = self.student_repo.db.collection(
                    self.student_repo.collection_name
                ).document()
                
                student_dict = {
                    "id_usuario": user_id,
                    "codigo_programa": student_data.codigo_programa,
                    "semestre": student_data.semestre,
                    "anio_ingreso": student_data.anio_ingreso,
                    "periodo": student_data.periodo,
                    "created_at": timestamp,
                    "updated_at": timestamp
                }
                
                # Validar datos del estudiante
                if not student_dict["codigo_programa"]:
                    raise ValidationException("Código de programa requerido")
                    
                transaction.set(student_ref, student_dict)
                
                return student_ref.id
                
            except ValidationException:
                raise
            except TransactionException:
                raise
            except Exception as e:
                logger.error(f"Error en transacción: {str(e)}")
                raise TransactionException(
                    message="Error durante la transacción de creación",
                    details={"error": str(e)}
                )
        
        try:
            transaction = self.student_repo.db.transaction()
            student_id = run_transaction(transaction)
            logger.info(f"Transacción exitosa: User {user_id} + Student {student_id}")
            return student_id
            
        except ValidationException as e:
            logger.warning(f"Error de validación en transacción: {str(e)}")
            raise
            
        except TransactionException as e:
            logger.error(f"Error de transacción: {str(e)}")
            raise DatabaseException(
                message="Error en transacción de base de datos",
                details=e.details
            )
            
        except GoogleCloudError as e:
            logger.error(f"Error de Google Cloud en transacción: {str(e)}")
            raise DatabaseException(
                message="Error de base de datos durante la creación",
                details={"firestore_error": str(e)}
            )
            
        except Exception as e:
            logger.error(f"Error inesperado en transacción: {str(e)}")
            raise DatabaseException(
                message="Error inesperado durante la creación",
                details={"unexpected_error": str(e)}
            )
    
    async def _compensate_firebase_user(self, firebase_user):
        """
        Elimina el usuario de Firebase Auth en caso de rollback (Saga Pattern).
        
        CRÍTICO: Si esto falla, se generará una inconsistencia entre Firebase Auth y Firestore.
        En producción, esto debería generar una alerta y quedar registrado para limpieza manual.
        
        Args:
            firebase_user: UserRecord de Firebase Auth a eliminar
        """
        if not firebase_user:
            return
        
        loop = asyncio.get_event_loop()
        
        try:
            await loop.run_in_executor(
                self._executor,
                lambda: firebase_auth.delete_user(firebase_user.uid)
            )
            logger.warning(f"COMPENSACIÓN: Usuario {firebase_user.uid} eliminado de Firebase Auth")
        except Exception as e:
            logger.error(f"Error durante compensación: {str(e)}")

    async def _get_created_student(self, student_id: str) -> StudentResponse:
        """
        Obtiene estudiante recién creado.
        
        Args:
            student_id: ID del estudiante
        
        Returns:
            StudentResponse con los datos del estudiante
        
        Raises:
            StudentNotFoundException: Si no se encuentra (no debería pasar)
        """
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)
        return StudentResponse(**student)

    async def get_student(self, student_id: str) -> StudentResponse:
        """
        Obtiene estudiante por ID.
        
        Args:
            student_id: ID del estudiante
        
        Returns:
            StudentResponse con los datos del estudiante
        
        Raises:
            StudentNotFoundException: Si no se encuentra
            DatabaseException: Si falla la consulta
        """
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)
        return StudentResponse(**student)

    async def get_student_with_user(self, student_id: str) -> StudentWithFullUserResponse:
        """
        Obtiene estudiante con información completa del usuario.
        
        Args:
            student_id: ID del estudiante
        
        Returns:
            StudentWithFullUserResponse con estudiante y usuario
        
        Raises:
            StudentNotFoundException: Si el estudiante no existe
            UserNotFoundException: Si el usuario asociado no existe
            ValidationException: Si el estudiante no tiene usuario asociado
            DatabaseException: Si falla la consulta
        """
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

    async def get_all_students(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[StudentWithUserResponse], int]:
        """
        Obtiene lista paginada de estudiantes con información básica del usuario.
        
        Args:
            active_only: Si True, solo estudiantes activos
            page: Número de página (1-indexed)
            limit: Cantidad de resultados por página
        
        Returns:
            Tupla (lista_estudiantes, total)
        
        Raises:
            DatabaseException: Si falla la consulta
        """
        students = await self.student_repo.get_all()
    
        if active_only is not None:
            students = await self._filter_active_students(students, active_only)
        
        # Enriquecer con información del usuario
        enriched_students = await self._enrich_students_with_user_info(students)

        return await self._paginate_enriched_students(enriched_students, page, limit)

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
                    logger.warning(
                        f"Usuario no encontrado para estudiante",
                        extra={
                            "student_id": student.get('id_estudiante'),
                            "user_id": user_id
                        }
                    )
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
                    f"Error enriqueciendo estudiante: {str(e)}",
                    extra={"student_id": student.get('id_estudiante')}
                )
                continue
        
        return enriched_students

    async def _filter_active_students(self, students: List[dict], active_only: bool) -> List[dict]:
        """Filtra estudiantes por estado activo/inactivo"""
        filtered_students = []
        for student in students:
            user_id = student.get("id_usuario")
            if not user_id:
                continue

            try:
                user = await self.user_repo.get_by_id(user_id)
                if not user:
                    continue
                    
                user_active = user.get("activo", True)
                
                if (active_only and user_active) or (not active_only and not user_active):
                    filtered_students.append(student)
            except Exception as e:
                logger.warning(
                    f"Error filtrando estudiante: {str(e)}",
                    extra={"student_id": student.get('id_estudiante')}
                )
                continue
        
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

    async def deactivate_student(self, student_id: str, reason: str) -> bool:
        """
        Desactiva un estudiante (desactiva su usuario).
        
        Args:
            student_id: ID del estudiante
            reason: Razón de la desactivación (mínimo 10 caracteres)
        
        Returns:
            True si se desactivó correctamente
        
        Raises:
            StudentNotFoundException: Si el estudiante no existe
            ValidationException: Si la razón no es válida
            DatabaseException: Si falla la desactivación
        """
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
        
        if not success:
            raise DatabaseException("No se pudo desactivar el estudiante")
            
        return success
    
    async def activate_student(self, student_id: str) -> bool:
        """
        Activa un estudiante (activa su usuario).
        
        Args:
            student_id: ID del estudiante
        
        Returns:
            True si se activó correctamente
        
        Raises:
            StudentNotFoundException: Si el estudiante no existe
            DatabaseException: Si falla la activación
        """
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)

        user_id = student["id_usuario"]
        success = await self.user_repo.activate_user(user_id)
        
        if not success:
            raise DatabaseException("No se pudo activar el estudiante")
            
        return success
    
    async def get_students_by_program(self, program_code: str) -> List[StudentResponse]:
        """
        Obtiene todos los estudiantes de un programa académico.
        
        Args:
            program_code: Código del programa
        
        Returns:
            Lista de StudentResponse
        
        Raises:
            DatabaseException: Si falla la consulta
        """
        students = await self.student_repo.get_students_by_program(program_code)
        return [StudentResponse(**student) for student in students]
    
    async def student_exists(self, student_id: str) -> bool:
        """
        Verifica si existe un estudiante.
        
        Args:
            student_id: ID del estudiante
        
        Returns:
            True si existe, False en caso contrario
        """
        student = await self.student_repo.get_by_id(student_id)
        return student is not None
    
    async def get_student_by_user_id(self, user_id: str) -> Optional[StudentResponse]:
        """
        Obtiene un estudiante por su ID de usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            StudentResponse si existe, None en caso contrario
        """
        student_data = await self.student_repo.get_student_by_user_id(user_id)
        if student_data:
            return StudentResponse(**student_data)
        return None