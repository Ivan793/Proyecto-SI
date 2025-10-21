from typing import List, Optional, Dict, Any
import logging

from app.repositories.teacher_subject_repository import TeacherSubjectRepository
from app.repositories.teacher_repository import TeacherRepository
from app.repositories.subject_repository import SubjectRepository
from app.repositories.group_repository import GroupRepository
from app.schemas.teacherSubject import (
    TeacherSubjectCreate, 
    TeacherSubjectUpdate, 
    TeacherSubjectResponse
)
from app.exceptions.teacher_subject_exceptions import (
    TeacherSubjectNotFoundException,
    TeacherSubjectAlreadyExistsException,
    TeacherSubjectAssignmentException
)
from app.exceptions.teacher_exceptions import TeacherNotFoundException
from app.exceptions.subject_exceptions import SubjectNotFoundException
from app.exceptions.group_exceptions import GroupNotFoundException

logger = logging.getLogger(__name__)


class TeacherSubjectService:
    
    def __init__(self):
        self.teacher_subject_repo = TeacherSubjectRepository()
        self.teacher_repo = TeacherRepository()
        self.subject_repo = SubjectRepository()
        self.group_repo = GroupRepository()

    async def _validate_assignment_data(
        self, 
        teacher_id: str, 
        subject_code: str, 
        group_code: int
    ) -> None:
        """Valida que el docente, materia y grupo existan"""
        # Validar docente
        teacher = await self.teacher_repo.get_by_id(teacher_id)
        if not teacher:
            raise TeacherNotFoundException(teacher_id)
        if not teacher.get("activo", True):
            raise TeacherSubjectAssignmentException(
                f"El docente '{teacher_id}' no está activo",
                field="id_docente"
            )

        # Validar materia
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        if not subject.get("activo", True):
            raise TeacherSubjectAssignmentException(
                f"La materia '{subject_code}' no está activa",
                field="codigo_materia"
            )

        # Validar grupo
        group = await self.group_repo.get_by_id(str(group_code))
        if not group:
            raise GroupNotFoundException(group_code)
        if not group.get("activo", True):
            raise TeacherSubjectAssignmentException(
                f"El grupo '{group_code}' no está activo",
                field="codigo_grupo"
            )

    async def create_assignment(
        self, 
        assignment_data: TeacherSubjectCreate,
        created_by: str
    ) -> TeacherSubjectResponse:
        # Validar que los recursos existen
        await self._validate_assignment_data(
            assignment_data.id_docente,
            assignment_data.codigo_materia,
            assignment_data.codigo_grupo
        )

        # Verificar si ya existe la asignación
        existing_assignment = await self.teacher_subject_repo.get_assignment_by_teacher_subject_group(
            assignment_data.id_docente,
            assignment_data.codigo_materia,
            assignment_data.codigo_grupo
        )
        if existing_assignment:
            raise TeacherSubjectAlreadyExistsException(
                assignment_data.id_docente,
                assignment_data.codigo_materia,
                assignment_data.codigo_grupo
            )

        # Crear la asignación
        assignment_dict = assignment_data.model_dump()
        assignment_dict.update({
            "activo": True,
            "created_by": created_by
        })
        
        assignment_id = await self.teacher_subject_repo.create(assignment_dict)
        
        # Obtener la asignación creada
        assignment = await self.teacher_subject_repo.get_by_id(assignment_id)
        return TeacherSubjectResponse(**assignment)

    async def get_assignment(self, assignment_id: str) -> TeacherSubjectResponse:
        assignment = await self.teacher_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise TeacherSubjectNotFoundException(assignment_id)
        return TeacherSubjectResponse(**assignment)

    async def get_assignments_by_teacher(
        self, 
        teacher_id: str,
        active_only: bool = True
    ) -> List[TeacherSubjectResponse]:
        assignments = await self.teacher_subject_repo.get_assignments_by_teacher(teacher_id)
        
        if active_only:
            assignments = [a for a in assignments if a.get("activo", True)]
            
        return [TeacherSubjectResponse(**assignment) for assignment in assignments]

    async def get_assignments_by_subject(
        self, 
        subject_code: str,
        active_only: bool = True
    ) -> List[TeacherSubjectResponse]:
        assignments = await self.teacher_subject_repo.get_assignments_by_subject(subject_code)
        
        if active_only:
            assignments = [a for a in assignments if a.get("activo", True)]
            
        return [TeacherSubjectResponse(**assignment) for assignment in assignments]

    async def get_assignments_by_group(
        self, 
        group_code: int,
        active_only: bool = True
    ) -> List[TeacherSubjectResponse]:
        assignments = await self.teacher_subject_repo.get_assignments_by_group(group_code)
        
        if active_only:
            assignments = [a for a in assignments if a.get("activo", True)]
            
        return [TeacherSubjectResponse(**assignment) for assignment in assignments]

    async def update_assignment(
        self, 
        assignment_id: str, 
        assignment_data: TeacherSubjectUpdate
    ) -> TeacherSubjectResponse:
        assignment = await self.teacher_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise TeacherSubjectNotFoundException(assignment_id)

        # Validar datos si se proporcionan
        if assignment_data.id_docente or assignment_data.codigo_materia or assignment_data.codigo_grupo:
            teacher_id = assignment_data.id_docente or assignment["id_docente"]
            subject_code = assignment_data.codigo_materia or assignment["codigo_materia"]
            group_code = assignment_data.codigo_grupo or assignment["codigo_grupo"]
            
            await self._validate_assignment_data(teacher_id, subject_code, group_code)

        update_dict = assignment_data.model_dump(exclude_none=True)
        if update_dict:
            await self.teacher_subject_repo.update(assignment_id, update_dict)

        updated_assignment = await self.teacher_subject_repo.get_by_id(assignment_id)
        return TeacherSubjectResponse(**updated_assignment)

    async def deactivate_assignment(self, assignment_id: str, reason: str) -> bool:
        assignment = await self.teacher_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise TeacherSubjectNotFoundException(assignment_id)

        return await self.teacher_subject_repo.update(assignment_id, {
            "activo": False,
            "razon_desactivacion": reason
        })

    async def activate_assignment(self, assignment_id: str) -> bool:
        assignment = await self.teacher_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise TeacherSubjectNotFoundException(assignment_id)

        return await self.teacher_subject_repo.update(assignment_id, {"activo": True})

    async def get_teacher_workload(self, teacher_id: str) -> Dict[str, Any]:
        """Obtiene la carga de trabajo de un docente (número de asignaciones activas)"""
        assignments = await self.get_assignments_by_teacher(teacher_id, active_only=True)
        
        return {
            "id_docente": teacher_id,
            "total_asignaciones": len(assignments),
            "asignaciones_activas": assignments
        }