from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
import re

from .config import settings
from app.exceptions.auth_exceptions import (
    InvalidTokenException,
    TokenExpiredException,
    InvalidCredentialsException
)


# ==================== HASHING DE CONTRASEÑAS ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hashea una contraseña usando bcrypt
    
    Args:
        password: Contraseña en texto plano
        
    Returns:
        Contraseña hasheada
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si una contraseña coincide con su hash
    
    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Contraseña hasheada
        
    Returns:
        True si coinciden, False en caso contrario
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==================== VALIDACIÓN DE CONTRASEÑAS ====================

def validate_password_strength(password: str) -> bool:

    # Validar longitud
    if len(password) < settings.PASSWORD_MIN_LENGTH:
        raise InvalidCredentialsException(
            f"La contraseña debe tener al menos {settings.PASSWORD_MIN_LENGTH} caracteres"
        )
    
    if len(password) > settings.PASSWORD_MAX_LENGTH:
        raise InvalidCredentialsException(
            f"La contraseña no puede tener más de {settings.PASSWORD_MAX_LENGTH} caracteres"
        )
    
    # Patrón regex según el diccionario:
    # - Al menos una mayúscula: (?=.*[A-Z])
    # - Al menos una minúscula: (?=.*[a-z])
    # - Al menos un dígito: (?=.*\d)
    # - Al menos un especial (no @): (?=.*[^A-Za-z0-9@])
    pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9@]).{8,12}$"
    
    if not re.match(pattern, password):
        raise InvalidCredentialsException(
            "La contraseña debe contener al menos: una mayúscula, una minúscula, "
            "un número y un carácter especial (excepto @)"
        )
    
    return True


# ==================== JWT TOKENS ====================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

#    Crea un token JWT de refresco (refresh token)
def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

# Decodifica y valida un token JWT
def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException()
        
    except JWTError as e:
        raise InvalidTokenException(f"Error al decodificar token: {str(e)}")

# Verifica que el token sea del tipo esperado
def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    token_type = payload.get("type")
    
    if token_type != expected_type:
        raise InvalidTokenException(
            f"Tipo de token inválido. Se esperaba '{expected_type}', se recibió '{token_type}'"
        )
    
    return True


# ==================== VALIDACIONES ADICIONALES ====================

#    Valida que el correo sea institucional para roles específicos
def validate_institutional_email(email: str, rol: str) -> bool:
    from app.exceptions.user_exceptions import InvalidEmailDomainException
    
    # Según el diccionario: Docente y Estudiante requieren correo institucional
    if rol in ("Docente", "Estudiante"):
        if not email.endswith(settings.INSTITUTIONAL_EMAIL_DOMAIN):
            raise InvalidEmailDomainException(rol=rol)
    
    return True


#    Sanitiza una cadena de texto removiendo caracteres potencialmente peligrosos
def sanitize_string(text: str) -> str:

    # Remover caracteres de control y espacios en blanco excesivos
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text