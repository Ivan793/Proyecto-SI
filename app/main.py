from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from typing import List

# Importaciones de configuración y servicios
from app.core.config import settings
from app.core.firebase import firebase_client
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler
from app.exceptions.handlers import register_exception_handlers
from slowapi.errors import RateLimitExceeded

# Importar todos los routers de forma centralizada (asumimos que app.routers importa todo lo necesario)
from app.routers import router as api_router

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
    
    # === Lógica de Inicialización (Antes de Yield) ===
    
    # 1. Inicializar Firebase (con la lógica condicional ya aplicada)
    try:
        firebase_client.initialize()
        logger.info("Firebase inicializado correctamente")
    except Exception as e:
        logger.error(f"Error CRÍTICO al inicializar Firebase: {e}")
        # Si la inicialización falla, la aplicación no debería continuar
        raise

    # 2. Imprimir Rutas Registradas (Solución al problema de logs)
    # Ejecutamos esta lógica aquí para garantizar que se registre después de 
    # incluir todos los routers y antes de que el servidor comience a escuchar.
    try:
        if logger.level <= logging.INFO:
            # Filtra las rutas para solo mostrar las API routes (excluye Middlewares/statics)
            routes: List[str] = [r.path for r in app.routes if getattr(r, 'path', None)]
            logger.info("RUTAS REGISTRADAS (%d): %s", len(routes), routes)
    except Exception as e:
        logger.error(f"Error al listar rutas: {e}")
        
    yield
    
    # === Lógica de Cierre (Después de Yield) ===
    
    firebase_client.close()
    logger.info("Firebase desconectado")


# Crear app (Única y correcta definición)
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
    # Verifica si la aplicación de Firebase existe (asumo que se almacena en _app)
    is_connected = bool(getattr(firebase_client, '_app', None))
    return {"firebase": "connected" if is_connected else "disconnected"}
