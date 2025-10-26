from typing import Optional, Dict, Any
from .base_exceptions import (
    NotFoundException, 
    ConflictException, 
    ValidationException,
    DependencyException
)
from app.core.response_codes import ResponseCode

class TeacherSubjectNotFoundException(NotFoundException):
    """Asignación docente-materia no encontrada"""
    
    def __init__(self, assignment_id: str):
        super().__init__(
            resource="Asignación docente-materia",
            identifier=assignment_id,
            code=ResponseCode.NOT_FOUND
        )


class TeacherSubjectAlreadyExistsException(ConflictException):
    """Asignación docente-materia ya existe"""
    
    def __init__(self, teacher_id: str, subject_code: str, group_code: int):
        super().__init__(
            message=f"El docente '{teacher_id}' ya está asignado a la materia '{subject_code}' grupo {group_code}",
            conflict_field="id_docente",
            code=ResponseCode.ALREADY_EXISTS
        )


class TeacherSubjectAssignmentException(ValidationException):
    """Error en la asignación docente-materia"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            field=field,
            code=ResponseCode.BUSINESS_RULE_VIOLATION
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
            dependencies=dependencies or {},
            code=ResponseCode.DEPENDENCY_ERROR
        )


class TeacherNotAvailableException(ConflictException):
    """Profesor no disponible"""
    
    def __init__(self, teacher_id: str, reason: str = ""):
        message = f"El profesor '{teacher_id}' no está disponible"
        if reason:
            message += f": {reason}"
        super().__init__(
            message=message,
            code=ResponseCode.RESOURCE_IN_USE
        )