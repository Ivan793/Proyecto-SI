from typing import List, Optional, Dict, Any
import logging

from app.repositories.subject_repository import SubjectRepository
from app.repositories.group_repository import GroupRepository
from app.repositories.teacher_subject_repository import TeacherSubjectRepository
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse, SubjectSummary
from app.schemas.group import GroupCreate
from app.schemas.teacherSubject import TeacherSubjectCreate
from app.exceptions.subject_exceptions import (
    SubjectNotFoundException,
    SubjectAlreadyExistsException,
    SubjectHasDependenciesException,
    MinimumGroupsRequiredException
)
from app.exceptions.group_exceptions import GroupAlreadyExistsException
from app.exceptions.teacher_exceptions import TeacherNotFoundException
from app.exceptions.base_exceptions import ValidationException

logger = logging.getLogger(__name__)


class SubjectService:
    
    def __init__(self):
        self.subject_repo = SubjectRepository()
        self.group_repo = GroupRepository()
        self.teacher_subject_repo = TeacherSubjectRepository()
        self.teacher_repo = TeacherRepository()

    async def _validate_teacher_exists_and_active(self, teacher_id: str) -> None:
        """Valida que un docente exista y esté activo"""
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        
        if not teacher.get("activo", True):
            raise ValidationException(
                message=f"El docente {teacher_id} no está activo",
                field="id_docente",
                details={
                    "teacher_id": teacher_id,
                    "teacher_status": "inactive"
                }
            )

    async def create_subject_with_groups_and_teachers(
        self, 
        subject_data: SubjectCreate, 
        groups_with_teachers: List[Dict[str, Any]],
        created_by: str
    ) -> SubjectResponse:
        """
        Crea una materia con grupos y asigna docentes a cada grupo usando TeacherSubject
        """
        # Verificar si la materia ya existe
        existing_subject = await self.subject_repo.get_by_id(subject_data.codigo_materia)
        if existing_subject:
            raise SubjectAlreadyExistsException(subject_data.codigo_materia)

        # Validar que hay al menos un grupo
        if not groups_with_teachers:
            raise MinimumGroupsRequiredException()

        # Validar que todos los docentes existen y están activos
        for group_data in groups_with_teachers:
            await self._validate_teacher_exists_and_active(group_data["id_docente"])

        # Crear la materia
        subject_dict = subject_data.model_dump()
        subject_dict.update({
            "activo": True,
            "created_by": created_by
        })
        
        subject_id = subject_data.codigo_materia
        await self.subject_repo.create(subject_dict, subject_id)

        try:
            # Crear grupos y asignaciones
            for group_data in groups_with_teachers:
                # Crear grupo (sin docente)
                group_create = GroupCreate(codigo_grupo=group_data["codigo_grupo"],codigo_materia=subject_id)
                group_dict = group_create.model_dump()
                group_dict.update({
                    "activo": True,
                    "created_by": created_by
                })
                
                # Verificar si el grupo ya existe
                existing_group = await self.group_repo.get_by_id(str(group_data["codigo_grupo"]))
                if existing_group:
                    # Rollback: marcar materia como inactiva
                    await self.subject_repo.update(subject_id, {"activo": False})
                    raise GroupAlreadyExistsException(group_data["codigo_grupo"])
                    
                await self.group_repo.create(group_dict, str(group_data["codigo_grupo"]))
                
                # Crear asignación docente-materia-grupo en TeacherSubject
                teacher_subject_data = TeacherSubjectCreate(
                    id_docente=group_data["id_docente"],
                    codigo_materia=subject_id,
                    codigo_grupo=group_data["codigo_grupo"]
                )
                
                teacher_subject_dict = teacher_subject_data.model_dump()
                teacher_subject_dict.update({
                    "activo": True,
                    "created_by": created_by
                })
                
                await self.teacher_subject_repo.create(teacher_subject_dict)
        
        except Exception as e:
            # Si algo falla, desactivar la materia
            await self.subject_repo.update(subject_id, {"activo": False})
            logger.error(f"Error creando grupos y asignaciones para materia {subject_id}: {str(e)}")
            raise

        # Obtener la materia creada con sus grupos
        subject_with_groups = await self.subject_repo.get_subject_with_groups(subject_id)
        return SubjectResponse(**subject_with_groups)

    async def get_subject(self, subject_code: str) -> SubjectResponse:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        return SubjectResponse(**subject)

    async def get_subject_with_groups(self, subject_code: str) -> Dict[str, Any]:
        subject_with_groups = await self.subject_repo.get_subject_with_groups(subject_code)
        if not subject_with_groups:
            raise SubjectNotFoundException(subject_code)
        
        # Obtener información de docentes asignados desde TeacherSubject
        assignments = await self.teacher_subject_repo.get_assignments_by_subject(subject_code)
        subject_with_groups["asignaciones_docentes"] = assignments
        
        return subject_with_groups

    async def get_all_subjects(
        self, 
        active_only: bool = True,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[SubjectSummary], int]:
        filters = {"activo": True} if active_only else {}
        subjects = await self.subject_repo.get_all(filters=filters)
        
        total = len(subjects)
        start = (page - 1) * limit
        end = start + limit
        paginated_subjects = subjects[start:end]
        
        return [SubjectSummary(**subject) for subject in paginated_subjects], total

    async def update_subject(
        self, 
        subject_code: str, 
        subject_data: SubjectUpdate
    ) -> SubjectResponse:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        update_dict = subject_data.model_dump(exclude_none=True)
        if update_dict:
            await self.subject_repo.update(subject_code, update_dict)

        updated_subject = await self.subject_repo.get_by_id(subject_code)
        return SubjectResponse(**updated_subject)

    async def deactivate_subject(self, subject_code: str, reason: str) -> bool:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Verificar si la materia tiene grupos activos
        if await self.subject_repo.subject_has_groups(subject_code):
            raise SubjectHasDependenciesException(
                subject_code,
                dependencies={"grupos_activos": True}
            )

        return await self.subject_repo.update(subject_code, {
            "activo": False,
            "razon_desactivacion": reason
        })
    
    async def activate_subject(self, subject_code: str) -> bool:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        return await self.subject_repo.update(subject_code, {"activo": True})

    async def add_group_to_subject(
        self, 
        subject_code: str, 
        group_data: GroupCreate,
        teacher_id: str,
        created_by: str
    ) -> bool:
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)

        # Validar que el docente existe y está activo
        await self._validate_teacher_exists_and_active(teacher_id)

        # Verificar si el grupo ya existe
        existing_group = await self.group_repo.get_by_id(str(group_data.codigo_grupo))
        if existing_group:
            raise GroupAlreadyExistsException(group_data.codigo_grupo)

        # Crear el grupo (sin docente)
        group_dict = group_data.model_dump()
        group_dict.update({
            "codigo_materia": subject_code,
            "activo": True,
            "created_by": created_by
        })
        
        await self.group_repo.create(group_dict, str(group_data.codigo_grupo))
        
        # Crear asignación en TeacherSubject
        teacher_subject_data = TeacherSubjectCreate(
            id_docente=teacher_id,
            codigo_materia=subject_code,
            codigo_grupo=group_data.codigo_grupo
        )
        
        teacher_subject_dict = teacher_subject_data.model_dump()
        teacher_subject_dict.update({
            "activo": True,
            "created_by": created_by
        })
        
        await self.teacher_subject_repo.create(teacher_subject_dict)
        
        return True

    async def get_subject_assignments(self, subject_code: str) -> List[Dict[str, Any]]:
        """Obtiene todas las asignaciones de docentes para una materia"""
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
            
        assignments = await self.teacher_subject_repo.get_assignments_by_subject(subject_code)
        return assignments