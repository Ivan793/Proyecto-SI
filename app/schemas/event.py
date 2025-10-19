
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from datetime import timezone, datetime
from app.schemas.types import *
from app.core.constants import Defaults, ValidationMessages


# NOTA: Campos adicionales no presentes en el diccionario original
# - nombre_evento: Para identificar el evento (requerido según TAREA)
# - fecha_inicio: Fecha de inicio del evento (requerido según TAREA)
# - fecha_cierre/fecha_fin: Fecha de finalización (requerido según TAREA)
# - descripcion: Descripción del evento (requerido según TAREA)
# - lugar: Ubicación del evento (Esperar Confirmacion de la lider)
# - fotos: URLs o referencias a fotos (mencionado en TAREA)
# - cupo_maximo: Límite de participantes (Esperar Confirmacion de la lider)
# - permite_invitados: Si acepta invitados externos (mencionado en swagger)
# - estado: Estado del evento (ACTIVO, INACTIVO, FINALIZADO)
# - created_at/updated_at: Para auditorías (requerido en TAREA)


class EventBase(BaseModel):
    nombre_evento: EventName
    descripcion: Optional[EventDescription] = None
    fecha_inicio: datetime
    fecha_fin: datetime
    lugar: Optional[EventLocation] = None
    cupo_maximo: Optional[EventCapacity] = None
    permite_invitados: bool = Field(default=Defaults.EVENT_ALLOWS_GUESTS)

    @field_validator("nombre_evento", "descripcion", "lugar")
    @classmethod
    def validate_text_fields(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return v.strip()
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre_evento": "ExpoSoftware 2025-I",
                "descripcion": "Exposición de proyectos del primer semestre 2025",
                "fecha_inicio": "2025-05-15T08:00:00Z",
                "fecha_fin": "2025-05-17T18:00:00Z",
                "lugar": "Auditorio Principal UPC",
                "cupo_maximo": 150,
                "permite_invitados": True
            }
        }
    )


class EventCreate(EventBase):
    """Validaciones que solo aplican al crear o editar eventos"""
    @field_validator("fecha_inicio")
    @classmethod
    def validate_fecha_inicio(cls, v: datetime) -> datetime:
        now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
        if v < now:
            raise ValueError(ValidationMessages.PAST_DATE)
        return v
    
    @field_validator("fecha_fin")
    @classmethod
    def validate_fecha_fin(cls, v: datetime, info) -> datetime:
        fecha_inicio = info.data.get("fecha_inicio")
        if fecha_inicio and v <= fecha_inicio:
            raise ValueError(ValidationMessages.INVALID_DATE_RANGE)
        return v


class EventUpdate(BaseModel):
    """Esquema para actualizar un evento existente"""
    
    nombre_evento: Optional[EventName] = None
    descripcion: Optional[EventDescription] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    lugar: Optional[EventLocation] = None
    cupo_maximo: Optional[EventCapacity] = None
    estado: Optional[EventState] = None
    permite_invitados: Optional[bool] = None

    


class EventStateChange(BaseModel):
    estado: EventState
    razon: Optional[ReasonText] = None
    
    @field_validator("razon")
    @classmethod
    def validate_razon_when_inactive(cls, v: Optional[str], info) -> Optional[str]:
        estado = info.data.get("estado")
        if estado == EventState.INACTIVO and not v:
            raise ValueError(ValidationMessages.REQUIRED_REASON)
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estado": "INACTIVO",
                "razon": "Evento aplazado por situación climática"
            }
        }
    )


class EventResponse(EventBase):
    id_evento: EventId
    estado: EventState = Field(default=EventState.ACTIVO)
    total_inscritos: int = Field(default=0, ge=0)
    total_proyectos: int = Field(default=0, ge=0)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True,validate_assignment=False)


class EventSummary(BaseModel):
    """Resumen de evento para listados"""
    
    id_evento: EventId
    nombre_evento: EventName
    fecha_inicio: datetime
    fecha_fin: datetime
    estado: EventState
    total_inscritos: int = 0
    total_proyectos: int = 0
    
    model_config = ConfigDict(from_attributes=True,validate_assignment=False)