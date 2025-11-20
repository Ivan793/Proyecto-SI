from typing import List, Optional, Dict, Any
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError
from firebase_admin._auth_utils import EmailAlreadyExistsError
from google.cloud.firestore_v1 import transactional

from app.exceptions.base_exceptions import NotFoundException, ValidationException, DatabaseException
from app.repositories.academic_repository import ProgramRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.schemas.teacher import (
    TeacherCreateWithUser,
    TeacherProfileUpdate,
    TeacherUpdate, 
    TeacherResponse,
    TeacherWithFullUserResponse, 
    TeacherWithUserResponse
)
from app.schemas.user import UserCreate, UserBasicInfo, UserResponse
from app.exceptions.teacher_exceptions import (
    TeacherNotFoundException,
    TeacherAlreadyExistsException,
    TeacherHasAssignmentsException
)
from app.exceptions.user_exceptions import (
    InvalidEmailDomainException, 
    UserNotFoundException, 
    UserAlreadyExistsException
)
from app.services.auth_service import AuthService
from app.validators.teacher_validators import TeacherValidators
from app.validators.user_validators import UserValidators

logger = logging.getLogger(__name__)

class TeacherService:
    """
    Servicio de gestión de docentes con inyección de dependencias completa.
    
    IMPORTANTE: Todas las excepciones se propagan al manejador global en main.py.
    
    Args:
        teacher_repo: Repositorio de docentes
        user_repo: Repositorio de usuarios
        program_repo: Repositorio de programas académicos
        auth_service: Servicio de autenticación
        teacher_validators: Validadores de docente
        user_validators: Validadores de usuario
    """
    
    def __init__(
        self,
        teacher_repo: TeacherRepository,
        user_repo: UserRepository,
        program_repo: ProgramRepository,
        auth_service: AuthService,
        teacher_validators: TeacherValidators,
        user_validators: UserValidators
    ):
        self.teacher_repo = teacher_repo
        self.user_repo = user_repo
        self.program_repo = program_repo
        self.auth_service = auth_service
        self.teacher_validators = teacher_validators
        self.user_validators = user_validators
        
        # Thread pool para operaciones bloqueantes (Firebase Auth)
        self._executor = ThreadPoolExecutor(max_workers=5)

    async def create_teacher_with_user(
        self, 
        teacher_data: TeacherCreateWithUser
    ) -> TeacherResponse:
        """
        Crea un docente con su usuario asociado en una transacción atómica.
        
        LAS EXCEPCIONES SE PROPAGAN AL MANEJADOR GLOBAL.
        
        Args:
            teacher_data: Datos completos del docente y usuario
        
        Returns:
            TeacherResponse con los datos del docente creado
        
        Raises:
            ValidationException: Si los datos no cumplen las reglas de validación
            UserAlreadyExistsException: Si el correo o identificación ya existe
            InvalidEmailDomainException: Si el dominio del correo no corresponde al rol
            DatabaseException: Si falla la creación en Firebase o Firestore
        """
        usuario_data = teacher_data.usuario
        firebase_user = None
        
        # VALIDACIONES INICIALES - Las excepciones se propagan
        await self.user_validators.validate_all_user_fields(
            usuario_data, 
            expected_role="Docente"
        )
        await self.teacher_validators.validate_all_teacher_fields(teacher_data)
        
        # CREAR EN FIREBASE AUTH (async-safe)
        firebase_user = await self._create_firebase_user_async(usuario_data)
        user_id = firebase_user.uid
        logger.info(f"Usuario creado en Firebase Auth: {user_id}")
        
        # TRANSACCIÓN FIRESTORE (User + Teacher)
        try:
            teacher_id = await self._create_user_and_teacher_atomic(
                usuario_data=usuario_data,
                user_id=user_id,
                teacher_data=teacher_data
            )
            logger.info(f"Transacción exitosa: User {user_id} + Teacher {teacher_id}")
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
        
        return await self._get_created_teacher(teacher_id)
    
    async def update_teacher(
        self, 
        teacher_id: str, 
        teacher_data: TeacherProfileUpdate
    ) -> TeacherWithFullUserResponse:
        """
        Actualiza el perfil completo del docente (datos docente + usuario).
        
        Operaciones:
            - Valida datos con UserValidators y TeacherValidators
            - Actualiza datos del docente (programa, categoría)
            - Actualiza datos del usuario (nombre, teléfono, etc.)
            - Actualiza contraseña en Firebase Auth (si se proporciona)
            - Todas las actualizaciones de Firestore se ejecutan en transacción atómica
        
        Args:
            teacher_id: ID del docente a actualizar
            teacher_data: Datos parciales del perfil a actualizar
        
        Returns:
            TeacherWithFullUserResponse con los datos actualizados
        
        Raises:
            TeacherNotFoundException: Si el docente no existe
            UserNotFoundException: Si el usuario no existe
            ValidationException: Si los datos de actualización son inválidos
            UserAlreadyExistsException: Si email/identificación ya existen
            InvalidEmailDomainException: Si el dominio no corresponde al rol
            DatabaseException: Si falla la actualización
        """
        # OBTENER Y VALIDAR EXISTENCIA DEL DOCENTE
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        
        user_id = teacher.get("id_usuario")
        if not user_id:
            raise ValidationException("Docente no tiene usuario asociado")
        
        # Obtener usuario actual para comparaciones
        current_user = await self.user_repo.get_by_id(user_id)
        if not current_user:
            raise UserNotFoundException(user_id)
        
        # PREPARAR DATOS DE ACTUALIZACIÓN
        teacher_updates = {}
        user_updates = {}
        password_update = None
        
        # Procesar datos del docente
        if teacher_data.datos_docente:
            teacher_updates = teacher_data.datos_docente.model_dump(
                exclude_none=True, 
                exclude_unset=True
            )

        # Procesar datos del usuario
        if teacher_data.datos_usuario:
            user_updates = teacher_data.datos_usuario.model_dump(
                exclude_none=True,
                exclude_unset=True
            )
            password_update = user_updates.pop("contraseña", None)

        # Verificar que haya al menos un campo para actualizar
        if not teacher_updates and not user_updates and not password_update:
            raise ValidationException("No se proporcionaron campos para actualizar")
        
        # VALIDACIONES (delegar a los Validators)
        if user_updates:
            await self._validate_user_updates(
                user_updates=user_updates,
                current_user=current_user
            )
        
        if teacher_updates:
            await self._validate_teacher_updates(teacher_updates)
        
        # TRANSACCIÓN ATÓMICA: Actualizar Teacher + User en Firestore
        if teacher_updates or user_updates:
            await self._update_teacher_and_user_atomic(
                teacher_id=teacher_id,
                user_id=user_id,
                teacher_updates=teacher_updates,
                user_updates=user_updates
            )

        # ACTUALIZAR CONTRASEÑA (fuera de transacción, Firebase Auth separado)
        if password_update:
            await self._update_firebase_password_async(user_id, password_update)
        
        # RETORNAR DATOS ACTUALIZADOS
        updated_teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not updated_teacher:
            raise TeacherNotFoundException(teacher_id)
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        
        return TeacherWithFullUserResponse(
            docente=TeacherResponse(**updated_teacher),
            usuario=UserResponse(**user)
        )
    
    async def _validate_user_updates(
        self,
        user_updates: dict,
        current_user: dict
    ) -> None:
        """
        Valida actualizaciones de usuario usando UserValidators.
        Solo valida campos que realmente cambiaron.
        """

        
        # VALIDACIÓN: Email único (si cambió)
        new_email = user_updates.get("correo")
        if new_email and new_email != current_user.get("correo"):
            await self.user_validators.validate_unique_email(new_email)
            
            # Validar dominio con el rol actual
            current_role = current_user.get("rol")
            await self.user_validators.validate_email_domain(new_email, current_role)
            
            logger.info(f"Email validado para actualización: {new_email}")
        
        # VALIDACIÓN: Lógica de desactivación
        new_active_status = user_updates.get("activo")
        new_reason = user_updates.get("razon_desactivacion")
        
        if new_active_status is False and not new_reason:
            raise ValidationException(
                message="Debe proporcionar una razón al desactivar el usuario",
                field="razon_desactivacion"
            )
        
        # Limpiar razón si se activa
        if new_active_status is True and "razon_desactivacion" not in user_updates:
            user_updates["razon_desactivacion"] = None
        
        logger.debug("Validaciones de usuario completadas")

    async def _validate_teacher_updates(self, teacher_updates: dict) -> None:
        """
        Valida actualizaciones de docente usando TeacherValidators.
        """
        # VALIDACIÓN: Programa académico existe (si cambió)
        new_program = teacher_updates.get("codigo_programa")
        if new_program:
            await self.teacher_validators.validate_program_existence(new_program)
            logger.info(f"Programa validado: {new_program}")
        
        logger.debug("Validaciones de docente completadas")

    async def _update_teacher_and_user_atomic(
        self,
        teacher_id: str,
        user_id: str,
        teacher_updates: dict,
        user_updates: dict
    ):
        """
        Actualiza Teacher + User en una transacción atómica de Firestore.
        Similar a _create_user_and_teacher_atomic pero para UPDATE.
        """
        @transactional
        def run_transaction(transaction):
            timestamp = datetime.now(timezone.utc)
            
            if teacher_updates:
                teacher_ref = self.teacher_repo.db.collection(
                    self.teacher_repo.collection_name
                ).document(teacher_id)
                teacher_updates["updated_at"] = timestamp
                transaction.update(teacher_ref, teacher_updates)
            
            if user_updates:
                user_ref = self.user_repo.db.collection(
                    self.user_repo.collection_name
                ).document(user_id)
                user_updates["updated_at"] = timestamp
                transaction.update(user_ref, user_updates)
        
        try:
            transaction = self.teacher_repo.db.transaction()
            run_transaction(transaction)
            logger.info(f"Transacción exitosa: Teacher {teacher_id} + User {user_id}")
        except Exception as e:
            logger.error(f"Error en transacción atómica: {str(e)}")
            raise DatabaseException(
                message="Error al actualizar docente y usuario",
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

    async def _create_user_and_teacher_atomic(
        self,
        usuario_data: UserCreate,
        user_id: str,
        teacher_data: TeacherCreateWithUser
    ) -> str:
        """
        Ejecuta la creación de User + Teacher en una transacción Firestore.
        Args:
            usuario_data: Datos del usuario
            user_id: ID generado por Firebase Auth
            teacher_data: Datos del docente
        
        Returns:
            str: ID del docente creado
        """
        @transactional
        def run_transaction(transaction):
            timestamp = datetime.now(timezone.utc)
            
            # Crear documento de usuario
            user_ref = self.user_repo.db.collection(
                self.user_repo.collection_name
            ).document(user_id)
            
            user_dict = usuario_data.model_dump(exclude={"contraseña"})
            user_dict.update({
                "activo": True,
                "razon_desactivacion": None,
                "created_at": timestamp,
                "updated_at": timestamp
            })
            transaction.set(user_ref, user_dict)
            
            # Crear documento de docente
            teacher_ref = self.teacher_repo.db.collection(
                self.teacher_repo.collection_name
            ).document()
            
            teacher_dict = {
                "id_usuario": user_id,
                "categoria_docente": teacher_data.categoria_docente,
                "codigo_programa": teacher_data.codigo_programa,
                "created_at": timestamp,
                "updated_at": timestamp
            }
            transaction.set(teacher_ref, teacher_dict)
            
            return teacher_ref.id
        
        transaction = self.teacher_repo.db.transaction()
        teacher_id = run_transaction(transaction)
        return teacher_id

    async def _compensate_firebase_user(self, firebase_user):
        """
        Elimina el usuario de Firebase Auth en caso de rollback.
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


    async def _get_created_teacher(self, teacher_id: str) -> TeacherResponse:
        """Obtiene docente recién creado."""
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        return TeacherResponse(**teacher)

    

    async def get_teacher(self, teacher_id: str) -> TeacherResponse:
        """
        Obtiene docente por ID. 
        
        """
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        return TeacherResponse(**teacher)

    async def get_teacher_with_user(self, teacher_id: str) -> TeacherWithFullUserResponse:
        """
        Obtiene docente con información completa del usuario.
        
        """
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)

        user_id = teacher.get("id_usuario")
        if not user_id:
            raise ValidationException("Docente no tiene usuario asociado")
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)

        user_info = UserResponse(**user)

        return TeacherWithFullUserResponse(
            docente=TeacherResponse(**teacher),
            usuario=user_info
        )
    
    async def get_all_teachers(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[TeacherWithUserResponse], int]:
        """
        Obtiene lista paginada de docentes con información básica del usuario.
        
        Args:
            active_only: Si True, solo docentes activos
            page: Número de página (1-indexed)
            limit: Cantidad de resultados por página
        
        Returns:
            Tupla (lista_docentes, total)
        """
        teachers = await self.teacher_repo.get_all()
        
        if active_only is not None:
            teachers = await self._filter_active_teachers(teachers, active_only)
        
        # Enriquecer con información del usuario
        enriched_teachers = await self._enrich_teachers_with_user_info(teachers)

        return await self._paginate_enriched_teachers(enriched_teachers, page, limit)
    
    async def _enrich_teachers_with_user_info(
        self, 
        teachers: List[dict]
    ) -> List[TeacherWithUserResponse]:
        """Enriquece lista de docentes con información del usuario asociado"""
        enriched_teachers = []
        
        for teacher in teachers:
            user_id = teacher.get("id_usuario")
            if not user_id:
                logger.warning(f"Docente {teacher.get('id_docente')} sin usuario asociado")
                continue
            
            # Obtener información del usuario
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                logger.warning(f"Usuario no encontrado para docente {teacher.get('id_docente')}: {user_id}")
                continue
            
            # Usar el método de clase para crear UserBasicInfo
            user_info = UserBasicInfo.from_user_data(user)
            
            enriched_teachers.append(
                TeacherWithUserResponse(
                    docente=TeacherResponse(**teacher),
                    usuario=user_info
                )
            )
        
        return enriched_teachers

    async def _filter_active_teachers(self, teachers: List[dict], active_only: bool) -> List[dict]:
        """Filtra docentes por estado activo/inactivo"""
        filtered_teachers = []
        for teacher in teachers:
            user_id = teacher.get("id_usuario")
            if not user_id:
                continue

            user = await self.user_repo.get_by_id(user_id)
            if not user:
                continue
                
            user_active = user.get("activo", True)
            
            if (active_only and user_active) or (not active_only and not user_active):
                filtered_teachers.append(teacher)
        
        return filtered_teachers

    async def _paginate_enriched_teachers(
        self, 
        teachers: List[TeacherWithUserResponse], 
        page: int, 
        limit: int
    ) -> tuple[List[TeacherWithUserResponse], int]:
        """Pagina lista de docentes enriquecidos"""
        total = len(teachers)
        start = (page - 1) * limit
        end = start + limit
        paginated_teachers = teachers[start:end]
        
        return paginated_teachers, total
    
    async def deactivate_teacher(self, teacher_id: str, reason: str) -> bool:
        """
        Desactiva un docente (desactiva su usuario).
        
        """
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        
        if not reason or len(reason.strip()) < 10:
            raise ValidationException(
                message="Debe proporcionar una razón de desactivación válida (mínimo 10 caracteres)",
                field="razon"
            )
        
        # Verificar si el docente tiene grupos activos
        from app.repositories.group_repository import GroupRepository
        group_repo = GroupRepository()
        groups = await group_repo.get_groups_by_teacher(teacher_id)
        active_groups = [group for group in groups if group.get("activo", True)]

        if active_groups:
            raise TeacherHasAssignmentsException(teacher_id)
        
        user_id = teacher["id_usuario"]
        success = await self.user_repo.deactivate_user(user_id, reason)
        
        if not success:
            raise DatabaseException("No se pudo desactivar el docente")
            
        return success

    async def activate_teacher(self, teacher_id: str) -> bool:
        """
        Activa un docente (activa su usuario).
        
        """
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)

        user_id = teacher["id_usuario"]
        success = await self.user_repo.activate_user(user_id)
        
        if not success:
            raise DatabaseException("No se pudo activar el docente")
            
        return success

    async def get_teachers_by_program(self, program_code: str) -> List[TeacherResponse]:
        """
        Obtiene todos los docentes de un programa académico.
        
        """
        teachers = await self.teacher_repo.get_teachers_by_program(program_code)
        return [TeacherResponse(**teacher) for teacher in teachers]

    async def teacher_exists(self, teacher_id: str) -> bool:
        """Verifica si existe un docente."""
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        return teacher is not None

    async def get_teacher_by_user_id(self, user_id: str) -> Optional[TeacherResponse]:
        """Obtiene un docente por su ID de usuario."""
        teacher_data = await self.teacher_repo.get_teacher_by_user_id(user_id)
        if teacher_data:
            return TeacherResponse(**teacher_data)
        return None

    async def get_teacher_workload(self, teacher_id: str) -> Dict[str, Any]:
        """
        Obtiene información sobre la carga de trabajo del docente.
        
        """
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)

        # Obtener grupos del docente
        from app.repositories.group_repository import GroupRepository
        group_repo = GroupRepository()
        groups = await group_repo.get_groups_by_teacher(teacher_id)
        
        # Enriquecer grupos con información básica
        enriched_groups = []
        for group in groups:
            group_code = group.get("codigo_grupo")
            if group_code:
                # Obtener información básica del grupo
                group_details = await group_repo.get_group_with_details(group_code)
                if group_details:
                    enriched_groups.append({
                        "codigo_grupo": group_code,
                        "codigo_materia": group.get("codigo_materia"),
                        "nombre_materia": group_details.get("nombre_materia"),
                        "activo": group.get("activo", True)
                    })
        
        active_groups = [g for g in enriched_groups if g.get("activo", True)]
        
        return {
            "id_docente": teacher_id,
            "total_grupos": len(groups),
            "grupos_activos": len(active_groups),
            "detalle_grupos": active_groups,
            "estado": "ACTIVO" if teacher.get("activo", True) else "INACTIVO"
        }
    

# ------------- Francisco ---------------------
    async def get_teacher_public_info(self, teacher_id: str) -> dict:
            """
            Obtiene información pública del docente (solo datos básicos).
            """
            try:
                teacher = await self.teacher_repo.get_by_id(teacher_id)
                if not teacher:
                    raise TeacherNotFoundException(teacher_id)
                
                user = await self.user_repo.get_by_id(teacher["id_usuario"])
                if not user:
                    raise UserNotFoundException(teacher["id_usuario"])

                # Solo datos públicos
                public_info = {
                    "id_docente": teacher_id,
                    "nombre_completo": f"{user.get('primer_nombre', '')} {user.get('segundo_nombre', '')} "
                                    f"{user.get('primer_apellido', '')} {user.get('segundo_apellido', '')}".strip(),
                    "correo_institucional": user.get("correo"),
                    "categoria_docente": teacher.get("categoria_docente"),
                    "codigo_programa": teacher.get("codigo_programa"),
                }
                return public_info

            except (TeacherNotFoundException, UserNotFoundException):
                raise
            except Exception as e:
                logger.error(f"Error obteniendo información pública del docente {teacher_id}: {str(e)}")
                raise DatabaseException("Error al obtener información pública del docente")

    async def list_teacher_subjects(self, teacher_id: str) -> list:
        """
        Lista las materias que dicta un docente.
        """
        try:
            from app.repositories.teacher_repository import TeacherSubjectRepository
            ts_repo = TeacherSubjectRepository()
            subjects = await ts_repo.get_subjects_by_teacher(teacher_id)
            return subjects
        except Exception as e:
            logger.error(f"Error listando materias del docente {teacher_id}: {str(e)}")
            raise DatabaseException("Error al listar materias del docente")

    async def list_subject_groups(self, subject_code: str) -> list:
        """
        Lista los grupos asociados a una materia específica.
        """
        try:
            from app.repositories.group_repository import GroupRepository
            group_repo = GroupRepository()
            groups = await group_repo.get_groups_by_subject(subject_code)
            return groups
        except Exception as e:
            logger.error(f"Error listando grupos de la materia {subject_code}: {str(e)}")
            raise DatabaseException("Error al listar grupos de la materia")

    async def list_teacher_projects(self, teacher_id: str) -> list:
        """
        Lista los proyectos en los que participa un docente.
        """
        try:
            from app.repositories.teacher_repository import TeacherRepository
            projects = await self.teacher_repo.get_projects_by_teacher(teacher_id)
            return projects
        except Exception as e:
            logger.error(f"Error listando proyectos del docente {teacher_id}: {str(e)}")
            raise DatabaseException("Error al listar proyectos del docente")

    async def get_project_info(self, project_id: str) -> dict:
        """
        Obtiene la información detallada de un proyecto.
        """
        try:
            from app.repositories.proyect_repository import ProjectRepository
            project_repo = ProjectRepository()
            project = await project_repo.get_project_detail(project_id)
            if not project:
                raise ValidationException("Proyecto no encontrado")
            return project
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo detalle del proyecto {project_id}: {str(e)}")
            raise DatabaseException("Error al obtener detalle del proyecto")

    async def list_all_projects(self) -> list:
        """
        Lista todos los proyectos disponibles públicamente.
        """
        try:
            from app.repositories.proyect_repository import ProjectRepository
            project_repo = ProjectRepository()
            projects = await project_repo.get_all_projects()
            return projects
        except Exception as e:
            logger.error(f"Error listando todos los proyectos públicos: {str(e)}")
            raise DatabaseException("Error al listar los proyectos públicos")


    