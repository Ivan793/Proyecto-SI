from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

from .config import settings

logger = logging.getLogger(__name__)


# ==================== CONFIGURACIÓN DE RATE LIMITER ====================

def get_rate_limit_key(request: Request) -> str:

    # Intentar obtener el ID del usuario desde el token
    if hasattr(request.state, "user_id"):
        return f"user:{request.state.user_id}"
    
    # Si no hay usuario, usar la IP
    return get_remote_address(request)


# Inicializar el limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[
        f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
        f"{settings.RATE_LIMIT_PER_HOUR}/hour"
    ],
    enabled=settings.RATE_LIMIT_ENABLED
)


# ==================== MANEJADOR DE ERRORES ====================

# Maneja el error cuando se excede el límite de peticiones
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:

    logger.warning(
        f"Rate limit exceeded: {get_rate_limit_key(request)} | Path: {request.url.path}"
    )
    
    return JSONResponse(
        status_code=429,
        content={
            "status": "error",
            "message": "Límite de peticiones excedido. Por favor, intente más tarde.",
            "code": "RATE_LIMIT_EXCEEDED",
            "retry_after": 60  # segundos
        }
    )


# ==================== DECORADORES PERSONALIZADOS ====================

#    Decorador para rate limiting estricto en endpoints sensibles
def strict_rate_limit(calls: int = 5, period: int = 60):
    return limiter.limit(f"{calls}/{period}second")


# Rate limiting específico para endpoints de autenticación
def auth_rate_limit():

    return limiter.limit("5/minute")

#    Rate limiting para endpoints de administrador
def admin_rate_limit():

    return limiter.limit("100/minute")