from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Configuración de la aplicación desde variables de entorno"""
    
    # ==================== APLICACIÓN ====================
    APP_NAME: str = "ExpoSoftware API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development, staging, production
    
    # ==================== API ====================
    API_V1_PREFIX: str = "/api/v1"
    
    # ==================== SEGURIDAD ====================
    SECRET_KEY: str = "MuIOjdl8Dl9mqr7-9nyQXneaHhwWcKSRGikRIcBZr9c"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1
    
    # ==================== FIREBASE ====================
    FIREBASE_CREDENTIALS_PATH: str = "academic-management-syst-1e4a1-firebase-adminsdk-fbsvc-74e58d92c4.json"
    FIREBASE_DATABASE_URL: Optional[str] = None
    FIREBASE_API_KEY: str = "AIzaSyCbEN3vnK6AtsLNbaKPPMT4Iz0hrP5vSuk"
    
    # ==================== CORS ====================
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8000",
    ]
    
    # ==================== RATE LIMITING ====================
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # ==================== PAGINACIÓN ====================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # ==================== LOGGING ====================
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==================== VALIDACIONES ====================
    # Contraseña
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Email institucional
    INSTITUTIONAL_EMAIL_DOMAIN: str = "@unicesar.edu.co"
    
    # Teléfono
    PHONE_MIN_LENGTH: int = 7
    PHONE_MAX_LENGTH: int = 15
    
    # ==================== ADMINISTRADOR ====================
    ADMIN_DEFAULT_EMAIL: str = "admin@unicesar.edu.co"
    ADMIN_DEFAULT_PASSWORD: str = ENVIRONMENT # Debe ser configurado en .env
    
    # ==================== TIMEZONE ====================
    TIMEZONE: str = "America/Bogota"

# ==================== ADMINISTRADOR ====================

    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Obtiene la configuración de la aplicación (singleton)
    Usa caché para evitar recargar múltiples veces
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()