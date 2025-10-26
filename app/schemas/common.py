"""Esquemas comunes para respuestas estandarizadas y utilidades"""
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Any, Dict
from datetime import datetime, timezone

from app.core.constants import Limits, Defaults
from app.core.response_codes import ResponseCode, ResponseMessage

# ==================== PAGINACIÓN ====================

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Número de página")
    limit: int = Field(
        default=Defaults.PAGINATION_LIMIT, 
        ge=1, 
        le=Defaults.PAGINATION_MAX,
        description="Elementos por página"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "page": 1,
                "limit": 20
            }
        }
    }


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
    status: str = Field(default="success", description="Estado de la respuesta")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")
    data: T = Field(..., description="Datos de la respuesta")
    code: str = Field(default=ResponseCode.SUCCESS, description="Código de respuesta")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Operación realizada exitosamente",
                "data": {
                    "id": "abc123",
                    "nombre": "Ejemplo"
                },
                "code": "SUCCESS"
            }
        }
    }


class PaginatedResponse(BaseModel, Generic[T]):
    status: str = Field(default="success", description="Estado de la respuesta")
    message: Optional[str] = Field(None, description="Mensaje descriptivo")
    data: List[T] = Field(..., description="Lista de elementos")
    pagination: PaginationMeta = Field(..., description="Información de paginación")
    code: str = Field(default=ResponseCode.SUCCESS, description="Código de respuesta")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Datos obtenidos correctamente",
                "data": [
                    {"id": "1", "nombre": "Elemento 1"},
                    {"id": "2", "nombre": "Elemento 2"}
                ],
                "pagination": {
                    "page": 1,
                    "limit": 20,
                    "total_items": 150,
                    "total_pages": 8,
                    "has_next": True,
                    "has_prev": False
                },
                "code": "SUCCESS"
            }
        }
    }


class ErrorDetail(BaseModel):
    field: Optional[str] = Field(None, description="Campo que causó el error")
    message: str = Field(..., description="Mensaje de error")
    type: Optional[str] = Field(None, description="Tipo de error")
    value: Optional[Any] = Field(None, description="Valor que causó el error")

    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "correo",
                "message": "El formato del correo es inválido",
                "type": "value_error.email",
                "value": "correo_invalido"
            }
        }
    }


class ErrorResponse(BaseModel):
    status: str = Field(default="error", description="Estado de error")
    message: str = Field(..., description="Mensaje de error general")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Lista de errores detallados")
    code: str = Field(..., description="Código de error específico")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    path: Optional[str] = Field(None, description="Endpoint donde ocurrió el error")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "error",
                "message": "Datos de entrada inválidos",
                "errors": [
                    {
                        "field": "correo",
                        "message": "El formato del correo es inválido",
                        "type": "value_error.email",
                        "value": "correo_invalido"
                    }
                ],
                "code": "VALIDATION_ERROR",
                "timestamp": "2025-01-15T10:30:00Z",
                "path": "/api/v1/usuarios"
            }
        }
    }


# ==================== RESPUESTAS ESPECÍFICAS ====================

class MessageResponse(BaseModel):
    status: str = Field(default="success", description="Estado de la respuesta")
    message: str = Field(..., description="Mensaje informativo")
    code: str = Field(default=ResponseCode.SUCCESS, description="Código de respuesta")

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "message": "Operación realizada exitosamente",
                "code": "SUCCESS"
            }
        }
    }


class IdResponse(BaseModel):
    id: str = Field(..., description="ID del recurso creado")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "L7Tz5A23fWx19oK9jK1a"
            }
        }
    }


class CountResponse(BaseModel):
    count: int = Field(..., description="Cantidad de elementos")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "count": 42
            }
        }
    }


class BulkOperationResult(BaseModel):
    processed: int = Field(..., description="Elementos procesados")
    successful: int = Field(..., description="Operaciones exitosas")
    failed: int = Field(..., description="Operaciones fallidas")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Errores detallados")

    model_config = {
        "json_schema_extra": {
            "example": {
                "processed": 10,
                "successful": 8,
                "failed": 2,
                "errors": [
                    {"item": "item1", "error": "Ya existe"},
                    {"item": "item2", "error": "Formato inválido"}
                ]
            }
        }
    }