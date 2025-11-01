from .base_exceptions import NotFoundException, ConflictException, ValidationException
from app.core.response_codes import ResponseCode

# ==================== FACULTAD ====================

class FacultyNotFoundException(NotFoundException):
    """Facultad no encontrada"""
    
    def __init__(self, faculty_id: str):
        super().__init__(
            resource="Facultad",
            identifier=faculty_id,
            code=ResponseCode.NOT_FOUND
        )

class FacultyAlreadyExistsException(ConflictException):
    """Facultad ya existe"""
    
    def __init__(self, faculty_id: str):
        super().__init__(
            message=f"Ya existe una facultad con código '{faculty_id}'",
            conflict_field="id_facultad",
            code=ResponseCode.ALREADY_EXISTS
        )

# ==================== PROGRAMA ====================

class ProgramNotFoundException(NotFoundException):
    """Programa no encontrado"""
    
    def __init__(self, program_code: str):
        super().__init__(
            resource="Programa",
            identifier=program_code,
            code=ResponseCode.NOT_FOUND
        )

class ProgramAlreadyExistsException(ConflictException):
    """Programa ya existe"""
    
    def __init__(self, program_code: str):
        super().__init__(
            message=f"Ya existe un programa con código '{program_code}'",
            conflict_field="codigo_programa",
            code=ResponseCode.ALREADY_EXISTS
        )

class InvalidFacultyException(ValidationException):
    """Facultad inválida"""
    
    def __init__(self, faculty_id: str):
        super().__init__(
            message=f"La facultad '{faculty_id}' no existe",
            field="id_facultad",
            code=ResponseCode.VALIDATION_ERROR
        )