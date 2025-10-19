from typing import Optional
from .base_exceptions import NotFoundException, ConflictException, DependencyException

class StudentNotFoundException(NotFoundException):
    def __init__(self, student_id: str):
        super().__init__(resource="Estudiante", identifier=student_id)

class StudentAlreadyExistsException(ConflictException):
    def __init__(self, user_id: str):
        super().__init__(
            message=f"Ya existe un estudiante para el usuario {user_id}",
            conflict_field="id_usuario"
        )