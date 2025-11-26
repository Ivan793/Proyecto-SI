from typing import List, Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from app.core.constants import Limits
from app.core.enums import TipoActividadEnum

# ==================== SCHEMAS ====================

class EstudianteInfo(BaseModel):
    id_estudiante: str = Field(..., min_length=3, description="ID del estudiante asignado")
    nombre: Optional[str] = Field(None, description="Nombre del estudiante")

class DocenteInfo(BaseModel):
    uid_docente: str = Field(..., min_length=1, description="ID del docente asignado")
    nombre: Optional[str] = Field(None, description="Nombre del docente")


class ProyectoBase(BaseModel):
    # Cambiar a Union para aceptar objeto vacío o con datos
    id_docente: Optional[Union[DocenteInfo, dict]] = Field(None, description="ID del docente (opcional para egresados)")
    id_estudiantes: Union[List[EstudianteInfo], List[dict], str] = Field(
        ..., 
        description="Lista de estudiantes vinculados al proyecto (mínimo 1)"
    )
    id_grupo: Optional[str] = Field(None, description="Identificador del grupo académico (opcional para egresados)")
    codigo_area: int = Field(..., description="Identificador del área temática")
    id_evento: str = Field(..., description="Identificador del evento")
    codigo_materia: Optional[str] = Field(None, description="Identificador de la materia asociada (opcional para egresados)")
    codigo_linea: int = Field(..., description="Código de la línea de investigación")
    codigo_sublinea: Optional[int] = Field(None, description="Código de la sublínea")
    titulo_proyecto: str = Field(
        ..., 
        min_length=Limits.NAME_MIN, 
        max_length=150, 
        description="Título del proyecto"
    )
    tipo_actividad: TipoActividadEnum = Field(..., description="Tipo de actividad académica que se toma con enum: exposoftware = 1, taller = 2, ponencia = 3, conferencia = 4, articulo_cientifico = 5")
    estado_calificacion: Optional[str] = Field(default="pendiente")
    calificacion: Optional[float] = Field(default=None, ge=0, le=5)
    es_egresado: Optional[bool] = Field(default=False, description="Indica si el proyecto es de un egresado")

    @field_validator("id_docente", mode="before")
    @classmethod
    def validate_docente(cls, value):
        """Normaliza el docente - permite objeto vacío o None"""
        if value is None:
            return None
        if isinstance(value, dict):
            # Si viene {"uid_docente": ""} lo convertimos a None
            uid = value.get("uid_docente", "")
            if not uid or uid.strip() == "":
                return None
            # Si tiene datos válidos, dejarlo pasar
            return value
        return value

    @field_validator("id_estudiantes", mode="before")
    @classmethod
    def validate_estudiantes(cls, value):
        """Normaliza la lista de estudiantes"""
        # Si viene como string JSON
        if isinstance(value, str):
            try:
                import json
                value = json.loads(value)
            except:
                raise ValueError("El campo 'id_estudiantes' debe ser un JSON válido")
        
        # Si viene como lista de strings, convertir a lista de dicts
        if isinstance(value, list):
            if all(isinstance(v, str) for v in value):
                return [{"id_estudiante": v} for v in value]
        
        return value


class ProyectoCreate(ProyectoBase):
    """Datos necesarios para crear un proyecto (PDF obligatorio)"""
    pass


class ProyectoUpdate(BaseModel):
    titulo_proyecto: Optional[str] = None
    tipo_actividad: Optional[str] = None
    calificacion: Optional[float] = Field(None, ge=0, le=5)
    id_evento: Optional[str] = None
    codigo_area: Optional[str] = None

    @field_validator("calificacion")
    @classmethod
    def validar_estado_calificacion(cls, value, info):
        # Solo actualizar estado_calificacion si el valor no es None
        if value is not None:
            if value >= 3:
                info.data["estado_calificacion"] = "aprobado"
            else:
                info.data["estado_calificacion"] = "reprobado"
        return value


class ProyectoResponse(ProyectoBase):
    id_proyecto: str
    archivo_pdf: str
    fecha_subida: datetime
    activo: bool = True

    # Campos extra para mostrar nombres
    nombre_area: Optional[str] = None
    nombre_linea: Optional[str] = None
    nombre_sublinea: Optional[str] = None

    # Normalizador de estudiantes
    @field_validator("id_estudiantes", mode="before")
    @classmethod
    def normalize_estudiantes(cls, value):
        if isinstance(value, list):
            if all(isinstance(v, str) for v in value):
                return [{"id_estudiante": v} for v in value]
        return value

    class Config:
        from_attributes = True