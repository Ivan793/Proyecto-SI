"""
Constantes y configuraciones centralizadas del sistema
"""
from enum import Enum

class Limits:
    """Límites de longitud y validaciones numéricas generales."""
    
    # Email
    MAX_EMAIL_LENGTH = 40
    
    # Teléfono
    MIN_PHONE_LENGTH = 7
    MAX_PHONE_LENGTH = 15
    
    # Contraseña
    PASSWORD_MIN = 8
    PASSWORD_MAX = 12
    
    # Nombres y apellidos
    NAME_MIN = 2
    NAME_MAX = 50
    
    # Identificación
    IDENTIFICATION_MIN = 6
    IDENTIFICATION_MAX = 16
    
    # Dirección
    ADDRESS_MIN = 5
    ADDRESS_MAX = 100
    
    # País
    COUNTRY_MIN = 2
    COUNTRY_MAX = 50
    
    # Ciudad
    CITY_MIN = 2
    CITY_MAX = 50
    DEPARTMENT_MIN = 2
    DEPARTMENT_MAX = 50
    MUNICIPALITY_MIN = 2
    MUNICIPALITY_MAX = 50
    NATIONALITY_MIN = 2
    NATIONALITY_MAX = 50
    
    # Categoría docente
    TEACHER_CATEGORY_MAX = 30
    
    # Código de programa
    PROGRAM_CODE_MIN = 3
    PROGRAM_CODE_MAX = 15
    
    # User ID
    USER_ID_MIN = 10
    USER_ID_MAX = 30

    # Facultad ID
    FACULTY_ID_MIN =3
    FACULTY_ID_MAX =10

    # Materia
    SUBJECT_NAME_MIN = 3
    SUBJECT_NAME_MAX = 100
    SUBJECT_CODE_MAX = 8
    CYCLE_NAME_MAX = 25
    
    # Eventos
    EVENT_NAME_MIN = 3
    EVENT_NAME_MAX = 100
    EVENT_DESCRIPTION_MAX = 500
    EVENT_LOCATION_MAX = 100
    EVENT_MIN_CAPACITY = 1
    
    # Razones y motivos
    REASON_MIN_LENGTH = 10
    REASON_MAX_LENGTH = 200
    
    # Búsqueda
    SEARCH_MIN_LENGTH = 1
    SEARCH_MAX_LENGTH = 100

    SEXUAL_IDENTITY_MIN = 3
    SEXUAL_IDENTITY_MAX = 20

    PAGINATION_PAGE = 1


class Defaults:
    """Valores por defecto del sistema."""
    PAGINATION_PAGE = 1
    PAGINATION_LIMIT = 20
    PAGINATION_MAX = 100
    ACTIVE_STATUS = True
    DEFAULT_LANGUAGE = "es"
    DEFAULT_EVENT_STATE = "ACTIVO"
    ACTIVE_STATUS = True


class ValidationMessages:
    """Mensajes de error para validaciones."""
    
    # Longitud
    MIN_LENGTH = "El campo debe tener al menos {min} caracteres"
    MAX_LENGTH = "El campo no puede exceder {max} caracteres"
    EXACT_LENGTH = "El campo debe tener exactamente {length} caracteres"
    
    # Formato
    INVALID_FORMAT = "El formato del campo es inválido"
    INVALID_EMAIL = "El correo electrónico no es válido"
    INVALID_INSTITUTIONAL_EMAIL = "Se requiere correo institucional (@unicesar.edu.co) para roles Docente o Estudiante"
    INVALID_PHONE = "El número de teléfono no es válido (debe ser +573001234567)"
    INVALID_PASSWORD = "La contraseña debe contener mayúsculas, minúsculas, números y caracteres especiales"
    INVALID_NAME = "El nombre solo puede contener letras y espacios"
    INVALID_IDENTIFICATION = "La identificación solo puede contener letras y números"
    INVALID_ADDRESS = "La dirección contiene caracteres no permitidos"

    # Fechas
    INVALID_DATE_RANGE = "La fecha de finalización debe ser posterior a la fecha de inicio"
    PAST_DATE = "La fecha no puede ser anterior a hoy"
    
    # Requerido
    REQUIRED_FIELD = "Este campo es obligatorio"
    REQUIRED_REASON = "Debe proporcionar una razón al desactivar"
    
    # Opciones
    INVALID_OPTION = "El valor seleccionado no es válido"
    
    # Estados
    INVALID_STATE_CHANGE = "El cambio de estado no es válido"
    
    # Dominios institucionales
    INSTITUTIONAL_EMAIL_REQUIRED = "Los usuarios con rol '{role}' deben tener correo institucional ({domains})"
    INVALID_EMAIL_DOMAIN = "El dominio del correo no está permitido para el rol {role}"


class EmailDomains:
    """Configuración centralizada de dominios de correo permitidos por rol."""
    
    # Dominios permitidos por rol - FÁCILMENTE CONFIGURABLE
    ALLOWED_DOMAINS = {
        "DOCENTE": ["@unicesar.edu.co", "@prof.unicesar.edu.co"],
        "ESTUDIANTE": ["@unicesar.edu.co", "@est.unicesar.edu.co"],
        "ADMINISTRATIVO": ["@unicesar.edu.co"],
        "INVITADO": ["*"],  # Cualquier dominio permitido
        "EGRESADO": ["*"]   # Cualquier dominio permitido
    }
    
    @classmethod
    def get_allowed_domains(cls, role: str) -> list:
        """Obtiene los dominios permitidos para un rol específico."""
        return cls.ALLOWED_DOMAINS.get(role.upper(), ["*"])
    
    @classmethod
    def is_domain_allowed(cls, email: str, role: str) -> bool:
        """Verifica si un dominio está permitido para el rol."""
        domains = cls.get_allowed_domains(role)
        
        # Si permite cualquier dominio
        if "*" in domains:
            return True
            
        # Verificar dominios específicos
        return any(email.lower().endswith(domain.lower()) for domain in domains)
    
    @classmethod
    def add_domain_for_role(cls, role: str, domain: str):
        """Agrega un nuevo dominio para un rol (para extensibilidad)."""
        if role.upper() not in cls.ALLOWED_DOMAINS:
            cls.ALLOWED_DOMAINS[role.upper()] = []
        
        if domain not in cls.ALLOWED_DOMAINS[role.upper()]:
            cls.ALLOWED_DOMAINS[role.upper()].append(domain)