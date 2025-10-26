from typing import Optional
from .base_exceptions import NotFoundException, ConflictException, ValidationException


class UserNotFoundException(NotFoundException):
    """Usuario no encontrado"""
    
    def __init__(self, user_id: str):
        super().__init__(
            resource="Usuario",
            identifier=user_id
        )


class UserAlreadyExistsException(ConflictException):
    """Usuario ya existe"""
    
    def __init__(
        self,
        field: str = "correo",
        value: Optional[str] = None
    ):
        message = f"Ya existe un usuario con {field}: {value}" if value else f"Ya existe un usuario con ese {field}"
        super().__init__(
            message=message,
            conflict_field=field
        )


class TeacherNotFoundException(NotFoundException):
    """Profesor no encontrado"""
    
    def __init__(self, teacher_id: str):
        super().__init__(
            resource="Profesor",
            identifier=teacher_id
        )


class StudentNotFoundException(NotFoundException):
    """Estudiante no encontrado"""
    
    def __init__(self, student_id: str):
        super().__init__(
            resource="Estudiante",
            identifier=student_id
        )


class GuestNotFoundException(NotFoundException):
    """Invitado no encontrado"""
    
    def __init__(self, guest_id: str):
        super().__init__(
            resource="Invitado",
            identifier=guest_id
        )


class InvalidEmailDomainException(ValidationException):
    """Dominio de correo inválido"""
    
    def __init__(
        self,
        role: str,
        required_domain: str = "@unicesar.edu.co"
    ):
        message = f"Los usuarios con rol '{role}' deben tener correo institucional ({required_domain})"
        super().__init__(
            message=message,
            field="correo"
        )


class InvalidPasswordException(ValidationException):
    """Contraseña inválida"""
    
    def __init__(
        self,
        message: str = "La contraseña no cumple con los requisitos de seguridad"
    ):
        super().__init__(
            message=message,
            field="contraseña"
        )


class InvalidDocumentException(ValidationException):
    """Documento de identidad inválido"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            field="identificacion"
        )