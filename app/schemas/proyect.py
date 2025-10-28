from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.core.constants import Limits
from app.core.enums import TipoActividadEnum
from app.schemas.types import TeacherId, UserId
# ==================== SCHEMAS ====================

class EstudianteInfo(BaseModel):
    id_estudiante: str = Field(..., min_length=3, description="ID del estudiante asignado")
    nombre: Optional[str] = Field(None, description="Nombre del estudiante")
    email: Optional[str] = Field(None, description="Correo del estudiante")



class ProyectoBase(BaseModel):
    id_docente: str = Field(..., min_length=3, description="ID del docente que dirige el proyecto")
    id_estudiantes: List[EstudianteInfo] = Field(
        ..., 
        description="Lista de estudiantes vinculados al proyecto (mínimo 1)"
    )
    id_grupo: int = Field(..., description="Identificador del grupo académico")
    codigo_area: int = Field(..., description="Identificador del área temática")
    id_evento: str = Field(..., description="Identificador del evento")
    id_materia: str = Field(..., description="Identificador de la materia asociada")
    codigo_linea: Union[str, int] = Field(..., description="Código de la línea de investigación")
    codigo_sublinea: Optional[int] = Field(None, description="Código de la sublínea")
    titulo_proyecto: str = Field(
        ..., 
        min_length=Limits.NAME_MIN, 
        max_length=150, 
        description="Título del proyecto"
    )
    tipo_actividad: TipoActividadEnum = Field(..., description="Tipo de actividad académica que se toma con enum: exposoftware = 1, taller = 2, ponencia = 3, conferencia = 4, articulo_cientifico = 5")
    calificacion: Optional[float] = Field(None, ge=0, le=5, description="Calificación del proyecto")


class ProyectoCreate(ProyectoBase):
    """Datos necesarios para crear un proyecto (PDF obligatorio)"""
    pass


class ProyectoUpdate(BaseModel):
    """Campos opcionales al actualizar un proyecto"""
    titulo_proyecto: Optional[str] = None
    tipo_actividad: Optional[str] = None
    calificacion: Optional[float] = None
    id_evento: Optional[str] = None
    id_area_tematica: Optional[str] = None


class ProyectoResponse(ProyectoBase):
    id_proyecto: str
    archivo_pdf: str
    fecha_subida: datetime
    activo: bool = True

    # Permitir que los estudiantes vengan como strings o como objetos
    @field_validator("id_estudiantes", mode="before")
    @classmethod
    def normalize_estudiantes(cls, value):
        if isinstance(value, list):
            if all(isinstance(v, str) for v in value):
                # Si vienen como ["EST001", "EST002"], convertirlos
                return [{"id_estudiante": v} for v in value]
        return value

    class Config:
        from_attributes = True