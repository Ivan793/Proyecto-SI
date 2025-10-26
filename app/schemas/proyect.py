from __future__ import annotations
from pydantic import BaseModel, Field, field_serializer
from typing import Optional
from datetime import datetime
from app.core.enums import TipoActividadEnum
from app.schemas.types import TeacherId, StudentId,TeacherSubjectId, SubResearchLineCode


class ProyectoBase(BaseModel):
    id_docente: TeacherId
    id_estudiante: StudentId
    id_docente_materia: TeacherSubjectId
    codigo_linea: int = Field(..., description="Código de la línea de investigación (FK)")
    codigo_sublinea: int = Field(..., description="Código de la sublínea de investigación (FK)")
    titulo_proyecto: str = Field(..., min_length=3, max_length=60, description="Título del proyecto")
    tipo_actividad: TipoActividadEnum = Field(
        ...,
        description=(
            "Tipo de actividad académica asociada al proyecto. "
            "Opciones: 1=Exposoftware, 2=Taller, 3=Ponencia, 4=Conferencia, 5=Artículo Científico."
        )
    )
    formato_pdf: str = Field(..., max_length=20, description="Formato del archivo digital del proyecto (por ejemplo, 'PDF')")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_docente": "DOC001",
                "id_estudiante": "EST001",
                "id_docente_materia": "DOCMAT001",
                "codigo_linea": 101,
                "codigo_sublinea": 202,
                "titulo_proyecto": "Sistema de Gestión Académica",
                "tipo_actividad": 1,
                "formato_pdf": "PDF"
            }
        }
    }


class ProyectoCreate(ProyectoBase):
    fecha_subida: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha y hora de subida del proyecto (se asigna automáticamente)"
    )
    calificacion: Optional[str] = Field(
        None, max_length=3, description="Calificación asignada por el docente (Ej: '4.5')"
    )


class ProyectoUpdate(BaseModel):
    titulo_proyecto: Optional[str] = Field(None, min_length=3, max_length=60)
    tipo_actividad: Optional[TipoActividadEnum] = None
    formato_pdf: Optional[str] = Field(None, max_length=20)
    calificacion: Optional[str] = Field(None, max_length=3)


class ProyectoResponse(ProyectoCreate):
    id_proyecto: str = Field(..., max_length=30, description="Identificador único del proyecto (PK)")

    # Serializador: convierte el Enum (o el int) en un nombre legible al devolver la respuesta
    @field_serializer("tipo_actividad")
    def serialize_tipo_actividad(self, v):
        """
        v suele ser un TipoActividadEnum (por la validación de Pydantic),
        pero por seguridad manejamos también int/str.
        Devuelve: "Ponencia", "Taller", etc.
        """
        try:
            # Si ya es enum, usamos name
            if isinstance(v, TipoActividadEnum):
                return v.name.replace("_", " ").title()
            # Si viene como int o str convertible a int, lo convertimos
            return TipoActividadEnum(int(v)).name.replace("_", " ").title()
        except Exception:
            # Fallback: devolver el valor tal cual (evita 500s)
            return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "id_proyecto": "001",
                "id_docente": "DOC001",
                "id_estudiante": "EST001",
                "id_docente_materia": "DOCMAT001",
                "codigo_linea": 101,
                "codigo_sublinea": 202,
                "titulo_proyecto": "Sistema de Gestión Académica",
                "tipo_actividad": "Ponencia",
                "formato_pdf": "PDF",
                "fecha_subida": "2025-10-17T15:00:00Z",
                "calificacion": "4.5"
            }
        }
    }
