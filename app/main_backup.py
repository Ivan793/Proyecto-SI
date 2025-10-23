

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import firebase_admin
from firebase_admin import credentials
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
if not load_dotenv():
    logger.warning("No se encontró el archivo .env")

# Validar la variable de entorno FIREBASE_CREDENTIALS_PATH
firebase_credentials_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
if not firebase_credentials_path:
    logger.error("FIREBASE_CREDENTIALS_PATH no está configurado en el archivo .env")
    sys.exit(1)

if not os.path.exists(firebase_credentials_path):
    logger.error(f"El archivo de credenciales de Firebase no existe en: {firebase_credentials_path}")
    sys.exit(1)

# Importar routers
try:
    from app.routers.report_router import router as report_router
    # ... otros routers existentes
except ImportError as e:
    logger.error(f"Error importando routers: {str(e)}")
    sys.exit(1)

# Inicializar Firebase
try:
    cred = credentials.Certificate(firebase_credentials_path)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase inicializado correctamente")
except Exception as e:
    logger.error(f"Error inicializando Firebase: {str(e)}")
    sys.exit(1)

# Crear aplicación FastAPI
app = FastAPI(
    title="API ExpoSoftware",
    description="Sistema de gestión para la Feria Tecnológica ExpoSoftware",
    version="1.0.0"
)

# Configurar CORS
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# Registrar routers
try:
    app.include_router(report_router, prefix="/api/v1")
    # ... incluir otros routers existentes
    logger.info("Routers registrados correctamente")
except Exception as e:
    logger.error(f"Error registrando routers: {str(e)}")
    sys.exit(1)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "mensaje": "API ExpoSoftware",
        "version": "1.0.0",
        "documentacion": "/docs",
        "estado": "operativo"
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado del servidor"""
    try:
        # Aquí podrías agregar verificaciones adicionales
        # como conexión a la base de datos, etc.
        return {
            "status": "healthy",
            "service": "ExpoSoftware API",
            "firebase": "connected",
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="Servicio no disponible temporalmente"
        )

import datetime

if __name__ == "__main__":
    try:
        import uvicorn
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "8000"))
        
        logger.info(f"Iniciando servidor en http://{host}:{port}")
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Error iniciando el servidor: {str(e)}")
        sys.exit(1)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging, sys

from app.core.config import settings
from app.core.firebase import firebase_client
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.exceptions.handlers import register_exception_handlers
from slowapi.errors import RateLimitExceeded

# Importar todos los routers de forma centralizada
from app.routers import graduate_router, guest_router, router as api_router, student_router

# Configuración de logs
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y cierre del ciclo de vida de la app."""
    logger.info("Iniciando ExpoSoftware API")
    firebase_client.initialize()
    logger.info("Firebase inicializado correctamente")
    yield
    firebase_client.close()
    logger.info("Firebase desconectado")


# Crear app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API del sistema ExpoSoftware",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
register_exception_handlers(app)

# Routers
app.include_router(api_router)

# Health check
@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "ExpoSoftware API funcionando"}

@app.get("/health", tags=["Health"])
async def health_check():
    return {"firebase": "connected" if firebase_client._db else "disconnected"}
