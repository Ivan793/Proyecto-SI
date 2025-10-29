from typing import Optional
from .base_exceptions import NotFoundException, ConflictException, DependencyException, BusinessRuleException
from app.core.response_codes import ResponseCode


class TeacherNotFoundException(NotFoundException):
    def __init__(self, teacher_id: str):
        super().__init__(
            resource="Profesor",
            identifier=teacher_id,
            code=ResponseCode.NOT_FOUND
        )


class TeacherAlreadyExistsException(ConflictException):
    def __init__(self, user_id: str):
        super().__init__(
            message=f"Ya existe un docente para el usuario {user_id}",
            conflict_field="id_usuario",
            code=ResponseCode.ALREADY_EXISTS
        )


class TeacherHasAssignmentsException(DependencyException):
    def __init__(self, teacher_id: str):
        super().__init__(
            message=f"No se puede desactivar el docente {teacher_id} porque tiene asignaciones activas",
            code=ResponseCode.DEPENDENCY_ERROR
        )


class TeacherCreationException(BusinessRuleException):
    """Error durante la creación del docente"""
    
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            rule="teacher_creation",
            details=details,
            code=ResponseCode.BUSINESS_RULE_VIOLATION
        )


class TeacherUpdateException(BusinessRuleException):
    """Error durante la actualización del docente"""
    
    def __init__(self, teacher_id: str, reason: str):
        super().__init__(
            message=f"No se puede actualizar el docente {teacher_id}: {reason}",
            rule="teacher_update",
            code=ResponseCode.INVALID_OPERATION
        )