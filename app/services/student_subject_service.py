# app/services/student_subject_service.py

from typing import List, Optional, Dict, Any
import logging

from app.repositories.student_subject_repository import StudentSubjectRepository # ⚠️ Debes crear este
from app.repositories.student_repository import StudentRepository # Ya importado en el anterior
from app.repositories.subject_repository import SubjectRepository # Reutilizado
from app.repositories.group_repository import GroupRepository # Reutilizado
from app.schemas.student_subject import (
    StudentSubjectCreate, 
    StudentSubjectUpdate, 
    StudentSubjectResponse
)
from app.exceptions.student_subject_exceptions import (
    StudentSubjectNotFoundException,
    StudentSubjectAlreadyExistsException,
    StudentSubjectAssignmentException
)
from app.exceptions.student_exceptions import StudentNotFoundException
from app.exceptions.subject_exceptions import SubjectNotFoundException
from app.exceptions.group_exceptions import GroupNotFoundException

logger = logging.getLogger(__name__)


class StudentSubjectService:
    
    def __init__(self):
        self.student_subject_repo = StudentSubjectRepository() # Análogo a TeacherSubjectRepository
        self.student_repo = StudentRepository()
        self.subject_repo = SubjectRepository()
        self.group_repo = GroupRepository()

    async def _validate_assignment_data(
        self, 
        student_id: str, 
        subject_code: str, 
        group_code: int
    ) -> None:
        """Valida que el estudiante, materia y grupo existan y estén activos"""
        # Validar estudiante
        student = await self.student_repo.get_by_id(student_id)
        if not student:
            raise StudentNotFoundException(student_id)
        if not student.get("activo", True):
            raise StudentSubjectAssignmentException(
                f"El estudiante '{student_id}' no está activo",
                field="id_estudiante"
            )

        # Validar materia
        subject = await self.subject_repo.get_by_id(subject_code)
        if not subject:
            raise SubjectNotFoundException(subject_code)
        if not subject.get("activo", True):
            # Asumo que SubjectRepository devuelve un diccionario
            raise StudentSubjectAssignmentException(
                f"La materia '{subject_code}' no está activa",
                field="codigo_materia"
            )

        # Validar grupo
        group = await self.group_repo.get_by_id(str(group_code))
        if not group:
            raise GroupNotFoundException(group_code)
        if not group.get("activo", True):
            # Asumo que GroupRepository devuelve un diccionario
            raise StudentSubjectAssignmentException(
                f"El grupo '{group_code}' no está activo",
                field="codigo_grupo"
            )

    async def create_assignment(
        self, 
        assignment_data: StudentSubjectCreate,
        created_by: str
    ) -> StudentSubjectResponse:
        
        await self._validate_assignment_data(
            assignment_data.id_estudiante, # 🚨 CAMBIO
            assignment_data.codigo_materia,
            assignment_data.codigo_grupo
        )

        # Verificar si ya existe la asignación
        existing_assignment = await self.student_subject_repo.get_assignment_by_student_subject_group( # ⚠️ Debe existir este método
            assignment_data.id_estudiante,
            assignment_data.codigo_materia,
            assignment_data.codigo_grupo
        )
        if existing_assignment:
            raise StudentSubjectAlreadyExistsException(
                assignment_data.id_estudiante,
                assignment_data.codigo_materia,
                assignment_data.codigo_grupo
            )

        # Crear la asignación
        assignment_dict = assignment_data.model_dump()
        assignment_dict.update({
            "activo": True,
            "created_by": created_by
        })
        
        assignment_id = await self.student_subject_repo.create(assignment_dict)
        
        assignment = await self.student_subject_repo.get_by_id(assignment_id)
        return StudentSubjectResponse(**assignment)

    # --- Métodos Análogos a TeacherSubjectService ---

    async def get_assignment(self, assignment_id: str) -> StudentSubjectResponse:
        assignment = await self.student_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise StudentSubjectNotFoundException(assignment_id)
        return StudentSubjectResponse(**assignment)
    
    async def get_assignments_by_student(
        self, 
        student_id: str, # 🚨 CAMBIO
        active_only: bool = True
    ) -> List[StudentSubjectResponse]:
        assignments = await self.student_subject_repo.get_assignments_by_student(student_id) # ⚠️ Debe existir este método
        
        if active_only:
            assignments = [a for a in assignments if a.get("activo", True)]
            
        return [StudentSubjectResponse(**assignment) for assignment in assignments]

    async def update_assignment(
        self, 
        assignment_id: str, 
        assignment_data: StudentSubjectUpdate
    ) -> StudentSubjectResponse:
        assignment = await self.student_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise StudentSubjectNotFoundException(assignment_id)

        if assignment_data.id_estudiante or assignment_data.codigo_materia or assignment_data.codigo_grupo:
            student_id = assignment_data.id_estudiante or assignment["id_estudiante"] # 🚨 CAMBIO
            subject_code = assignment_data.codigo_materia or assignment["codigo_materia"]
            group_code = assignment_data.codigo_grupo or assignment["codigo_grupo"]
            
            await self._validate_assignment_data(student_id, subject_code, group_code)

        update_dict = assignment_data.model_dump(exclude_none=True)
        if update_dict:
            await self.student_subject_repo.update(assignment_id, update_dict)

        updated_assignment = await self.student_subject_repo.get_by_id(assignment_id)
        return StudentSubjectResponse(**updated_assignment)

    async def deactivate_assignment(self, assignment_id: str, reason: str) -> bool:
        assignment = await self.student_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise StudentSubjectNotFoundException(assignment_id)

        return await self.student_subject_repo.update(assignment_id, {
            "activo": False,
            "razon_desactivacion": reason
        })

    async def activate_assignment(self, assignment_id: str) -> bool:
        assignment = await self.student_subject_repo.get_by_id(assignment_id)
        if not assignment:
            raise StudentSubjectNotFoundException(assignment_id)

        return await self.student_subject_repo.update(assignment_id, {"activo": True})