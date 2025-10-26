"""
Utilidades para documentación automática de Swagger
"""
from typing import Dict, Any, List, Optional, Type
from functools import wraps
from fastapi import HTTPException
import inspect

from app.core.swagger_config import get_response_example
from app.core.response_codes import ResponseCode


def api_response(
    success_model: Optional[Type] = None,
    success_description: str = "Respuesta exitosa",
    error_codes: Optional[List[int]] = None,
    error_descriptions: Optional[Dict[int, str]] = None
):
    """
    Decorador para documentar respuestas API de forma consistente
    """
    default_errors = {
        400: "Solicitud incorrecta",
        401: "No autorizado", 
        403: "Prohibido",
        404: "No encontrado",
        409: "Conflicto",
        422: "Error de validación",
        429: "Límite de tasa excedido",
        500: "Error interno del servidor"
    }
    
    if error_descriptions:
        default_errors.update(error_descriptions)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Agregar metadata para OpenAPI
        if not hasattr(wrapper, '__api_metadata__'):
            wrapper.__api_metadata__ = {}
        
        wrapper.__api_metadata__.update({
            'success_model': success_model,
            'success_description': success_description,
            'error_codes': error_codes or list(default_errors.keys()),
            'error_descriptions': default_errors
        })
        
        return wrapper
    
    return decorator


class ResponseDocumentation:
    """Clase para gestionar documentación de respuestas"""
    
    @staticmethod
    def get_standard_responses(include_errors: bool = True) -> Dict[int, Dict]:
        """Obtiene respuestas estándar para documentación"""
        responses = {
            200: {
                "description": "Operación exitosa",
                "content": {
                    "application/json": {
                        "example": get_response_example("SuccessResponse")
                    }
                }
            },
            201: {
                "description": "Recurso creado exitosamente", 
                "content": {
                    "application/json": {
                        "example": get_response_example("SuccessResponse")
                    }
                }
            }
        }
        
        if include_errors:
            error_responses = {
                400: {
                    "description": "Solicitud incorrecta",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                },
                401: {
                    "description": "No autorizado",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                },
                403: {
                    "description": "Prohibido - Sin permisos suficientes",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                },
                404: {
                    "description": "Recurso no encontrado",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                },
                409: {
                    "description": "Conflicto - El recurso ya existe",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                },
                422: {
                    "description": "Error de validación",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                },
                429: {
                    "description": "Límite de tasa excedido",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                },
                500: {
                    "description": "Error interno del servidor",
                    "content": {
                        "application/json": {
                            "example": get_response_example("ErrorResponse")
                        }
                    }
                }
            }
            responses.update(error_responses)
        
        return responses
    
    @staticmethod
    def get_paginated_response() -> Dict[int, Dict]:
        """Obtiene respuesta paginada para documentación"""
        return {
            200: {
                "description": "Datos paginados obtenidos exitosamente",
                "content": {
                    "application/json": {
                        "example": get_response_example("PaginatedResponse")
                    }
                }
            }
        }