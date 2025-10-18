from typing import Any, Dict, Optional
from .base_exceptions import NotFoundException, ConflictException, DependencyException, ValidationException


class GroupNotFoundException(NotFoundException):
    def __init__(self, group_code: int):
        super().__init__(resource="Grupo", identifier=str(group_code))


class GroupAlreadyExistsException(ConflictException):
    def __init__(self, group_code: int):
        super().__init__(
            message=f"Ya existe un grupo con código {group_code}",
            conflict_field="codigo_grupo"
        )


class GroupHasStudentsException(DependencyException):
    def __init__(self, group_code: int):
        super().__init__(
            message=f"No se puede desactivar el grupo {group_code} porque tiene estudiantes inscritos"
        )


class SubjectNotFoundException(NotFoundException):
    def __init__(self, subject_code: str):
        super().__init__(resource="Materia", identifier=subject_code)


class TeacherNotFoundException(NotFoundException):
    def __init__(self, teacher_id: str):
        super().__init__(resource="Profesor", identifier=teacher_id)

class GroupHasNoTeacherException(ValidationException):
    """Grupo sin profesor asignado"""
    
    def __init__(self, group_code: int):
        super().__init__(
            message=f"El grupo '{group_code}' no tiene un profesor asignado"
        )

class GroupHasNoSubjectException(ValidationException):
    """Grupo sin materia asignada"""
    
    def __init__(self, group_code: int):
        super().__init__(
            message=f"El grupo '{group_code}' no tiene una materia asignada"
        )


class GroupHasDependenciesException(DependencyException):
    """Grupo tiene dependencias activas"""
    
    def __init__(
        self,
        group_code: int,
        dependencies: Optional[Dict[str, Any]] = None
    ):
        message = f"No se puede eliminar el grupo '{group_code}' porque tiene dependencias activas"
        super().__init__(
            message=message,
            dependencies=dependencies or {}
        )