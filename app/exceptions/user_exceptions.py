from typing import Optional
from .base_exceptions import NotFoundException, ConflictException, ValidationException, BusinessRuleException
from app.core.response_codes import ResponseCode


class UserNotFoundException(NotFoundException):
    """Usuario no encontrado"""
    
    def __init__(self, user_id: str):
        super().__init__(
            resource="Usuario",
            identifier=user_id,
            code=ResponseCode.NOT_FOUND
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
            conflict_field=field,
            code=ResponseCode.ALREADY_EXISTS
        )


class TeacherNotFoundException(NotFoundException):
    """Profesor no encontrado"""
    
    def __init__(self, teacher_id: str):
        super().__init__(
            resource="Profesor",
            identifier=teacher_id,
            code=ResponseCode.NOT_FOUND
        )


class StudentNotFoundException(NotFoundException):
    """Estudiante no encontrado"""
    
    def __init__(self, student_id: str):
        super().__init__(
            resource="Estudiante",
            identifier=student_id,
            code=ResponseCode.NOT_FOUND
        )


class GuestNotFoundException(NotFoundException):
    """Invitado no encontrado"""
    
    def __init__(self, guest_id: str):
        super().__init__(
            resource="Invitado",
            identifier=guest_id,
            code=ResponseCode.NOT_FOUND
        )


class GraduateNotFoundException(NotFoundException):
    """Egresado no encontrado"""
    
    def __init__(self, graduate_id: str):
        super().__init__(
            resource="Egresado",
            identifier=graduate_id,
            code=ResponseCode.NOT_FOUND
        )


class InvalidEmailDomainException(ValidationException):
    """Dominio de correo inválido"""
    
    def __init__(
        self,
        role: str,
        required_domain: str = "@unicesar.edu.co",
        custom_message: Optional[str] = None
    ):
        if custom_message:
            message = custom_message
        else:
            # Si el rol es un Enum, obtener su valor
            role_str = role.value if hasattr(role, 'value') else role
            message = f"Los usuarios con rol '{role_str}' deben tener correo institucional ({required_domain})"
        
        super().__init__(
            message=message,
            field="correo",
            code=ResponseCode.INVALID_EMAIL
        )


class InvalidPasswordException(ValidationException):
    """Contraseña inválida"""
    
    def __init__(
        self,
        message: str = "La contraseña no cumple con los requisitos de seguridad"
    ):
        super().__init__(
            message=message,
            field="contraseña",
            code=ResponseCode.INVALID_PASSWORD
        )


class InvalidDocumentException(ValidationException):
    """Documento de identidad inválido"""
    
    def __init__(self, message: str):
        super().__init__(
            message=message,
            field="identificacion",
            code=ResponseCode.INVALID_IDENTIFICATION
        )


class UserDeactivationException(BusinessRuleException):
    """Error al desactivar usuario"""
    
    def __init__(self, user_id: str, reason: str):
        super().__init__(
            message=f"No se puede desactivar el usuario {user_id}: {reason}",
            rule="user_deactivation",
            code=ResponseCode.INVALID_OPERATION
        )


class UserActivationException(BusinessRuleException):
    """Error al activar usuario"""
    
    def __init__(self, user_id: str, reason: str):
        super().__init__(
            message=f"No se puede activar el usuario {user_id}: {reason}",
            rule="user_activation",
            code=ResponseCode.INVALID_OPERATION
        )