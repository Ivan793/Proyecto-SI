from typing import Optional
from .base_exceptions import NotFoundException, ConflictException, DependencyException


class TeacherNotFoundException(NotFoundException):
    def __init__(self, teacher_id: str):
        super().__init__(resource="Profesor", identifier=teacher_id)


class TeacherAlreadyExistsException(ConflictException):
    def __init__(self, user_id: str):
        super().__init__(
            message=f"Ya existe un docente para el usuario {user_id}",
            conflict_field="id_usuario"
        )


class TeacherHasAssignmentsException(DependencyException):
    def __init__(self, teacher_id: str):
        super().__init__(
            message=f"No se puede desactivar el docente {teacher_id} porque tiene asignaciones activas"
        )