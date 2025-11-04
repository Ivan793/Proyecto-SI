from typing import Any, Dict, Optional
from .base_exceptions import NotFoundException, ConflictException, DependencyException, ValidationException
from app.core.response_codes import ResponseCode


class GroupNotFoundException(NotFoundException):
    """Grupo no encontrado"""
    
    def __init__(self, group_code: str):
        super().__init__(
            resource="Grupo", 
            identifier=str(group_code),
            code=ResponseCode.NOT_FOUND
        )


class GroupAlreadyExistsException(ConflictException):
    """Grupo ya existe"""
    
    def __init__(self, group_code: str):
        super().__init__(
            message=f"Ya existe un grupo con código {group_code}",
            conflict_field="codigo_grupo",
            code=ResponseCode.ALREADY_EXISTS
        )


class GroupHasStudentsException(DependencyException):
    """Grupo tiene estudiantes inscritos"""
    
    def __init__(self, group_code: str):
        super().__init__(
            message=f"No se puede desactivar el grupo {group_code} porque tiene estudiantes inscritos",
            code=ResponseCode.DEPENDENCY_ERROR
        )


class GroupHasNoTeacherException(ValidationException):
    """Grupo sin profesor asignado"""
    
    def __init__(self, group_code: str):
        super().__init__(
            message=f"El grupo '{group_code}' no tiene un profesor asignado",
            code=ResponseCode.VALIDATION_ERROR
        )


class GroupHasNoSubjectException(ValidationException):
    """Grupo sin materia asignada"""
    
    def __init__(self, group_code: str):
        super().__init__(
            message=f"El grupo '{group_code}' no tiene una materia asignada",
            code=ResponseCode.VALIDATION_ERROR
        )


class GroupHasDependenciesException(DependencyException):
    """Grupo tiene dependencias activas"""
    
    def __init__(
        self,
        group_code: str,
        dependencies: Optional[Dict[str, Any]] = None
    ):
        message = f"No se puede eliminar el grupo '{group_code}' porque tiene dependencias activas"
        super().__init__(
            message=message,
            dependencies=dependencies or {},
            code=ResponseCode.DEPENDENCY_ERROR
        )