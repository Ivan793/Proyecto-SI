from typing import Any, Optional, List
from pydantic import field_validator, model_validator
from pydantic_core.core_schema import ValidationInfo
import re
from datetime import datetime

from app.core.patterns import Patterns
from app.core.constants import Limits, ValidationMessages, EmailDomains
from app.core.enums import Role


class BaseValidators:
    """Validadores para lógica compleja que Pydantic NO puede hacer automáticamente."""
    
    @staticmethod
    def validate_email_domain(email: str, role: Optional[str] = None) -> str:
        """
        Valida dominio de correo según configuración centralizada.
        Pydantic ya validó el formato básico, esta es lógica de negocio compleja.
        """
        email = email.lower().strip()
        
        # Si no hay rol o rol no requiere validación específica
        if not role or role.upper() not in EmailDomains.ALLOWED_DOMAINS:
            return email
        
        # Verificar dominio permitido - LÓGICA DE NEGOCIO COMPLEJA
        if not EmailDomains.is_domain_allowed(email, role):
            allowed_domains = EmailDomains.get_allowed_domains(role)
            raise ValueError(
                ValidationMessages.INSTITUTIONAL_EMAIL_REQUIRED.format(
                    role=role,
                    domains=", ".join(allowed_domains)
                )
            )
        
        return email
    
    @staticmethod
    def validate_password_complexity(password: str) -> str:
        """
        Valida patrón complejo de contraseña.
        Pydantic ya validó longitud básica, esto es lógica de negocio.
        """
        if not re.match(Patterns.PASSWORD, password):
            raise ValueError(ValidationMessages.INVALID_PASSWORD)
        return password
    
    @staticmethod
    def validate_birth_date(date: datetime) -> datetime:
        """
        Valida reglas de negocio para fecha de nacimiento.
        Pydantic no puede validar edades mínimas/máximas automáticamente.
        """
        today = datetime.now()
        
        if date >= today:
            raise ValueError(ValidationMessages.PAST_DATE)
        
        # Validar edad mínima (15 años) - LÓGICA DE NEGOCIO
        min_age = 15
        age = (today - date).days / 365.25
        
        if age < min_age:
            raise ValueError(f"Debe tener al menos {min_age} años")
        
        # Validar edad máxima razonable (100 años) - LÓGICA DE NEGOCIO
        max_age = 100
        if age > max_age:
            raise ValueError("Fecha de nacimiento no válida")
        
        return date
    
    @staticmethod
    def transform_text_fields(value: str) -> str:
        """Transformación de formato (no validación) - Pydantic no hace esto."""
        return value.strip().title()
    
    @staticmethod
    def transform_identification(value: str) -> str:
        """Transformación de formato (no validación)."""
        return value.strip().upper()


class UserValidatorMixin:
    """
    Mixin que usa validadores SOLO para lógica compleja.
    Pydantic ya maneja las validaciones básicas de los tipos Annotated.
    """
    
    @field_validator('correo')
    @classmethod
    def validate_email_domain_by_role(cls, v: str, info: ValidationInfo) -> str:
        """Valida dominio según rol - Pydantic ya validó formato básico."""
        rol = info.data.get('rol')
        return BaseValidators.validate_email_domain(v, rol)
    
    @field_validator('nombres', 'apellidos')
    @classmethod
    def transform_names(cls, v: str) -> str:
        """Transforma formato de nombres - Pydantic ya validó contenido."""
        return BaseValidators.transform_text_fields(v)
    
    @field_validator('identificacion')
    @classmethod
    def transform_identification(cls, v: str) -> str:
        """Transforma formato de identificación."""
        return BaseValidators.transform_identification(v)
    
    @field_validator('fecha_nacimiento')
    @classmethod
    def validate_birth_date_business_rules(cls, v: datetime) -> datetime:
        """Valida reglas de negocio para fecha nacimiento."""
        return BaseValidators.validate_birth_date(v)


class StudentValidatorMixin:
    """Validadores específicos para estudiantes - LÓGICA DE NEGOCIO."""
    
    @field_validator('semestre')
    @classmethod
    def validate_semester_range(cls, v: int) -> int:
        """Valida rango de semestre - Pydantic no sabe los límites de negocio."""
        if v < 1 or v > 20:
            raise ValueError("El semestre debe estar entre 1 y 20")
        return v
    
    @field_validator('anio_ingreso')
    @classmethod
    def validate_admission_year_logic(cls, v: int) -> int:
        """Valida lógica de año de ingreso."""
        current_year = datetime.now().year
        
        if v < 2000:
            raise ValueError("Año de ingreso no válido")
        
        if v > current_year + 1:
            raise ValueError("Año de ingreso no puede ser futuro")
        
        return v
    
    @field_validator('periodo')
    @classmethod
    def validate_periodo_options(cls, v: int) -> int:
        """Valida opciones de periodo - Lógica de negocio."""
        if v not in [1, 2]:
            raise ValueError("El periodo debe ser 1 o 2")
        return v


class TeacherValidatorMixin:
    """Validadores específicos para docentes."""
    
    @field_validator('categoria_docente')
    @classmethod
    def validate_category_exists(cls, v: str) -> str:
        """
        La validación del enum ya está en el tipo, pero podemos agregar
        lógica adicional de negocio si es necesario.
        """
        return v


# Funciones helper para uso en servicios
def validate_user_role_email_match(email: str, rol: str) -> bool:
    """
    Función helper para validar en servicios que el email corresponda al rol.
    Retorna True si es válido, lanza ValueError si no.
    """
    try:
        BaseValidators.validate_email_domain(email, rol)
        return True
    except ValueError as e:
        raise ValueError(f"Error en validación de correo: {str(e)}")


def validate_password_complexity(password: Optional[str]) -> Optional[str]:
    """
    Valida complejidad de contraseña en actualizaciones.
    """
    if password is None:
        return None
    return BaseValidators.validate_password_complexity(password)


def validate_email_for_role(email: str, role: str) -> str:
    """
    Valida un email para un rol específico.
    Útil para validaciones en servicios antes de operaciones.
    """
    return BaseValidators.validate_email_domain(email, role)