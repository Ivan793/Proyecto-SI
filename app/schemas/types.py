from typing import Annotated
from pydantic import Field, EmailStr
from datetime import date, datetime

from app.core.constants import Limits, Defaults
from app.core.enums import Role, DocumentType, Sex, TeacherCategory, EventState, SubjectCycle
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

UserSex = Annotated[
    Sex, 
    Field(description="Sexo del usuario")
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

UserDepartment = Annotated[
    str,
    Field(
        min_length=Limits.DEPARTMENT_MIN,
        max_length=Limits.DEPARTMENT_MAX,
        description="Departamento del usuario"
    )
]

UserMunicipality = Annotated[
    str,
    Field(
        min_length=Limits.MUNICIPALITY_MIN,
        max_length=Limits.MUNICIPALITY_MAX,
        pattern=Patterns.NAME,
        description="Municipio de residencia"
    )
]

UserNationality = Annotated[
    str,
    Field(
        min_length=Limits.NATIONALITY_MIN,
        max_length=Limits.NATIONALITY_MAX,
        pattern=Patterns.NAME,
        description="Nacionalidad del usuario"
    )
]

UserCity = Annotated[
    str,
    Field(
        min_length=2,
        max_length=50,
        pattern=Patterns.NAME,
        description="Ciudad de residencia"
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

# ==================== TIPOS DE FACULTAD ====================

FacultyId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único de la facultad"
    )
]

FacultyName = Annotated[
    str,
    Field(
        max_length=50,
        description="Nombre de la facultad"
    )
]

# ==================== TIPOS DE PROGRAMA ACADÉMICO ====================

ProgramCode = Annotated[
    str, 
    Field(
        min_length=Limits.PROGRAM_CODE_MIN,
        max_length=Limits.PROGRAM_CODE_MAX,
        pattern=Patterns.PROGRAM_CODE,
        description="Código del programa académico"
    )
]

ProgramName = Annotated[
    str,
    Field(
        max_length=40,
        description="Nombre del programa académico"
    )
]

# ==================== TIPOS DE DOCENTE ====================

TeacherCategoryType = Annotated[
    TeacherCategory,
    Field(description="Categoría del docente")
]

TeacherId = Annotated[
    str, 
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único del docente"
    )
]

# ==================== TIPOS DE ESTUDIANTE ====================

StudentId = Annotated[
    str, 
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único del estudiante"
    )
]

StudentCode = Annotated[
    str,
    Field(
        min_length=3,
        max_length=20,
        description="Código del estudiante dentro del programa académico"
    )
]

Semester = Annotated[
    int,
    Field(
        ge=1, le=20,
        description="Semestre actual del estudiante"
    )
]

YearOfEntry = Annotated[
    int,
    Field(
        ge=2000, le=2100,
        description="Año de ingreso del estudiante"
    )
]

period = Annotated[
    int,
    Field(
        ge=1, le=2,
        description= "periodo académico que ingreso el usuario a la institución es 1 o 2."
    )
]

# ==================== TIPOS DE EGRESADO ====================

GraduateId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único del egresado"
    )
]

AcademicProgram = Annotated[
    str,
    Field(
        min_length=3,
        description="Programa académico cursado"
    )
]

GraduationYear = Annotated[
    int,
    Field(
        ge=1900, le=datetime.now().year,
        description="Año de graduación"
    )
]

DegreeTitle = Annotated[
    str,
    Field(
        min_length=3,
        description="Título obtenido por el egresado"
    )
]

# ==================== TIPOS DE INVITADO ====================

GuestId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único del invitado"
    )
]

Institution = Annotated[
    str,
    Field(
        description="Institución del invitado"
    )
]

VisitReason = Annotated[
    str,
    Field(
        description="Motivo de la visita"
    )
]

# ==================== TIPOS DE SECTOR ====================

SectorId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único del sector"
    )
]

SectorName = Annotated[
    str,
    Field(
        max_length=25,
        description="Nombre del sector"
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
    str,
    Field(
        min_length=1,
        max_length=10,
        pattern=r"^[0-9]+$",
        description="Código único del grupo (números)"
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

# ==================== TIPOS DE INSCRIPCIÓN ESTUDIANTE-MATERIA ====================

StudentSubjectId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único de la inscripción estudiante-materia"
    )
]

# ==================== TIPOS DE ASISTENCIA ====================

AttendanceId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador único de la asistencia"
    )
]

ProjectId = Annotated[
    str,
    Field(
        min_length=Limits.USER_ID_MIN,
        max_length=Limits.USER_ID_MAX,
        description="Identificador del proyecto"
    )
]

AttendanceDateTime = Annotated[
    datetime,
    Field(
        description="Fecha y hora exacta de la asistencia"
    )
]

# ==================== TIPOS DE LÍNEA DE INVESTIGACIÓN ====================

ResearchLineCode = Annotated[
    int,
    Field(
        description="Código de la línea de investigación (1 o 2)"
    )
]

ResearchLineName = Annotated[
    str,
    Field(
        min_length=Limits.RESEARCH_LINE_NAME_MIN,
        max_length=Limits.RESEARCH_LINE_NAME_MAX,
        description="Nombre de la línea de investigación"
    )
]

# ==================== TIPOS DE SUBLÍNEA DE INVESTIGACIÓN ====================

SubResearchLineCode = Annotated[
    int,
    Field(
        gt=0,
        description="Código único de la sublínea de investigación"
    )
]

SubResearchLineName = Annotated[
    str,
    Field(
        min_length=Limits.RESEARCH_LINE_NAME_MIN,
        max_length=Limits.RESEARCH_LINE_NAME_MAX,
        description="Nombre de la sublínea de investigación"
    )
]

# ==================== TIPOS DE ÁREA TEMÁTICA ====================

ThematicAreaCode = Annotated[
    int,
    Field(
        gt=0,
        description="Código único del área temática"
    )
]

ThematicAreaName = Annotated[
    str,
    Field(
        min_length=Limits.RESEARCH_LINE_NAME_MIN,
        max_length=Limits.RESEARCH_LINE_NAME_MAX,
        description="Nombre del área temática"
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

# ==================== TIPOS DE FACULTAD ====================

FacultyId = Annotated[
    str,
    Field(
        min_length=Limits.FACULTY_ID_MIN,
        max_length=Limits.FACULTY_ID_MAX,
        pattern=Patterns.FACULTY_ID,
        description="Código único de la facultad (Ej: FAC_ING, FAC_EDU)"
    )
]

FacultyName = Annotated[
    str,
    Field(
        min_length=Limits.NAME_MIN,
        max_length=100,
        pattern=Patterns.NAME,
        description="Nombre completo de la facultad"
    )
]

