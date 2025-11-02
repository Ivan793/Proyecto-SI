from enum import Enum, IntEnum
from enum import IntEnum

class TipoActividadEnum(IntEnum):
    exposoftware = 1
    taller = 2
    ponencia = 3
    conferencia = 4
    articulo_cientifico = 5


class Role(str, Enum):
    DOCENTE = "Docente"
    ESTUDIANTE = "Estudiante"
    INVITADO = "Invitado"
    EGRESADO = "Egresado"
    ADMINISTRATIVO = "Administrativo"


class TeacherCategory(str, Enum):
    INTERNO = "Interno"
    INVITADO = "Invitado"
    EXTERNO = "Externo"


class EventState(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    FINALIZADO = "FINALIZADO"

class DocumentType(str, Enum):
    CC = "CC"  # Cédula de Ciudadanía
    TI = "TI"  # Tarjeta de Identidad
    CE = "CE"  # Cédula de Extranjería
    PTE = "PTE"  # Permiso Temporal de Estadía
    PAS = "PAS"  # Pasaporte


class Sex(str, Enum):
    HOMBRE = "Hombre"
    MUJER = "Mujer"
    HERMAFRODITA = "Hermafrodita"


class SubjectCycle(str, Enum):
    BASICO = "Ciclo Básico"
    PROFESIONAL = "Ciclo Profesional"
    PROFUNDIZACION = "Ciclo de Profundización"

class TipoActividadEnum(IntEnum):
    exposoftware = 1
    taller = 2
    ponencia = 3
    conferencia = 4
    articulo_cientifico = 5

class Sector(IntEnum):
    EDUCATIVO = 1
    EMPRESARIAL = 2
    SOCIAL = 3
    GOBIERNO = 4
