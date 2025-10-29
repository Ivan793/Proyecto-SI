from typing import Optional, Dict, Any
from .base_exceptions import (
    NotFoundException,
    ConflictException,
    ValidationException,
    DependencyException
)
from app.core.response_codes import ResponseCode


class SubjectNotFoundException(NotFoundException):
    """Materia no encontrada"""
    
    def __init__(self, subject_code: str):
        super().__init__(
            resource="Materia",
            identifier=subject_code,
            code=ResponseCode.NOT_FOUND
        )


class SubjectAlreadyExistsException(ConflictException):
    """Materia ya existe"""
    
    def __init__(self, subject_code: str):
        super().__init__(
            message=f"Ya existe una materia con código '{subject_code}'",
            conflict_field="codigo_materia",
            code=ResponseCode.ALREADY_EXISTS
        )


class SubjectHasDependenciesException(DependencyException):
    """Materia tiene dependencias activas"""
    
    def __init__(
        self,
        subject_code: str,
        dependencies: Optional[Dict[str, Any]] = None
    ):
        message = f"No se puede desactivar/eliminar la materia '{subject_code}' porque tiene dependencias activas"
        super().__init__(
            message=message,
            dependencies=dependencies or {},
            code=ResponseCode.DEPENDENCY_ERROR
        )


class InvalidSubjectStateException(ConflictException):
    """Estado de materia inválido"""
    
    def __init__(self, current_state: str, target_state: str):
        message = f"No se puede cambiar el estado de la materia de '{current_state}' a '{target_state}'"
        super().__init__(
            message=message,
            code=ResponseCode.INVALID_STATE
        )


class MinimumGroupsRequiredException(ValidationException):
    """Se requiere al menos un grupo para crear una materia"""
    
    def __init__(self):
        super().__init__(
            message="Para crear una materia se requiere al menos un grupo asociado",
            code=ResponseCode.VALIDATION_ERROR
        )