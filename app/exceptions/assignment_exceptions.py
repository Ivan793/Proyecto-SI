from .base_exceptions import ConflictException


class TeacherSubjectAssignmentException(ConflictException):
    """Error en asignación docente-materia"""
    
    def __init__(self, message: str):
        super().__init__(message=message)


class TeacherNotAvailableException(ConflictException):
    """Profesor no disponible"""
    
    def __init__(self, teacher_id: str, reason: str = ""):
        message = f"El profesor '{teacher_id}' no está disponible"
        if reason:
            message += f": {reason}"
        super().__init__(message=message)