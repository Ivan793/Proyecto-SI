# app/services/teacher_service.py
from typing import List, Optional, Dict, Any
import logging
from firebase_admin import auth as firebase_auth
from firebase_admin.exceptions import FirebaseError

from app.exceptions.base_exceptions import ValidationException, DatabaseException
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.user_repository import UserRepository
from app.schemas.teacher import (
    TeacherCreateWithUser, 
    TeacherUpdate, 
    TeacherResponse,
    TeacherWithFullUserResponse, 
    TeacherWithUserResponse
)
from app.schemas.user import UserCreate, UserResponse
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
from firebase_admin._auth_utils import (
    EmailAlreadyExistsError,
    UserNotFoundError
)
from app.core.validators import validate_user_role_email_match
from app.services.auth_service import AuthService
from app.schemas.teacher import UserBasicInfo

logger = logging.getLogger(__name__)


class TeacherService:
    
    def __init__(self):
        self.teacher_repo = TeacherRepository()
        self.user_repo = UserRepository()
        self.auth_service = AuthService()

    async def create_teacher_with_user(
        self, 
        teacher_data: TeacherCreateWithUser
    ) -> TeacherResponse:
        usuario_data = teacher_data.usuario
        
        try:
            await self._validate_teacher_creation_prerequisites(usuario_data)
            
            
            # Variables para rollback
            firebase_user = None
            user_created = False
            teacher_created = False
            
            try:
                firebase_user = await self._create_firebase_user(usuario_data)
                user_id = firebase_user.uid
                logger.info(f"Usuario creado en Firebase Auth: {user_id}")
                
                await self._create_firestore_user(usuario_data, user_id)
                user_created = True
                logger.info(f"Usuario creado en Firestore: {user_id}")
                
                teacher_id = await self._create_teacher_record(teacher_data, user_id)
                teacher_created = True
                logger.info(f"Docente creado y vinculado: {teacher_id} -> {user_id}")
                # enviar email de verificacion
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
                
                return await self._get_created_teacher(teacher_id)
                
            except FirebaseError as e:
                logger.error(f"Error de Firebase al crear usuario: {str(e)}")
                raise DatabaseException(
                    message="Error al crear usuario en el sistema de autenticación",
                    details={"firebase_error": str(e)}
                )
            except Exception as e:
                logger.error(f"Error inesperado durante creación: {str(e)}")
                await self._rollback_teacher_creation(
                    firebase_user, user_created, teacher_created
                )
                raise DatabaseException(
                    message="Error durante la creación del docente",
                    details={"internal_error": str(e)}
                )
                
        except (ValidationException, UserAlreadyExistsException, InvalidEmailDomainException) as e:
            logger.warning(f"Error de validación/negocio: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado en validaciones iniciales: {str(e)}")
            raise DatabaseException("Error interno del sistema")

    async def _validate_teacher_creation_prerequisites(self, usuario_data: UserCreate) -> None:
        # Validar rol
        if usuario_data.rol != "Docente":
            raise ValidationException(
                message="El rol debe ser 'Docente' para este endpoint",
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

    async def _create_teacher_record(self, teacher_data: TeacherCreateWithUser, user_id: str) -> str:
        """Crea registro de docente - VERSIÓN MEJORADA"""
        teacher_dict = {
            "id_usuario": user_id,
            "categoria_docente": teacher_data.categoria_docente,
            "codigo_programa": teacher_data.codigo_programa
        }
        
        return await self.teacher_repo.create(teacher_dict)

    async def _get_created_teacher(self, teacher_id: str) -> TeacherResponse:
        """Obtiene docente creado - VERSIÓN MEJORADA"""
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        return TeacherResponse(**teacher)

    async def _rollback_teacher_creation(
        self, 
        firebase_user: Any, 
        user_created: bool, 
        teacher_created: bool
    ) -> None:
        rollback_errors = []
        
        try:
            if teacher_created:
                logger.info("Rollback: eliminando docente creado")
                # await self.teacher_repo.delete(teacher_id)  # Si implementas delete
                pass
                
        except Exception as e:
            rollback_errors.append(f"Error eliminando docente: {str(e)}")
            logger.error(f"Error durante rollback de docente: {str(e)}")
        
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


    async def get_teacher(self, teacher_id: str) -> TeacherResponse:
        """Obtiene docente por ID - VERSIÓN MEJORADA"""
        try:
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise TeacherNotFoundException(teacher_id)
            return TeacherResponse(**teacher)
            
        except TeacherNotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo docente {teacher_id}: {str(e)}")
            raise DatabaseException("Error al obtener docente")

    async def get_teacher_with_user(self, teacher_id: str) -> TeacherWithFullUserResponse:
        try:
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
            
        except (TeacherNotFoundException, UserNotFoundException, ValidationException) as e:
            logger.warning(f"Error obteniendo docente con usuario {teacher_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado obteniendo docente con usuario {teacher_id}: {str(e)}")
            raise DatabaseException("Error al obtener información completa del docente")

    async def get_all_teachers(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[TeacherWithUserResponse], int]:
        try:
            teachers = await self.teacher_repo.get_all()
            
            if active_only is not None:
                teachers = await self._filter_active_teachers(teachers, active_only)
            
            # Enriquecer con información del usuario
            enriched_teachers = await self._enrich_teachers_with_user_info(teachers)

            return await self._paginate_enriched_teachers(enriched_teachers, page, limit)
            
        except Exception as e:
            logger.error(f"Error obteniendo todos los docentes: {str(e)}")
            raise DatabaseException("Error al obtener la lista de docentes")
    
    async def _enrich_teachers_with_user_info(
        self, 
        teachers: List[dict]
    ) -> List[TeacherWithUserResponse]:
        """Enriquece lista de docentes con información del usuario asociado"""
        enriched_teachers = []
        
        for teacher in teachers:
            try:
                user_id = teacher.get("id_usuario")
                if not user_id:
                    logger.warning(f"Docente {teacher.get('id_docente')} sin usuario asociado")
                    continue
                
                # Obtener información del usuario
                user = await self.user_repo.get_by_id(user_id)
                if not user:
                    logger.warning(f"Usuario {user_id} no encontrado para docente {teacher.get('id_docente')}")
                    continue
                
                # Usar el método de clase para crear UserBasicInfo
                user_info = UserBasicInfo.from_user_data(user)
                
                enriched_teachers.append(
                    TeacherWithUserResponse(
                        docente=TeacherResponse(**teacher),
                        usuario=user_info
                    )
                )
                
            except Exception as e:
                logger.warning(
                    f"Error enriqueciendo docente {teacher.get('id_docente')}: {str(e)}"
                )
                continue
        
        return enriched_teachers

    async def _filter_active_teachers(self, teachers: List[dict], active_only: bool) -> List[dict]:
        """Filtra docentes activos - VERSIÓN MEJORADA"""
        filtered_teachers = []
        for teacher in teachers:
            user_id = teacher.get("id_usuario")
            if user_id:
                user = await self.user_repo.get_by_id(user_id)
                if user:
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

    async def update_teacher(
        self, 
        teacher_id: str, 
        teacher_data: TeacherUpdate
    ) -> TeacherResponse:
        try:
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise TeacherNotFoundException(teacher_id)

            update_dict = teacher_data.model_dump(exclude_none=True)
            if not update_dict:
                raise ValidationException("No se proporcionaron campos para actualizar")

            await self.teacher_repo.update(teacher_id, update_dict)

            updated_teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not updated_teacher:
                raise TeacherNotFoundException(teacher_id)
            
            logger.info(f"Docente actualizado: {teacher_id}")
            return TeacherResponse(**updated_teacher)
            
        except (TeacherNotFoundException, ValidationException) as e:
            raise
        except Exception as e:
            logger.error(f"Error actualizando docente {teacher_id}: {str(e)}")
            raise DatabaseException("Error al actualizar docente")

    async def deactivate_teacher(self, teacher_id: str, reason: str) -> bool:
        try:
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise TeacherNotFoundException(teacher_id)
            if not reason or len(reason.strip()) < 10:
                raise ValidationException(
                    message="Debe proporcionar una razón de desactivación válida (mínimo 10 caracteres)",
                    field="razon"
                )
            
            # Verificar si el docente tiene grupos activos usando GroupRepository
            from app.repositories.group_repository import GroupRepository
            group_repo = GroupRepository()
            groups = await group_repo.get_groups_by_teacher(teacher_id)

            # Filtrar grupos activos
            active_groups = [group for group in groups if group.get("activo", True)]

            if active_groups:
                raise TeacherHasAssignmentsException(teacher_id)
            
            user_id = teacher["id_usuario"]
            success = await self.user_repo.deactivate_user(user_id, reason)
            
            if success:
                logger.info(f"Docente desactivado: {teacher_id}")
            else:
                raise DatabaseException("No se pudo desactivar el docente")
                
            return success
            
        except (TeacherNotFoundException, ValidationException, TeacherHasAssignmentsException) as e:
            logger.warning(f"Error desactivando docente {teacher_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado desactivando docente {teacher_id}: {str(e)}")
            raise DatabaseException("Error al desactivar docente")

    async def activate_teacher(self, teacher_id: str) -> bool:
        try:
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise TeacherNotFoundException(teacher_id)

            user_id = teacher["id_usuario"]
            success = await self.user_repo.activate_user(user_id)
            
            if success:
                logger.info(f"Docente activado: {teacher_id}")
            else:
                raise DatabaseException("No se pudo activar el docente")
                
            return success
            
        except TeacherNotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error activando docente {teacher_id}: {str(e)}")
            raise DatabaseException("Error al activar docente")

    async def get_teachers_by_program(self, program_code: str) -> List[TeacherResponse]:
        try:
            teachers = await self.teacher_repo.get_teachers_by_program(program_code)
            return [TeacherResponse(**teacher) for teacher in teachers]
            
        except Exception as e:
            logger.error(f"Error obteniendo docentes del programa {program_code}: {str(e)}")
            raise DatabaseException("Error al obtener docentes por programa")

    async def get_teacher_workload(self, teacher_id: str) -> Dict[str, Any]:
        try:
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
        
        except TeacherNotFoundException as e:
            raise
        except Exception as e:
            logger.error(f"Error obteniendo carga de trabajo del docente {teacher_id}: {str(e)}")
            raise DatabaseException("Error al obtener la carga de trabajo del docente")

    async def teacher_exists(self, teacher_id: str) -> bool:
        try:
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            return teacher is not None
        except Exception as e:
            logger.error(f"Error verificando existencia del docente {teacher_id}: {str(e)}")
            return False

    async def get_teacher_by_user_id(self, user_id: str) -> Optional[TeacherResponse]:
        try:
            teacher_data = await self.teacher_repo.get_teacher_by_user_id(user_id)
            if teacher_data:
                return TeacherResponse(**teacher_data)
            return None
        except Exception as e:
            logger.error(f"Error obteniendo docente por usuario {user_id}: {str(e)}")
            return None
        




    
    #MÉTODOS PÚBLICOS (acceso sin autenticación de administrador)


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


    async def get_teacher_with_user(self, teacher_id: str) -> TeacherWithFullUserResponse:
        try:
            teacher = await self.teacher_repo.get_by_id(teacher_id)
            if not teacher:
                raise TeacherNotFoundException(teacher_id)

            user_id = teacher.get("id_usuario")
            if not user_id:
                raise ValidationException("Docente no tiene usuario asociado")

            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            teacher_info = TeacherResponse(**teacher)

            return TeacherWithFullUserResponse(
                docente=TeacherResponse(**teacher),
                usuario=teacher_info
            )

        except (TeacherNotFoundException, UserNotFoundException, ValidationException) as e:
            logger.warning(f"Error obteniendo docente con usuario {teacher_id}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error inesperado obteniendo docente con usuario {teacher_id}: {str(e)}")
            raise DatabaseException("Error al obtener información completa del docente")
