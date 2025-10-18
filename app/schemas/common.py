"""Esquemas comunes para respuestas estandarizadas y utilidades"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Any, Dict
from datetime import datetime, timezone

from app.core.constants import Limits, Defaults

# ==================== PAGINACIÓN ====================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=Defaults.PAGINATION_LIMIT, ge=1, le=Defaults.PAGINATION_MAX)


class PaginationMeta(BaseModel):
    """Metadata de paginación"""
    
    page: int = Field(..., description="Página actual")
    limit: int = Field(..., description="Elementos por página")
    total_items: int = Field(..., description="Total de elementos")
    total_pages: int = Field(..., description="Total de páginas")
    has_next: bool = Field(..., description="Tiene página siguiente")
    has_prev: bool = Field(..., description="Tiene página anterior")

    model_config = {
        "json_schema_extra": {
            "example": {
                "page": 1,
                "limit": 20,
                "total_items": 150,
                "total_pages": 8,
                "has_next": True,
                "has_prev": False
            }
        }
    }


# RESPUESTAS GENÉRICAS

T = TypeVar('T')


class SuccessResponse(BaseModel, Generic[T]):
    status: str = Field(default="success")
    message: Optional[str] = None
    data: T

    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel, Generic[T]):
    status: str = Field(default="success")
    data: List[T] = Field(..., description="Lista de elementos")
    pagination: PaginationMeta
    model_config = {"from_attributes": True}


class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None, description="Campo que causó el error")
    message: str    
    type: Optional[str] = Field(None, description="Tipo de error")


class ErrorResponse(BaseModel):
    status: str = Field(default="error")
    message: str
    errors: Optional[List[ErrorDetail]] = Field(None, description="Lista de errores detallados")
    code: Optional[str] = Field(None, description="Código de error específico")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "error",
                "message": "Datos de entrada inválidos",
                "errors": [
                    {
                        "field": "correo",
                        "message": "El formato del correo es inválido",
                        "type": "value_error.email"
                    }
                ],
                "code": "VALIDATION_ERROR",
                "timestamp": "2025-01-15T10:30:00Z"
            }
        }
    }


# ==================== AUDITORÍA ====================

class AuditInfo(BaseModel):
    realizado_por: str = Field(..., description="ID del usuario que realizó la acción")
    realizado_por_nombre: str = Field(..., description="Nombre del usuario")
    fecha: datetime = Field(default_factory=datetime.utcnow, description="Fecha y hora de la acción")
    accion: str = Field(..., description="Tipo de acción realizada")
    detalles: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")

    model_config = {
        "json_schema_extra": {
            "example": {
                "realizado_por": "admin_001",
                "realizado_por_nombre": "Administrador Principal",
                "fecha": "2025-01-15T10:30:00Z",
                "accion": "APROBACION",
                "detalles": {
                    "estado_anterior": "PENDIENTE",
                    "estado_nuevo": "APROBADO"
                }
            }
        }
    }


class ChangeAudit(BaseModel):
    cambio_realizado_por: str
    cambio_realizado_por_nombre: str
    fecha_cambio: datetime = Field(default_factory=datetime.now(timezone.utc))
    cambio_anterior: Optional[Dict[str, Any]] = None
    cambio_nuevo: Optional[Dict[str, Any]] = None
    razon: Optional[str] = Field(None, min_length=Limits.REASON_MIN_LENGTH, max_length=Limits.REASON_MAX_LENGTH)


class ApprovalAudit(BaseModel):
    aprobado_por: str
    aprobado_por_nombre: str
    fecha_aprobacion: datetime = Field(default_factory=datetime.now(timezone.utc))
    estado_anterior: str
    estado_nuevo: str = "APROBADO"


class RejectionAudit(BaseModel):
    rechazado_por: str
    rechazado_por_nombre: str
    fecha_rechazo: datetime = Field(default_factory=datetime.now(timezone.utc))
    estado_anterior: str
    estado_nuevo: str = "RECHAZADO"
    motivo_rechazo: str = Field(..., min_length=Limits.REASON_MIN_LENGTH, max_length=Limits.REASON_MAX_LENGTH)


# ==================== FILTROS ====================

class DateRangeFilter(BaseModel):
    fecha_desde: Optional[datetime] = None
    fecha_hasta: Optional[datetime] = None


class SearchFilter(BaseModel):
    search: Optional[str] = Field(None, min_length=Limits.SEARCH_MIN_LENGTH, max_length=Limits.SEARCH_MAX_LENGTH)


# ==================== ESTADÍSTICAS ====================

class CountStats(BaseModel):
    total: int = Field(..., description="Total de elementos")
    activos: int = Field(default=0, description="Elementos activos")
    inactivos: int = Field(default=0, description="Elementos inactivos")
    pendientes: int = Field(default=0, description="Elementos pendientes")


class PercentageDistribution(BaseModel):
    categoria: str = Field(..., description="Nombre de la categoría")
    cantidad: int = Field(..., description="Cantidad de elementos")
    porcentaje: float = Field(..., ge=0, le=100, description="Porcentaje del total")


# ==================== MENSAJES ====================

class MessageResponse(BaseModel):
    status: str = Field(default="success")
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Operación realizada exitosamente"
            }
        }
    }


# ==================== TIPOS DE ESTADO ====================

class StatusInfo(BaseModel):
    codigo: str = Field(..., description="Código del estado")
    nombre: str = Field(..., description="Nombre descriptivo")
    descripcion: Optional[str] = Field(None, description="Descripción del estado")
    color: Optional[str] = Field(None, description="Color asociado (para UI)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "codigo": "ACTIVO",
                "nombre": "Activo",
                "descripcion": "El elemento está activo y operativo",
                "color": "#28a745"
            }
        }
    }