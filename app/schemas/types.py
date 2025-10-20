from typing import Annotated
from pydantic import Field, EmailStr
from datetime import date

from app.core.constants import Limits, Defaults
from app.core.enums import Role, DocumentType, Gender, TeacherCategory, EventState, SubjectCycle
from app.core.patterns import Patterns

# ==================== TIPOS BASE ====================

UserId = Annotated[
    str, 
    Field(
        min_length=Limits.USER_ID_MIN, 
        max_length=Limits.USER_ID_MAX,
        description="Identificador único generado por el sistema"
    )
]

UserDocumentType = Annotated[
    DocumentType,
    Field(description="Tipo de documento del usuario")
]

UserIdentification = Annotated[
    str, 
    Field(
        min_length=Limits.IDENTIFICATION_MIN, 
        max_length=Limits.IDENTIFICATION_MAX,
        pattern=Patterns.IDENTIFICATION,
        description="Número de identificación oficial"
    )
]

UserName = Annotated[
    str, 
    Field(
        min_length=Limits.NAME_MIN, 
        max_length=Limits.NAME_MAX,
        pattern=Patterns.NAME,
        description="Nombre o apellido del usuario"
    )
]

UserGender = Annotated[
    Gender, 
    Field(description="Género del usuario")
]

UserSexualIdentity = Annotated[
    str,
    Field(
        min_length=Limits.SEXUAL_IDENTITY_MIN, 
        max_length=Limits.SEXUAL_IDENTITY_MAX,
        description="Identidad sexual del usuario"
    )
]

UserAddress = Annotated[
    str,
    Field(
        min_length=Limits.ADDRESS_MIN,
        max_length=Limits.ADDRESS_MAX,
        pattern=Patterns.ADDRESS,
        description="Dirección de residencia"
    )
]

UserCountry = Annotated[
    str,
    Field(
        min_length=Limits.COUNTRY_MIN,
        max_length=Limits.COUNTRY_MAX,
        description="País de origen"
    )
]

UserCity = Annotated[
    str,
    Field(
        min_length=Limits.CITY_MIN,
        max_length=Limits.CITY_MAX,
        description="Ciudad o municipio"
    )
]

UserPhone = Annotated[
    str,
    Field(
        pattern=Patterns.PHONE,
        min_length=Limits.MIN_PHONE_LENGTH,
        max_length=Limits.MAX_PHONE_LENGTH,
        description="Número de teléfono con prefijo opcional"
    )
]

UserEmail = Annotated[
    EmailStr,
    Field(
        max_length=Limits.MAX_EMAIL_LENGTH,
        description="Correo electrónico del usuario"
    )
]

UserPassword = Annotated[
    str,
    Field(
        min_length=Limits.PASSWORD_MIN,
        max_length=Limits.PASSWORD_MAX,
        description="Contraseña del usuario"
    )
]

UserRole = Annotated[
    Role,
    Field(description="Rol del usuario en el sistema")
]

# ==================== TIPOS DE DOCENTE ====================

TeacherCategoryType = Annotated[
    TeacherCategory,
    Field(description="Categoría del docente")
]

ProgramCode = Annotated[
    str, 
    Field(
        min_length=Limits.PROGRAM_CODE_MIN,
        max_length=Limits.PROGRAM_CODE_MAX,
        pattern=Patterns.PROGRAM_CODE,
        description="Código del programa académico"
    )
]

TeacherId = Annotated[
    str, 
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único del docente"
    )
]

# ==================== TIPOS DE EVENTO ====================

EventName = Annotated[
    str,
    Field(
        min_length=Limits.EVENT_NAME_MIN,
        max_length=Limits.EVENT_NAME_MAX,
        description="Nombre del evento o feria"
    )
]

EventDescription = Annotated[
    str,
    Field(
        max_length=Limits.EVENT_DESCRIPTION_MAX,
        description="Descripción detallada del evento"
    )
]

EventLocation = Annotated[
    str,
    Field(
        max_length=Limits.EVENT_LOCATION_MAX,
        description="Ubicación física del evento"
    )
]

EventCapacity = Annotated[
    int,
    Field(
        gt=Limits.EVENT_MIN_CAPACITY - 1,
        description="Número máximo de participantes permitidos"
    )
]

EventId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="ID único del evento"
    )
]

# ==================== TIPOS DE MATERIA ====================

SubjectName = Annotated[
    str,
    Field(
        min_length=Limits.SUBJECT_NAME_MIN,
        max_length=Limits.SUBJECT_NAME_MAX,
        description="Nombre descriptivo de la materia"
    )
]

SubjectCycleType = Annotated[
    SubjectCycle, 
    Field(description="Ciclo académico")
]

SubjectCode = Annotated[
    str,
    Field(
        max_length=Limits.SUBJECT_CODE_MAX,
        pattern=Patterns.PROGRAM_CODE,
        description="Código único de la materia"
    )
]

# ==================== TIPOS DE GRUPO ====================

GroupCode = Annotated[
    int,
    Field(
        gt=0,
        description="Código único del grupo"
    )
]

GroupName = Annotated[
    str,
    Field(
        min_length=2,
        max_length=50,
        description="Nombre descriptivo del grupo"
    )
]

# ==================== TIPOS DE ASIGNACIÓN DOCENTE-MATERIA ====================

TeacherSubjectId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="ID único de la asignación docente-materia"
    )
]

# ==================== TIPOS COMUNES ====================

ReasonText = Annotated[
    str,
    Field(
        min_length=Limits.REASON_MIN_LENGTH,
        max_length=Limits.REASON_MAX_LENGTH,
        description="Razón o motivo"
    )
]

SearchText = Annotated[
    str,
    Field(
        min_length=Limits.SEARCH_MIN_LENGTH,
        max_length=Limits.SEARCH_MAX_LENGTH,
        description="Término de búsqueda"
    )
]

StatusActive = Annotated[
    bool,
    Field(description="Estado activo/inactivo del registro")
]