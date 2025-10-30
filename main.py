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
from app.routers import  router as api_router

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

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# Registrar manejadores de excepciones globales
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