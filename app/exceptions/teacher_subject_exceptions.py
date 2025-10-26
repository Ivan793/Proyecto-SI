from typing import Optional, Dict, Any
from .base_exceptions import (
    NotFoundException, 
    ConflictException, 
    ValidationException,
    DependencyException
)

class TeacherSubjectNotFoundException(NotFoundException):
    """Asignación docente-materia no encontrada"""
    
    def __init__(self, assignment_id: str):
        super().__init__(
            resource="Asignación docente-materia",
            identifier=assignment_id
        )


class TeacherSubjectAlreadyExistsException(ConflictException):
    """Asignación docente-materia ya existe"""
    
    def __init__(self, teacher_id: str, subject_code: str, group_code: int):
        super().__init__(
            message=f"El docente '{teacher_id}' ya está asignado a la materia '{subject_code}' grupo {group_code}",
            conflict_field="id_docente"
        )


class TeacherSubjectAssignmentException(ValidationException):
    """Error en la asignación docente-materia"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            field=field
        )


class TeacherSubjectHasDependenciesException(DependencyException):
    """Asignación tiene dependencias activas"""
    
    def __init__(
        self,
        assignment_id: str,
        dependencies: Optional[Dict[str, Any]] = None
    ):
        message = f"No se puede eliminar la asignación '{assignment_id}' porque tiene dependencias activas"
        super().__init__(
            message=message,
            dependencies=dependencies or {}
        )