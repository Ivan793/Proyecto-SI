# schemas/proyecto_schema.py
from pydantic import BaseModel
from typing import Optional
from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime
from app.core.constants import Limits
from app.core.enums import TipoActividadEnum
from app.schemas.types import TeacherId, StudentId, TeacherSubjectId


# ==================== SCHEMAS ====================

class EstudianteInfo(BaseModel):
    """Información de un estudiante vinculado al proyecto"""
    id_estudiante: StudentId = Field(..., min_length=3, description="ID del estudiante asignado")
    nombre: Optional[str] = Field(None, description="Nombre del estudiante")
    email: Optional[str] = Field(None, description="Correo del estudiante")


class ProyectoBase(BaseModel):
    """Datos base de un proyecto académico"""
    id_docente: TeacherId = Field(..., min_length=3, description="ID del docente que dirige el proyecto")
    id_estudiantes: List[EstudianteInfo] = Field(
        ..., 
        description="Lista de estudiantes vinculados al proyecto (mínimo 1)"
    )
    id_docente_materia: TeacherSubjectId = Field(..., description="ID de la relación docente-materia")
    id_grupo: str = Field(..., description="Identificador del grupo académico")
    id_area_tematica: str = Field(..., description="Identificador del área temática")
    id_evento: str = Field(..., description="Identificador del evento")
    id_materia: str = Field(..., description="Identificador de la materia asociada")
    codigo_linea: int = Field(..., description="Código de la línea de investigación (FK)")
    codigo_sublinea: Optional[int] = Field(None, description="Código de la sublínea de investigación (FK)")
    titulo_proyecto: str = Field(
        ..., 
        min_length=Limits.NAME_MIN, 
        max_length=150, 
        description="Título del proyecto"
    )
    tipo_actividad: TipoActividadEnum = Field(
        ...,
        description=(
            "Tipo de actividad académica asociada al proyecto. "
            "Opciones: 1=Exposoftware, 2=Taller, 3=Ponencia, 4=Conferencia, 5=Artículo Científico."
        )
    )
    formato_pdf: str = Field(
        default="PDF", 
        max_length=20, 
        description="Formato del archivo digital del proyecto"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_docente": "DOC001",
                "id_estudiantes": [
                    {"id_estudiante": "EST001", "nombre": "Juan Pérez", "email": "juan@example.com"}
                ],
                "id_docente_materia": "DOCMAT001",
                "id_grupo": "GRP001",
                "id_area_tematica": "AREA001",
                "id_evento": "EVT001",
                "id_materia": "MAT001",
                "codigo_linea": 101,
                "codigo_sublinea": 202,
                "titulo_proyecto": "Sistema de Gestión Académica",
                "tipo_actividad": 1,
                "formato_pdf": "PDF"
            }
        }
    }


class ProyectoCreate(ProyectoBase):
    """Datos necesarios para crear un proyecto"""
    fecha_subida: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha y hora de subida del proyecto (se asigna automáticamente)"
    )
    calificacion: Optional[float] = Field(
        None, 
        ge=0, 
        le=5, 
        description="Calificación asignada por el docente (0.0 a 5.0)"
    )


class ProyectoUpdate(BaseModel):
    """Campos opcionales al actualizar un proyecto"""
    titulo_proyecto: Optional[str] = Field(None, min_length=Limits.NAME_MIN, max_length=150)
    tipo_actividad: Optional[TipoActividadEnum] = None
    formato_pdf: Optional[str] = Field(None, max_length=20)
    calificacion: Optional[float] = Field(None, ge=0, le=5)
    id_evento: Optional[str] = None
    id_area_tematica: Optional[str] = None


class ProyectoResponse(ProyectoCreate):
    """Respuesta completa de un proyecto con todos sus datos"""
    id_proyecto: str = Field(..., max_length=30, description="Identificador único del proyecto (PK)")
    archivo_pdf: str = Field(..., description="URL o path del archivo PDF del proyecto")
    activo: bool = Field(default=True, description="Indica si el proyecto está activo")

    # Permitir que los estudiantes vengan como strings o como objetos
    @field_validator("id_estudiantes", mode="before")
    @classmethod
    def normalize_estudiantes(cls, value):
        """Normaliza la lista de estudiantes si vienen como strings"""
        if isinstance(value, list):
            if all(isinstance(v, str) for v in value):
                # Si vienen como ["EST001", "EST002"], convertirlos a objetos
                return [{"id_estudiante": v} for v in value]
        return value

    # Serializador: convierte el Enum en un nombre legible al devolver la respuesta
    @field_serializer("tipo_actividad")
    def serialize_tipo_actividad(self, v):
        """
        Convierte el enum de tipo_actividad a un nombre legible
        v: TipoActividadEnum
        Devuelve: "Exposoftware", "Ponencia", "Taller", etc.
        """
        try:
            # Si ya es enum, usamos name
            if isinstance(v, TipoActividadEnum):
                return v.name.replace("_", " ").title()
            # Si viene como int o str convertible a int, lo convertimos
            return TipoActividadEnum(int(v)).name.replace("_", " ").title()
        except Exception:
            # Fallback: devolver el valor tal cual (evita errores 500)
            return v

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id_proyecto": "PROY001",
                "id_docente": "DOC001",
                "id_estudiantes": [
                    {"id_estudiante": "EST001", "nombre": "Juan Pérez", "email": "juan@example.com"}
                ],
                "id_docente_materia": "DOCMAT001",
                "id_grupo": "GRP001",
                "id_area_tematica": "AREA001",
                "id_evento": "EVT001",
                "id_materia": "MAT001",
                "codigo_linea": 101,
                "codigo_sublinea": 202,
                "titulo_proyecto": "Sistema de Gestión Académica",
                "tipo_actividad": "Ponencia",
                "formato_pdf": "PDF",
                "archivo_pdf": "https://storage.firebase.com/proyecto001.pdf",
                "fecha_subida": "2025-10-17T15:00:00Z",
                "calificacion": 4.5,
                "activo": True
            }
        }
    }